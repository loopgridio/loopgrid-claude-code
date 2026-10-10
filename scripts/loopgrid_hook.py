#!/usr/bin/env python3
"""Claude Code hook bridge to LoopGrid Core. Requires only Python 3.10+.

Modes: off (default); observe (best effort); enforce (Core auto_allowed or deny).
Do not mistake PostToolUse receipts for independently observed business outcomes.
"""
from __future__ import annotations

from contextlib import contextmanager

import fnmatch
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

MAX_HOOK_BYTES = 2 * 1024 * 1024
DEFAULT_TOOLS = "Bash,Write,Edit,MultiEdit,NotebookEdit,mcp__*"
PROJECT_OPT_IN = Path(".loopgrid") / "claude-code.enabled"


class HookFailure(RuntimeError):
    pass


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def config(env=None):
    env = os.environ if env is None else env
    mode = env.get("LOOPGRID_CLAUDE_MODE", "off").lower().strip()
    if mode not in {"off", "observe", "enforce"}:
        raise HookFailure("Invalid LOOPGRID_CLAUDE_MODE; use off, observe, or enforce")
    base = (env.get("CLAUDE_PLUGIN_OPTION_CORE_URL") or env.get("LOOPGRID_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise HookFailure("LOOPGRID_BASE_URL must be an http(s) origin without credentials or path")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"} :
        raise HookFailure("Remote LoopGrid endpoints require HTTPS")
    patterns = tuple(x.strip() for x in env.get("LOOPGRID_CLAUDE_TOOLS", DEFAULT_TOOLS).split(",") if x.strip())
    root = Path(env.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".loopgrid" / "claude-code")
    return {
        "mode": mode, "base": base, "key": env.get("CLAUDE_PLUGIN_OPTION_SERVICE_KEY", ""),
        "workspace": (env.get("CLAUDE_PLUGIN_OPTION_WORKSPACE_ID") or env.get("LOOPGRID_WORKSPACE", "default")).strip() or "default",
        "policy": env.get("LOOPGRID_CLAUDE_POLICY_ID", "").strip(),
        "tools": patterns, "state": root / "hook_state.sqlite3",
    }


def project_opted_in(env=None):
    """Only capture tool activity in a project that explicitly enabled LoopGrid.

    CLAUDE_PROJECT_DIR is supplied by Claude Code to command hooks. The
    project marker is checked BEFORE reading any hook event JSON, touching
    SQLite, or making network requests. No directory traversal or global
    project scanning is performed. Do not fall back to the plugin install
    directory, which would enable unrelated sessions.
    """
    env = os.environ if env is None else env
    raw_root = env.get("CLAUDE_PROJECT_DIR", "")
    if not raw_root:
        return False
    root = Path(raw_root)
    if not root.is_absolute():
        return False
    return (root / PROJECT_OPT_IN).is_file()


def protected(name, cfg):
    # Our own MCP tools manage their evidence separately and must not recurse.
    if name.startswith("mcp__loopgrid__") or name.startswith("mcp__plugin_loopgrid_loopgrid__"):
        return False
    return any(fnmatch.fnmatchcase(name, p) for p in cfg["tools"])


def deny(reason):
    # Never return allow; leave all normal Claude Code permission checks in place.
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "LoopGrid: " + reason[:300]}}


def _api(cfg, method, path, payload=None):
    url = cfg["base"] + path
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "loopgrid-claude-code/0.1.0"}
    if cfg["key"]:
        headers["X-LoopGrid-Key"] = cfg["key"]
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    req = Request(url, headers=headers, method=method, data=body)
    # No HTTP redirects: do not leak the service key to a different host.
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise HookFailure("LoopGrid redirected API request")
    try:
        with build_opener(NoRedirect()).open(req, timeout=12) as res:
            value = json.loads(res.read(1024 * 1024))
            if not isinstance(value, dict):
                raise HookFailure("LoopGrid returned a non-object response")
            return value
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        raise HookFailure("LoopGrid API request failed") from exc


@contextmanager
def state_db(cfg):
    path = cfg["state"]
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    # Close the connection even if PRAGMA/schema initialization raises. On
    # Windows, leaving a failed concurrent initializer open can lock the DB
    # file and prevent TemporaryDirectory cleanup (WinError 32).
    try:
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS calls (
            k TEXT PRIMARY KEY, tool TEXT NOT NULL, input_sha TEXT NOT NULL,
            decision_id TEXT, status TEXT NOT NULL, result_sha TEXT
        )""")
        yield db
    finally:
        db.close()


def call_identity(payload):
    session = payload.get("session_id")
    tool_id = payload.get("tool_use_id")
    tool = payload.get("tool_name")
    args = payload.get("tool_input")
    if not all(isinstance(x, str) and x for x in (session, tool_id, tool)) or not isinstance(args, dict):
        raise HookFailure("Claude Code hook must include session_id, tool_use_id, tool_name and object tool_input")
    return digest([session, tool_id]), tool, digest(args), args


def _reserve(db, k, tool, input_sha):
    with db:
        inserted = db.execute("INSERT OR IGNORE INTO calls (k, tool, input_sha, status) VALUES (?, ?, ?, 'pending')", (k, tool, input_sha)).rowcount
    return inserted == 1


def _set(db, k, status, decision_id=None, result_sha=None):
    with db:
        if decision_id is None:
            db.execute("UPDATE calls SET status=?, result_sha=COALESCE(?,result_sha) WHERE k=?", (status, result_sha, k))
        else:
            db.execute("UPDATE calls SET status=?, decision_id=?, result_sha=COALESCE(?,result_sha) WHERE k=?", (status, decision_id, result_sha, k))


def _event(cfg, decision_id, event_type, payload, suffix, actor_type="integration", actor_id="claude-code"):
    return _api(cfg, "POST", f"/api/v1/decisions/{quote(decision_id, safe='')}/events", {
        "event_type": event_type, "actor_type": actor_type, "actor_id": actor_id,
        "idempotency_key": suffix, "payload": payload,
    })


def pre(payload, cfg):
    """Return None to permit normal Claude Code checks; only return JSON to deny."""
    tool = payload.get("tool_name", "")
    if cfg["mode"] == "off" or not isinstance(tool, str) or not protected(tool, cfg):
        return None
    strict = cfg["mode"] == "enforce"
    try:
        k, tool, input_sha, args = call_identity(payload)
        with state_db(cfg) as db:
            if not _reserve(db, k, tool, input_sha):
                # Deny repeated pre callbacks in enforce mode: no duplicate authorization.
                return deny("Duplicate tool-use ID; retry requires a new authorization") if strict else None
            decision_id = None
            try:
                proposed = {"tool": tool, "arguments_sha256": input_sha}
                # Existing Core amount-threshold policies can only evaluate an amount
                # supplied in tool input. This is NOT independently proven amount data.
                if type(args.get("amount")) in (int, float):
                    proposed["amount"] = args["amount"]
                created = _api(cfg, "POST", "/api/v1/decisions", {
                    "decision_type": "claude_code_tool_call", "service_name": "claude-code",
                    "workspace_id": cfg["workspace"], "agent": {"id": "claude-code"},
                    "proposed_action": proposed, "input": {}, "context": {}, "authority": {},
                    "privacy_mode": "proof_only", "idempotency_key": "claude-code:" + k,
                    "metadata": {"source": "loopgrid-claude-code", "session_sha256": digest(payload["session_id"]), "tool_use_sha256": digest(payload["tool_use_id"])},
                })
                decision_id = created.get("decision_id")
                if not isinstance(decision_id, str) or not decision_id:
                    raise HookFailure("LoopGrid did not return a decision ID")
                _set(db, k, "created", decision_id)
                if strict and not cfg["policy"]:
                    raise HookFailure("Enforcement mode requires LOOPGRID_CLAUDE_POLICY_ID")
                if cfg["policy"]:
                    evaluation = _api(cfg, "POST", f"/api/v1/workspaces/{quote(cfg['workspace'], safe='')}/policies/evaluate", {
                        "policy_id": cfg["policy"], "proposed_action": proposed, "authority": {}, "context": {},
                    })
                    verdict = evaluation.get("decision")
                    if not isinstance(verdict, str):
                        raise HookFailure("Policy returned no decision")
                    _event(cfg, decision_id, "policy_evaluated", evaluation, "claude-code:" + k + ":policy", "policy", cfg["policy"])
                    if strict and verdict != "auto_allowed":
                        _set(db, k, "denied")
                        if verdict == "blocked":
                            reason = "Policy decision is blocked; this action is prohibited by the active policy"
                        elif verdict in {"manual_review_required", "human_approval_required"}:
                            reason = ("Policy decision is " + verdict +
                                      "; human review is required; this call will not automatically resume")
                        else:
                            reason = "Policy decision is " + verdict + "; tool execution not authorized"
                        return deny(reason)
                _event(cfg, decision_id, "tool_requested", {"tool": tool, "arguments_sha256": input_sha}, "claude-code:" + k + ":request")
                _set(db, k, "authorized" if strict else "observed")
                return None
            except Exception as exc:
                _set(db, k, "denied" if strict else "capture_failed", decision_id)
                if strict:
                    return deny(str(exc) if isinstance(exc, HookFailure) else "Evidence/policy gate unavailable")
                return None
    except Exception as exc:
        return deny(str(exc) if isinstance(exc, HookFailure) else "Hook preparation failed") if strict else None


def post(payload, cfg, failure=False):
    tool = payload.get("tool_name", "")
    if cfg["mode"] == "off" or not isinstance(tool, str) or not protected(tool, cfg):
        return None
    try:
        k, tool, input_sha, _args = call_identity(payload)
        with state_db(cfg) as db:
            rec = db.execute("SELECT tool,input_sha,decision_id,status FROM calls WHERE k=?", (k,)).fetchone()
            if not rec or rec[0] != tool or rec[1] != input_sha or rec[3] not in {"authorized", "observed", "needs_reconciliation"}:
                return None  # no trusted pre receipt; never invent executed evidence
            if not failure and "tool_response" not in payload:
                _set(db, k, "needs_reconciliation")
                return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "LoopGrid post-tool callback lacked tool_response. Action status needs manual reconciliation; do not automatically retry."}}
            result_sha = digest(payload.get("error", "") if failure else payload["tool_response"])
            if rec[3] == "needs_reconciliation":
                return None  # Reconcile offline; never assume a retry is harmless.
            try:
                _event(cfg, rec[2], "tool_result", {
                    "tool": tool, "arguments_sha256": input_sha, "result_sha256": result_sha,
                    "execution_status": "failed" if failure else "returned", "outcome_verified": False,
                }, "claude-code:" + k + ":result", "tool", "claude-code")
                _set(db, k, "result_recorded", result_sha=result_sha)
            except Exception:
                _set(db, k, "needs_reconciliation", result_sha=result_sha)
                return {"hookSpecificOutput": {"hookEventName": "PostToolUseFailure" if failure else "PostToolUse", "additionalContext": "LoopGrid evidence persistence failed after execution. Do not retry the external action; reconciliation is required."}}
    except Exception:
        # A post-event error cannot undo a tool already executed.
        return None
    return None


def run(argv=None, stdin=None, stdout=None):
    argv = sys.argv[1:] if argv is None else argv
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    if len(argv) != 1 or argv[0] not in {"pre", "post", "failure"}:
        return 2
    try:
        # Unenabled projects must not have their tool input read by this
        # broadly matched hook. The global mode is a separate opt-in.
        if os.environ.get("LOOPGRID_CLAUDE_MODE", "off").strip().lower() == "off":
            return 0
        if not project_opted_in():
            return 0
        cfg = config()
        raw = stdin.read(MAX_HOOK_BYTES + 1)
        if len(raw.encode("utf-8")) > MAX_HOOK_BYTES:
            raise HookFailure("Hook input exceeds 2 MB")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise HookFailure("Hook input must be a JSON object")
        result = pre(payload, cfg) if argv[0] == "pre" else post(payload, cfg, failure=argv[0] == "failure")
        if result is not None:
            stdout.write(json.dumps(result) + "\n")
        return 0
    except Exception:
        if argv[0] == "pre" and os.environ.get("LOOPGRID_CLAUDE_MODE", "off").strip().lower() not in {"off", "observe"}:
            stdout.write(json.dumps(deny("Hook error; fail-closed")) + "\n")
        elif argv[0] in {"post", "failure"} and os.environ.get("LOOPGRID_CLAUDE_MODE", "off").strip().lower() != "off":
            event = "PostToolUse" if argv[0] == "post" else "PostToolUseFailure"
            stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": "LoopGrid evidence callback failed; inspect the external action and reconcile manually. Do not retry solely to fill evidence."}}) + "\n")
        return 0  # Avoid leaking credentials and stack traces to the model.


if __name__ == "__main__":
    sys.exit(run())
