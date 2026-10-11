# LoopGrid for Claude Code

**Signed decision evidence, policy-aware tool gating, human review provenance, and independent verification for consequential AI actions.**

LoopGrid adds an evidence and governance layer to Claude Code. It connects Claude to the existing `loopgrid-mcp` server and supplies native Claude Code hooks for recording tool decisions and execution receipts. The LoopGrid Core signs and hash-chains evidence, which can be exported and verified independently.

The plugin is separate from the [LoopGrid Claude Agent SDK Python adapter](https://github.com/loopgridio/loopgrid-claude-agent). It does not replace that SDK, alter the LoopGrid Core, or execute payment/CRM/business actions on its own.

## What you get

| Capability | Claude Code integration |
|---|---|
| Record a proposed AI/agent decision | LoopGrid MCP `record_decision` + `/loopgrid:decision` skill |
| Record policy evaluation | Native Core policy evaluation when configured |
| Human approval or rejection evidence | MCP review tool, disabled unless an authenticated operator enables it |
| Record actual tool execution receipts | MCP `record_action` or opt-in `PostToolUse`/`PostToolUseFailure` hooks |
| Record independently observed downstream outcome | MCP `record_outcome` only after checking the external system |
| Verify signed evidence | MCP `verify_evidence` (connected Core); export for independent `loopgrid-verify` |
| Govern selected Claude Code actions | Opt-in `PreToolUse` auto-policy gate, fail-closed in `enforce` mode |
| Durable local hook correlation | SQLite evidence-state ledger; no raw arguments/results stored |

## Privacy, data handling and support

**[Privacy Policy — LoopGrid](https://loopgrid.io/privacy/)** · [Security disclosure](SECURITY.md) · [Directory reviewer notes](DIRECTORY-REVIEW-NOTES.md) · [Support and privacy questions](mailto:hello@loopgrid.io)

LoopGrid is intended for professional developers and teams, not users under 18. The plugin may **read and store personal data** when a user deliberately records evidence containing identifiers or personal information through the six MCP tools. The operator-selected LoopGrid Core receives these authorized evidence submissions, applies the chosen privacy mode, and may retain decision records and evidence commitments beyond 30 days according to workspace settings and applicable agreements. LoopGrid does not promise a uniform under-30-day retention period. Deleting an optional raw disclosure does not necessarily delete cryptographic evidence commitments or audit metadata.

Automatic tool lifecycle hooks are **off by default** and only read hooked event data when an operator enables observe/enforce mode and opts a project in. Opted-in hooks send the configured Core tool names, SHA-256 commitments of tool inputs/results, hashed session/tool-use IDs, and a numeric amount when present; they do not send raw hook arguments/results. SHA-256 commitments of low-entropy content can reveal information through guessing. Hook state is written locally in SQLite and may persist until the user removes it. In contrast, deliberately invoked MCP tools may send additional user-approved decision/evidence content to Core, including personal data. Neither hooks nor the plugin's MCP tools have an independent analytics or advertising destination. The launcher installs published `loopgrid-claude-launcher==0.1.0` and its dependency `loopgrid-mcp==0.1.0` from the Python package registry when not cached. The checked-in `uv.lock` is an auditable dependency snapshot for Directory review; direct `uvx` execution does not necessarily enforce that project lockfile.

The configured LoopGrid Core may be local/self-hosted or remotely operated by the customer; the data retention and privacy configuration of that Core governs uploaded evidence. See the [Privacy Policy](https://loopgrid.io/privacy/) for details of collected information, processing, sharing, retention and deletion requests.

## Support

For plugin installation problems, configuration questions, vulnerability reports, or data-handling inquiries, contact **hello@loopgrid.io**. Do not include API keys, service credentials, production customer records, or other secrets in messages or public bug reports. Refer to [SECURITY.md](SECURITY.md) when reporting a security issue.

- [Installation and documentation](https://github.com/loopgridio/loopgrid-claude-code#readme)
- [Privacy policy](https://loopgrid.io/privacy/)
- [Terms for website/evaluation materials](https://loopgrid.io/terms/)

## Architecture

```text
Claude Code
  |-- /loopgrid:decision /loopgrid:review /loopgrid:verify /loopgrid:guard
  |-- MCP tools  --------------------> loopgrid-mcp 0.1.0
  |-- optional PreToolUse/PostToolUse hooks -> Python evidence bridge
                                             |
                                             v
                                  LoopGrid Core REST API
                                   | policy evaluation
                                   | human-review evidence
                                   | signed SHA-256 event chain
                                   v
                                evidence ZIP
                                   |
                              loopgrid-verify
```

### Privacy and installation behavior

The plugin includes three registered tool lifecycle hooks (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`) for matching Bash, file-edit and MCP tools. **Automatic hook capture is off by default and requires a project activation file.** An operator explicitly enables `observe` or `enforce` in the environment **before launching Claude Code**, and opts in each project by placing `.loopgrid/claude-code.enabled` in its root. When enabled, the bridge can contact the operator-configured LoopGrid Core over HTTPS (or local loopback HTTP) and send the tool name, canonical input/result SHA-256 commitments, hashed session/tool-use IDs, and a numeric `amount` field if the tool arguments provide one. Raw hook arguments and results are not sent by this bridge. Tool content may include low-entropy values whose hashes are guessable. See [SECURITY.md](SECURITY.md).

The MCP configuration uses the **published and Windows-tested** pinned `uvx loopgrid-claude-launcher==0.1.0`, which depends on the unchanged published `loopgrid-mcp==0.1.0`. The repository includes a genuine registry-resolved `uv.lock` generated from the published packages (38 resolved packages on Windows, October 11, 2026). `uvx` resolves its own environment at runtime; the adjacent lockfile is an auditable snapshot rather than an enforced runtime lock for the `uvx` invocation. Registry packages and dependencies may download on first use. MCP tools record data only when invoked and may send additional operator-approved decision content to the connected Core; the default evidence export excludes payloads. The plugin has **no analytics endpoint or separate usage telemetry**. Review the declared LoopGrid endpoint and credentials before enabling capture. Enabling this plugin is not an authorization to send unrelated sensitive tool data.

### Installation

Prerequisites: Claude Code installed, Python 3.10+ available as `python`, `uv` (from the [uv](https://docs.astral.sh/uv/) toolchain) available on PATH, and a reachable LoopGrid v0.8.x Core for evidence operations. The published Claude-only launcher reuses [loopgrid-mcp==0.1.0](https://pypi.org/project/loopgrid-mcp/) unchanged. The included `uv.lock` has been generated against the published package; confirm it remains current with `uv lock --check` before pushing.

1. Download or clone the repository into a directory such as `loopgrid-claude-code`. Run the tests and offline `doctor.py` inside that folder. When launching Claude Code for a **plugin smoke test**, start it from a separate disposable project; otherwise Claude Code may also interpret `.mcp.json` as a second, project-level MCP server and report a spurious `CLAUDE_PLUGIN_ROOT` warning.
2. Set the LoopGrid configuration in the **terminal that starts Claude Code**. For local evaluation on Windows PowerShell:

   ```powershell
   $env:LOOPGRID_BASE_URL = 'http://127.0.0.1:8000'
   $env:LOOPGRID_WORKSPACE = 'your-workspace-id'
   # For authenticated Core, configure the optional service_key through the
   # Claude plugin manager (sensitive userConfig, stored securely).
   # For local --plugin-dir smoke tests only, use a session-only
   # CLAUDE_PLUGIN_OPTION_SERVICE_KEY without committing it anywhere.
   python .\scripts\doctor.py  # Offline configuration check (no network)
   claude plugin validate .
   # From a separate, disposable working directory:
   # claude --plugin-dir "C:\path\to\loopgrid-claude-code"
   ```

   For macOS/Linux, export the same environment variables and use `python3` only if your system's `python` is not on PATH; the hook executor requires a command named `python` unless you change the hook config to your interpreter.

3. In Claude Code, use `/mcp` to check that the `loopgrid` server is connected; use `/loopgrid:decision`, `/loopgrid:verify`, `/loopgrid:review`, or `/loopgrid:guard`. The MCP server's review tool is disabled by default. Installing the plugin does not grant review authority.

The plugin declares `core_url`, `workspace_id`, and a sensitive `service_key` using Claude plugin `userConfig`. Its hook reads only a fixed allowlist of these and other explicitly named operational settings, rather than enumerating all process environment variables. It never **uses** an inherited machine-wide `LOOPGRID_SERVICE_KEY` for the hook or MCP launcher; the service key is sourced from Claude-managed plugin configuration. The MCP launcher forwards only a short allowlist of OS/runtime values to the downloaded package, deliberately omitting unrelated environment tokens, `PYTHONPATH`, and proxy credentials. This may require additional setup on machines that rely on a corporate HTTP(S) proxy. Remote Core URLs must use HTTPS; HTTP is permitted only for loopback Core. Local developer testing can set `CLAUDE_PLUGIN_OPTION_SERVICE_KEY` in the launching shell without storing it in the repository. On some Claude graphical clients, plugin `userConfig` prompts may require explicit configuration from the plugin manager or Claude Code terminal.

The plugin can also be distributed through a GitHub Claude Code marketplace. The main manifest is `.claude-plugin/plugin.json`; `.mcp.json`, `hooks/hooks.json`, and `skills/` are at the plugin root.

### Validation status (October 11, 2026)

The previous `uv run --locked` plugin passed 50 Windows regression/security tests and real Core/hook/evidence exercises. For the **published** `loopgrid-claude-launcher==0.1.0` integration, Windows MCP stdio discovery returned all six tools; a clean Claude Code `/mcp` session loaded exactly one LoopGrid server with six tools; `uv lock --check` and Claude's strict plugin validation passed. After a CI-environment diagnostic test correction, the current GitHub source at `8b04b09` passed **49 Python tests** on Ubuntu and Windows with Python 3.10 and 3.12. The new hook environment-selection regression test will be included in the next scan; run it on all CI platforms before submission.

The prior five-event sandbox Core run passed with `evidence_complete` and valid signatures in an isolated workspace. The older default workspace had an unrelated existing integrity failure; we do not claim that it passed. A fresh end-to-end decision/execution/outcome test with this *exact* updated launcher and Core was not run, so those results must not be conflated. Details: [VALIDATION.md](VALIDATION.md).

### Decision → policy → authorized execution → outcome → verification

1. Record a proposed action via `/loopgrid:decision` or `loopgrid.record_decision` (redacted/proof-only defaults). Obtain the Core decision ID.
2. Apply an existing, operator-defined LoopGrid policy. For human review, use the authenticated reviewer workflow; the model cannot approve itself.
3. Execute with the **actual external tool**, subject to Claude Code permissions and any separately configured LoopGrid guard. The MCP server does *not* perform external business actions.
4. Capture the execution receipt with `loopgrid.record_action`, or opt into hooks (which record a hash commitment to the tool result).
5. Verify the **downstream system** (for example, payment, ticket, or deployment state), then call `loopgrid.record_outcome` with its reference.
6. Use `loopgrid.verify_evidence`, export the evidence ZIP via `loopgrid.get_evidence`, and check independently with `loopgrid-verify` when needed.

Integrity verification supports evidence provenance and tamper detection; it does not by itself certify the correctness of a business decision or the identity of a reviewer.

## Optional native Claude Code hook modes

By default `LOOPGRID_CLAUDE_MODE=off`: the MCP and skill tools work, but automatic background hooks do not capture evidence or block tool calls. The hooks also require an **explicit project-local activation marker**: `.loopgrid/claude-code.enabled` in the root folder reported by `CLAUDE_PROJECT_DIR`. Without both opt-ins, they exit **before reading tool input**, opening SQLite, or sending network requests. This keeps hook capture out of unrelated projects.

| Mode | Behavior |
|---|---|
| `off` | No automatic tool interception; MCP and skills still work |
| `observe` | Best-effort decision/tool-result evidence for selected tools; Core errors do not block actions; missed records are possible |
| `enforce` | Selected tools require an actual Core policy result `auto_allowed`, persisted before execution; unavailable Core or missing policy denies the call |

For a project you intentionally want to govern, create the empty marker **in that project's root** (not in the installed plugin directory unless you are specifically testing that project):

```powershell
New-Item -ItemType Directory -Force .loopgrid | Out-Null
New-Item -ItemType File -Force .loopgrid\claude-code.enabled | Out-Null
```

Only do this in projects whose operators have opted into tool capture. The marker contains no secrets; removing it disables hook processing for that project. The default `.gitignore` ignores this marker in the LoopGrid source repository. Hook processes locate the project via Claude Code's `CLAUDE_PROJECT_DIR`; if that variable is not provided, hooks do not activate.

Configure **before launching Claude Code**:

```powershell
$env:LOOPGRID_CLAUDE_MODE = 'observe'          # or 'enforce'
$env:LOOPGRID_CLAUDE_TOOLS = 'Bash,Write,Edit,MultiEdit,NotebookEdit,mcp__*'
$env:LOOPGRID_CLAUDE_POLICY_ID = 'your-active-policy-id'   # mandatory for enforce
claude --plugin-dir .
```

The guard never returns `permissionDecision: allow`, so it never intentionally bypasses Claude Code's own permissions. It binds decisions to a hashed `(session_id, tool_use_id)`, an exact tool name and a canonical hash of the input. It persists results and marks evidence-write failures for manual reconciliation instead of retrying the action. Only the selected tools are subject to the guard; the plugin is not a system-wide execution sandbox.

**Policy caveat:** LoopGrid Core v0.8's built-in evaluation presently focuses on numeric amount-threshold rules. A generic code edit or shell command does not normally have the necessary policy fields and will be denied in `enforce` mode. Model-supplied amount values are not independently trusted, and `human_approval_required` is denied rather than auto-resumed by this v0.1.0 bridge. Do not enable enforce globally until you have an applicable Core policy and have validated your exact tool types.

`PreToolUse` can prevent a selected action *when the hook runs and completes*. Claude Code hook disablement, timeout behavior, out-of-band execution, unrelated tools, or an untrusted local machine are separate boundaries; see [SECURITY.md](SECURITY.md). `PostToolUse` captures the tool result, **not an independently observed downstream outcome**.

### Reconciliation

```powershell
python .\scripts\reconciliation_status.py
```

If post-execution persistence fails, inspect the actual external system before recording/reconciling anything. Never re-execute a consequential external action just to fill missing evidence.

## Real Core sandbox validation (no Claude model credits)

With a local LoopGrid v0.8.x Core exposing its demo `refund-policy`, run:

```powershell
python .\examples\core_sandbox_e2e.py
```

This creates a **fresh isolated test workspace and sandbox policy**, records a signed decision, obtains a real Core policy result, executes a **local in-memory sandbox action**, captures its tool receipt, separately observes the sandbox's result, records an outcome, checks the full test-workspace evidence chain, and proves an over-limit action is denied. It does not test real Claude Code dispatch or move money.

## Current Directory status and Verified eligibility

The existing Claude Directory entry is a **draft**, not yet approved or Anthropic Verified. The latest captured source scan (`main @ 8b04b09`) **passed structural validation but reported 4 warnings and 4 policy holds**: pinned-`uvx` dependency review, a false-positive static-asset reference in reviewer documentation, and two credential/environment heuristic findings. The static-asset reference and test fixtures have been cleaned up; an explicit allowlist now restricts hook settings read from the process environment. **The findings are not considered cleared until Anthropic rescans the next commit.** The four listing-field `UNKNOWN_KEY` warnings are informational for fields consumed by the Directory.

`uvx` starts the Python package manager before the launcher's environment filter runs and does **not** enforce this plugin's `uv.lock`. The lockfile is an audit snapshot, not a runtime security guarantee. Three declared lifecycle-hook Python commands run outside the MCP subprocess; the Directory compliance wording needs clarification before final attestation. See [Directory reviewer notes](DIRECTORY-REVIEW-NOTES.md) and [security boundaries](SECURITY.md).

## Validation and release

The latest GitHub CI (`8b04b09`) passed **49 tests** on Ubuntu/Windows with Python 3.10/3.12. The preceding Claude-only launcher also passed seven launcher security tests, Windows six-tool MCP discovery and Ubuntu/Windows/macOS CI. The current patch adds a 50th regression test covering explicitly selected hook environment settings; re-run CI after applying it. The previous real Core lifecycle/evidence tests remain useful but were performed with the older local launcher.

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts examples
uv lock --check
claude plugin validate --strict .
```

The repository includes the genuine 38-entry `uv.lock` generated against published `loopgrid-claude-launcher==0.1.0` and unchanged `loopgrid-mcp==0.1.0`. This file is **not enforced** by the direct `uvx` invocation. Do not submit or claim Verified until the latest portal findings and compliance declarations have been reviewed.

**Repository:** https://github.com/loopgridio/loopgrid-claude-code  
**LoopGrid:** https://loopgrid.io  
**Support:** hello@loopgrid.io  
**License:** Apache-2.0
