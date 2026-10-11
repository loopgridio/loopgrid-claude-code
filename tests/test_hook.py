import concurrent.futures
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import loopgrid_hook as hook


def case(tool="Bash", args=None, session="sess1", tool_id="toolu1", event="PreToolUse"):
    return {"session_id": session, "tool_use_id": tool_id, "tool_name": tool,
            "tool_input": {"command": "echo ok"} if args is None else args, "hook_event_name": event}


class FakeCore:
    def __init__(self, verdict="auto_allowed"):
        self.verdict = verdict
        self.requests = []
        self.fail = set()
        self.lock = threading.RLock()

    def handle(self, method, path, body):
        with self.lock:
            self.requests.append((method, path, body))
            if "all" in self.fail or ("events" in path and "events" in self.fail):
                raise hook.HookFailure("Core unavailable")
            if path == "/api/v1/decisions":
                return {"decision_id": "dec_001", "idempotent_replay": False}
            if path.endswith("/policies/evaluate"):
                return {"decision": self.verdict, "policy_id": "p", "policy_digest": "sha256-test"}
            if "/events" in path:
                return {"event_id": "ev_001"}
            raise hook.HookFailure("unexpected mock URL")

    @contextmanager
    def patched(self):
        def api(cfg, method, path, payload=None):
            return self.handle(method, path, payload)
        with patch.object(hook, "_api", api):
            yield


class HookTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.cfg = {
            "mode": "enforce", "base": "http://127.0.0.1:8000", "key": "secret-key",
            "workspace": "w-test", "policy": "p", "tools": hook.DEFAULT_TOOLS.split(","),
            "state": Path(self.d.name) / "hook.sqlite3",
        }
        self.core = FakeCore()

    def tearDown(self):
        self.d.cleanup()

    def test_state_db_closes_if_initialization_fails(self):
        """A failed concurrent SQLite initializer must not leak a DB handle.

        Windows refuses to delete an open SQLite file (WinError 32).
        """
        class FailedInitializer:
            def __init__(self):
                self.closed = False
                self.calls = 0

            def execute(self, _sql):
                self.calls += 1
                if self.calls == 2:
                    raise sqlite3.OperationalError("database is locked")
                return self

            def close(self):
                self.closed = True

        db = FailedInitializer()
        with patch.object(hook.sqlite3, "connect", return_value=db):
            with self.assertRaises(sqlite3.OperationalError):
                with hook.state_db(self.cfg):
                    self.fail("state_db should fail during initialization")
        self.assertTrue(db.closed)

    def test_off_no_side_effect(self):
        self.cfg["mode"] = "off"
        with self.core.patched():
            self.assertIsNone(hook.pre(case(), self.cfg))
        self.assertFalse(self.cfg["state"].exists())

    def test_unprotected_tool(self):
        with self.core.patched():
            self.assertIsNone(hook.pre(case(tool="Read"), self.cfg))
        self.assertFalse(self.cfg["state"].exists())

    def test_own_mcp_exempt(self):
        for n in ["mcp__loopgrid__record_decision", "mcp__plugin_loopgrid_loopgrid__record_decision"]:
            self.assertFalse(hook.protected(n, self.cfg))
        self.assertTrue(hook.protected("mcp__stripe__refund", self.cfg))
        self.assertTrue(hook.protected("mcp__plugin_loopgrid_stripe__refund", self.cfg))

    def test_core_auto_allow_no_override(self):
        with self.core.patched():
            self.assertIsNone(hook.pre(case(args={"command":"echo ok", "amount":25}), self.cfg))
        self.assertEqual([x[2]["event_type"] for x in self.core.requests if "/events" in x[1]], ["policy_evaluated", "tool_requested"])

    def test_deny_blocked(self):
        self.core.verdict = "blocked"
        with self.core.patched():
            r = hook.pre(case(), self.cfg)
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("prohibited by the active policy", r["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertNotIn("review and retry", r["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertFalse(any(x[2].get("event_type") == "tool_requested" for x in self.core.requests if "/events" in x[1]))

    def test_deny_human_required(self):
        self.core.verdict = "human_approval_required"
        with self.core.patched():
            r = hook.pre(case(), self.cfg)
        self.assertIn("human_approval_required", r["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIn("will not automatically resume", r["hookSpecificOutput"]["permissionDecisionReason"])

    def test_deny_unsupported_rule(self):
        self.core.verdict = "manual_review_required"
        with self.core.patched():
            output = hook.pre(case(), self.cfg)["hookSpecificOutput"]
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("human review is required", output["permissionDecisionReason"])
            self.assertIn("will not automatically resume", output["permissionDecisionReason"])

    def test_deny_missing_policy(self):
        self.cfg["policy"] = ""
        with self.core.patched():
            self.assertEqual(hook.pre(case(), self.cfg)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_deny_when_core_down(self):
        self.core.fail.add("all")
        with self.core.patched():
            self.assertEqual(hook.pre(case(), self.cfg)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_observe_core_down_does_not_deny(self):
        self.cfg["mode"] = "observe"
        self.core.fail.add("all")
        with self.core.patched():
            self.assertIsNone(hook.pre(case(), self.cfg))
        with hook.state_db(self.cfg) as db:
            self.assertEqual(db.execute("select status from calls").fetchone()[0], "capture_failed")

    def test_deny_incomplete_hook_payload(self):
        for change in ({"tool_use_id": ""}, {"tool_input": None}, {"session_id": None}):
            p = case(tool_id="different"+str(change))
            p.update(change)
            with self.core.patched():
                self.assertEqual(hook.pre(p, self.cfg)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_duplicate_tool_use_pre_deny(self):
        with self.core.patched():
            self.assertIsNone(hook.pre(case(), self.cfg))
            self.assertEqual(hook.pre(case(), self.cfg)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(sum(1 for x in self.core.requests if x[1] == "/api/v1/decisions"), 1)

    def test_same_tool_id_different_args_deny(self):
        with self.core.patched():
            self.assertIsNone(hook.pre(case(), self.cfg))
            self.assertEqual(hook.pre(case(args={"command":"dangerous"}), self.cfg)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_session_bound_id(self):
        with self.core.patched():
            self.assertIsNone(hook.pre(case(session="1"), self.cfg))
            self.assertIsNone(hook.pre(case(session="2"), self.cfg))
        with hook.state_db(self.cfg) as db:
            self.assertEqual(db.execute("select count(*) from calls").fetchone()[0], 2)

    def test_post_records_tool_receipt_not_outcome(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            post = case(event="PostToolUse")
            post["tool_response"] = {"stdout": "ok", "stderr": ""}
            self.assertIsNone(hook.post(post, self.cfg))
        event = self.core.requests[-1][2]
        self.assertEqual(event["event_type"], "tool_result")
        self.assertFalse(event["payload"]["outcome_verified"])
        self.assertNotIn("stdout", json.dumps(event))

    def test_failure_records_failed_tool_result(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            p = case(event="PostToolUseFailure")
            p["error"] = "private error details"
            hook.post(p, self.cfg, failure=True)
        self.assertEqual(self.core.requests[-1][2]["payload"]["execution_status"], "failed")
        self.assertNotIn("private error details", json.dumps(self.core.requests[-1]))

    def test_no_forged_post_without_pre(self):
        with self.core.patched():
            p = case(event="PostToolUse")
            p["tool_response"] = {"ok":True}
            hook.post(p, self.cfg)
        self.assertEqual(len(self.core.requests), 0)

    def test_no_forged_post_with_wrong_args(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            p = case(args={"command":"other"})
            p["tool_response"] = "ok"
            hook.post(p, self.cfg)
        self.assertNotEqual(self.core.requests[-1][2]["event_type"], "tool_result")

    def test_denied_decision_does_not_record_execution(self):
        self.core.verdict = "blocked"
        with self.core.patched():
            hook.pre(case(), self.cfg)
            p = case()
            p["tool_response"] = "ok"
            hook.post(p, self.cfg)
        self.assertFalse(any(x[2].get("event_type") == "tool_result" for x in self.core.requests if "/events" in x[1]))

    def test_duplicate_post_no_duplicate_event(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            p = case()
            p["tool_response"] = "ok"
            hook.post(p, self.cfg)
            hook.post(p, self.cfg)
        self.assertEqual(sum(1 for x in self.core.requests if "/events" in x[1] and x[2]["event_type"] == "tool_result"), 1)

    def test_post_failure_requires_reconciliation(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            self.core.fail.add("events")
            p = case()
            p["tool_response"] = "payment complete"
            response = hook.post(p, self.cfg)
        self.assertIn("reconciliation", response["hookSpecificOutput"]["additionalContext"])
        with hook.state_db(self.cfg) as db:
            self.assertEqual(db.execute("select status from calls").fetchone()[0], "needs_reconciliation")

    def test_restart_persistent_data(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
        # New connection emulates restarted process.
        with hook.state_db(self.cfg) as db:
            self.assertEqual(db.execute("select decision_id from calls").fetchone()[0], "dec_001")
        with self.core.patched():
            p = case()
            p["tool_response"] = "ok"
            hook.post(p, self.cfg)
        self.assertEqual(self.core.requests[-1][2]["event_type"], "tool_result")

    def test_concurrent_duplicate_authorization_once(self):
        with self.core.patched():
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
                responses = list(ex.map(lambda i: hook.pre(case(), self.cfg), range(5)))
        self.assertEqual(sum(x is None for x in responses), 1)
        self.assertEqual(sum(x is not None for x in responses), 4)
        self.assertEqual(sum(1 for x in self.core.requests if x[1] == "/api/v1/decisions"), 1)

    def test_no_raw_sensitive_input_in_remote_payloads(self):
        with self.core.patched():
            hook.pre(case(args={"command": "echo my-super-secret-token", "amount": 5}), self.cfg)
            p = case(args={"command":"echo my-super-secret-token", "amount":5})
            p["tool_response"] = {"stdout":"private response"}
            hook.post(p, self.cfg)
        encoded = json.dumps(self.core.requests)
        self.assertNotIn("my-super-secret-token", encoded)
        self.assertNotIn("private response", encoded)
        self.assertNotIn("secret-key", encoded)

    def test_config_https_remote(self):
        with self.assertRaises(hook.HookFailure):
            hook.config({"LOOPGRID_BASE_URL": "http://example.invalid", "LOOPGRID_CLAUDE_MODE": "enforce"})
        self.assertEqual(hook.config({"LOOPGRID_BASE_URL": "https://example.invalid"})["base"], "https://example.invalid")

    def test_config_reject_embedded_credentials(self):
        with self.assertRaises(hook.HookFailure):
            hook.config({"LOOPGRID_BASE_URL":"https://someone:pwd@127.0.0.1:8000"})

    def test_config_reject_bad_mode(self):
        with self.assertRaises(hook.HookFailure):
            hook.config({"LOOPGRID_CLAUDE_MODE":"sometimes"})

    def test_canonical_hash(self):
        self.assertEqual(hook.digest({"b": 2, "a": 1}), hook.digest({"a": 1, "b": 2}))
        self.assertNotEqual(hook.digest({"a": 1}), hook.digest({"a": 2}))

    def test_enforce_missing_input_denies_in_cli(self):
        (Path(self.d.name) / ".loopgrid").mkdir()
        (Path(self.d.name) / hook.PROJECT_OPT_IN).touch()
        env = {"LOOPGRID_CLAUDE_MODE":"enforce", "LOOPGRID_BASE_URL":"http://127.0.0.1:8000", "CLAUDE_PROJECT_DIR":self.d.name}
        out = io.StringIO()
        self.assertEqual(hook.run(["pre"], stdin=io.StringIO("not json"), stdout=out, env=env), 0)
        self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_misspelled_enforce_mode_does_not_fail_open(self):
        (Path(self.d.name) / ".loopgrid").mkdir()
        (Path(self.d.name) / hook.PROJECT_OPT_IN).touch()
        env = {"LOOPGRID_CLAUDE_MODE":"enfroce", "LOOPGRID_BASE_URL":"http://127.0.0.1:8000", "CLAUDE_PROJECT_DIR":self.d.name}
        out = io.StringIO()
        self.assertEqual(hook.run(["pre"], stdin=io.StringIO(json.dumps(case())), stdout=out, env=env), 0)
        self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_project_requires_explicit_activation(self):
        self.assertFalse(hook.project_opted_in({}))
        self.assertFalse(hook.project_opted_in({"CLAUDE_PROJECT_DIR":self.d.name}))
        self.assertFalse(hook.project_opted_in({"CLAUDE_PROJECT_DIR":"relative"}))
        (Path(self.d.name) / ".loopgrid").mkdir()
        (Path(self.d.name) / hook.PROJECT_OPT_IN).touch()
        self.assertTrue(hook.project_opted_in({"CLAUDE_PROJECT_DIR":self.d.name}))

    def test_unrelated_project_never_reads_hook_payload(self):
        class NoRead:
            def read(self, *args):
                raise AssertionError("Unrelated project hook read tool data")
        for mode in ("observe", "enforce"):
            env = {"LOOPGRID_CLAUDE_MODE":mode, "CLAUDE_PROJECT_DIR":self.d.name}
            out=io.StringIO()
            with patch.object(hook, "_api", side_effect=AssertionError("Unexpected network access")):
                self.assertEqual(hook.run(["pre"], stdin=NoRead(), stdout=out, env=env), 0)
            self.assertEqual(out.getvalue(), "")
        self.assertFalse(self.cfg["state"].exists())

    def test_enabled_project_dispatches_native_pre_hook(self):
        (Path(self.d.name) / ".loopgrid").mkdir()
        (Path(self.d.name) / hook.PROJECT_OPT_IN).touch()
        env = {"LOOPGRID_CLAUDE_MODE":"observe", "CLAUDE_PROJECT_DIR":self.d.name}
        with patch.object(hook, "pre", return_value=None) as actual:
            self.assertEqual(hook.run(["pre"], stdin=io.StringIO(json.dumps(case())), stdout=io.StringIO(), env=env),0)
            actual.assert_called_once()

    def test_marker_in_another_project_cannot_activate_this_project(self):
        (Path(self.d.name) / ".loopgrid").mkdir()
        (Path(self.d.name) / hook.PROJECT_OPT_IN).touch()
        with tempfile.TemporaryDirectory() as other:
            self.assertFalse(hook.project_opted_in({"CLAUDE_PROJECT_DIR":other}))

    def test_missing_tool_result_does_not_forge_execution(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            hook.post(case(event="PostToolUse"), self.cfg)
        self.assertFalse(any(x[2].get("event_type") == "tool_result" for x in self.core.requests if "/events" in x[1]))

    def test_post_reconciliation_never_replays_action(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            self.core.fail.add("events")
            p = case(event="PostToolUse")
            p["tool_response"] = {"transaction_id":"fake-receipt"}
            hook.post(p, self.cfg)
            initial = len(self.core.requests)
            self.core.fail.clear()
            self.assertIsNone(hook.post(p, self.cfg))
        self.assertEqual(len(self.core.requests), initial)

    def test_off_cli_does_not_read_input(self):
        env = {"LOOPGRID_CLAUDE_MODE":"off", "LOOPGRID_BASE_URL":"http://127.0.0.1:8000"}
        self.assertEqual(hook.run(["pre"], stdin=io.StringIO("invalid"), stdout=io.StringIO(), env=env), 0)

    def test_result_hash_not_status_duplicated(self):
        with self.core.patched():
            hook.pre(case(), self.cfg)
            p = case()
            p["tool_response"] = {"a": 1}
            hook.post(p, self.cfg)
        self.assertEqual(self.core.requests[-1][2]["payload"]["result_sha256"], hook.digest({"a":1}))


class TransportTests(unittest.TestCase):
    def test_redirect_to_different_host_not_followed(self):
        count = []
        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                count.append(self.path)
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:1/steal")
                self.end_headers()
            def log_message(self, fmt, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            cfg = {"base": f"http://127.0.0.1:{server.server_port}", "key":"private-test-key"}
            with self.assertRaises(hook.HookFailure):
                hook._api(cfg, "POST", "/api/v1/decisions", {"a": 1})
            self.assertEqual(count, ["/api/v1/decisions"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_real_http_json_request(self):
        seen = []
        class Core(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length))
                seen.append((self.path, payload, self.headers.get("X-LoopGrid-Key")))
                body = json.dumps({"decision_id":"dec_live_stub"}).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, fmt, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Core)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            cfg={"base":f"http://127.0.0.1:{server.server_port}","key":"private-key"}
            val=hook._api(cfg, "POST", "/api/v1/decisions", {"proposed_action":{"tool":"Bash"}})
            self.assertEqual(val["decision_id"], "dec_live_stub")
            self.assertEqual(seen[0], ("/api/v1/decisions", {"proposed_action":{"tool":"Bash"}}, "private-key"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class FormatTests(unittest.TestCase):
    def test_plugin_files(self):
        root = Path(__file__).resolve().parents[1]
        plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "loopgrid")
        self.assertEqual(plugin["version"], "0.1.0")
        for file in [".mcp.json", "hooks/hooks.json"]:
            self.assertIsInstance(json.loads((root / file).read_text(encoding="utf-8")), dict)
        for name in ("decision", "review", "guard", "verify"):
            self.assertTrue((root / "skills" / name / "SKILL.md").read_text(encoding="utf-8").startswith("---\n"))

    def test_mcp_server_pinned_version(self):
        root = Path(__file__).resolve().parents[1]
        server = json.loads((root / ".mcp.json").read_text())["mcpServers"]["loopgrid"]
        self.assertEqual(server["command"], "uvx")
        self.assertEqual(server["args"], ["loopgrid-claude-launcher==0.1.0"])
        self.assertEqual(server["env"]["LOOPGRID_CLAUDE_PLUGIN"], "1")
        project = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"loopgrid-claude-launcher==0.1.0"', project)

    def test_plugin_user_config_sensitive(self):
        root = Path(__file__).resolve().parents[1]
        plugin = json.loads((root / ".claude-plugin/plugin.json").read_text())
        self.assertTrue(plugin["userConfig"]["service_key"]["sensitive"])
        self.assertFalse(plugin["userConfig"]["service_key"]["required"])
        self.assertEqual(plugin["userConfig"]["core_url"]["type"], "string")

    def test_process_environment_reads_only_declared_hook_settings(self):
        with patch.dict(os.environ, {
            "LOOPGRID_CLAUDE_MODE": "observe",
            "CLAUDE_PLUGIN_OPTION_WORKSPACE_ID": "test-workspace",
            "UNRELATED_SETTING_FOR_TEST": "not-a-hook-setting",
        }):
            selected = hook.process_hook_settings()
        self.assertEqual(selected["LOOPGRID_CLAUDE_MODE"], "observe")
        self.assertEqual(selected["CLAUDE_PLUGIN_OPTION_WORKSPACE_ID"], "test-workspace")
        self.assertNotIn("UNRELATED_SETTING_FOR_TEST", selected)
        self.assertEqual(set(selected).difference(hook.HOOK_SETTING_NAMES), set())

    def test_hook_credential_only_from_plugin_option(self):
        cfg = hook.config({"LOOPGRID_SERVICE_KEY": "machine-wide-secret"})
        self.assertEqual(cfg["key"], "")
        cfg2 = hook.config({"LOOPGRID_SERVICE_KEY": "bad", "CLAUDE_PLUGIN_OPTION_SERVICE_KEY":"claude-secure-key"})
        self.assertEqual(cfg2["key"], "claude-secure-key")

    def test_offline_origin_check_for_doctor(self):
        from core_origin import validate_core_origin
        self.assertEqual(validate_core_origin("https://example.invalid/"), "https://example.invalid")
        with self.assertRaises(ValueError):
            validate_core_origin("http://example.invalid")

    def test_offline_doctor_has_no_network_access(self):
        from importlib.util import module_from_spec, spec_from_file_location
        root = Path(__file__).resolve().parents[1]
        spec = spec_from_file_location("lg_doctor", root / "scripts/doctor.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        # The diagnostic should succeed when its prerequisites are present.
        # CI runners do not necessarily have uv installed, so mock the
        # prerequisite explicitly rather than depending on the host PATH.
        with patch.dict(os.environ, {"LOOPGRID_BASE_URL": "http://127.0.0.1:8000",
                                      "LOOPGRID_CLAUDE_MODE": "off"}), \
             patch.object(module.shutil, "which", return_value="uv-present-for-test"), \
             patch("socket.socket", side_effect=AssertionError("no sockets in doctor")):
            self.assertEqual(module.main(), 0)

    def test_offline_doctor_reports_missing_uv_without_network(self):
        from importlib.util import module_from_spec, spec_from_file_location
        root = Path(__file__).resolve().parents[1]
        spec = spec_from_file_location("lg_doctor_no_uv", root / "scripts/doctor.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        # Missing uv is a genuine installation error, not a network request.
        with patch.dict(os.environ, {"LOOPGRID_BASE_URL": "http://127.0.0.1:8000",
                                      "LOOPGRID_CLAUDE_MODE": "off"}), \
             patch.object(module.shutil, "which", return_value=None), \
             patch("socket.socket", side_effect=AssertionError("no sockets in doctor")):
            self.assertEqual(module.main(), 1)

    def test_hooks_do_not_auto_allow(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts" / "loopgrid_hook.py").read_text()
        self.assertNotIn('"permissionDecision": "allow"', source)
        data = json.loads((root / "hooks" / "hooks.json").read_text())
        self.assertEqual(set(data["hooks"]), {"PreToolUse", "PostToolUse", "PostToolUseFailure"})


if __name__ == '__main__':
    unittest.main()
