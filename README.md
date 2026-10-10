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

The bundled MCP configuration starts the independently published `loopgrid-mcp==0.1.0` through `uvx`, which **downloads the Python package and its dependencies on first use** if not cached. MCP tools record data only when invoked and may send additional operator-approved decision content to the connected Core; the default evidence export excludes payloads. The plugin has **no analytics endpoint or separate usage telemetry**. Review the declared LoopGrid endpoint and credentials before enabling capture. Enabling this plugin is not an authorization to send unrelated sensitive tool data.

### Installation

Prerequisites: Claude Code installed, Python 3.10+ available as `python`, `uvx` (from the [uv](https://docs.astral.sh/uv/) toolchain) available on PATH, and a reachable LoopGrid v0.8.x Core. The plugin uses the existing published [loopgrid-mcp==0.1.0](https://pypi.org/project/loopgrid-mcp/) and downloads it on first launch through `uvx`.

1. Download or clone the repository into a directory named `loopgrid-claude-code` and open a terminal **inside that folder**.
2. Set the LoopGrid configuration in the **terminal that starts Claude Code**. For local evaluation on Windows PowerShell:

   ```powershell
   $env:LOOPGRID_BASE_URL = 'http://127.0.0.1:8000'
   $env:LOOPGRID_WORKSPACE = 'your-workspace-id'
   # On an authenticated Core, set LOOPGRID_SERVICE_KEY with an appropriately scoped credential.
   python .\scripts\doctor.py
   claude plugin validate .
   claude --plugin-dir .
   ```

   For macOS/Linux, export the same environment variables and use `python3` only if your system's `python` is not on PATH; the hook executor requires a command named `python` unless you change the hook config to your interpreter.

3. In Claude Code, use `/mcp` to check that the `loopgrid` server is connected; use `/loopgrid:decision`, `/loopgrid:verify`, `/loopgrid:review`, or `/loopgrid:guard`. The MCP server's review tool is disabled by default. Installing the plugin does not grant review authority.

The plugin can also be distributed through a GitHub Claude Code marketplace. The main manifest is `.claude-plugin/plugin.json`; `.mcp.json`, `hooks/hooks.json`, and `skills/` are at the plugin root.

### Validated with real Claude Code on Windows

The v0.1.0 integration has been tested in Claude Code 2.1.292 on Windows with LoopGrid Core 0.8.1: **44/44 Windows security and regression tests on the project-scoped update**, with strict Claude Code plugin validation and GitHub Actions passing, valid plugin manifest, six connected LoopGrid MCP tools, all four skills and three registered hooks, a real observed Bash tool result, and independently verified attested evidence bundles. A configured policy permitted a harmless **$25 sandbox MCP action exactly once**, denied a **$2,500 sandbox action with zero executions**, and returned `manual_review_required` for a generic Bash action without the policy's required amount. The amount-25 and review-required decisions had valid Core evidence; independent offline verification was also completed for the observed Bash action and review-required denial. No financial transaction occurred.

The isolated five-event sandbox Core test passed with `evidence_complete` and valid signatures. A *separate historical* `default` test workspace has a chain mismatch at sequence 89. No evidence was erased or rewritten; see [VALIDATION.md](VALIDATION.md) for the distinction. Tests do not establish that this plugin has been endorsed or reviewed by Anthropic.

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

## Validation and release

This is a tested Claude Code plugin **not yet marketplace approved or endorsed**. Project-scoped hook activation was tested on Windows (44/44 tests), and a real opted-in Claude Code project recorded a new Bash tool result (`result_recorded`, decision `dec_0f7044dc46f342fb85a78288`). The existing LoopGrid MCP tool contract and Python Agent SDK are separate integrations. All Windows validation results and the boundaries of the tests are recorded in [VALIDATION.md](VALIDATION.md). Real Claude Code runtime discovery, hook observation/enforcement, and independent offline verification were demonstrated; we still recommend a second-person security/privacy review and macOS/Linux smoke test before submitting for community review.

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts
claude plugin validate .
```

**Repository:** https://github.com/loopgridio/loopgrid-claude-code  
**LoopGrid:** https://loopgrid.io  
**Support:** hello@loopgrid.io  
**License:** Apache-2.0
