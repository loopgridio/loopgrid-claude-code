# Claude community plugin marketplace submission notes

**Candidate**: LoopGrid Decision Evidence, `loopgrid` v0.1.0. The public GitHub repository must exist before submitting. The community review is not the separately curated official marketplace and does not guarantee listing or verification by Anthropic.

## Concise public description

LoopGrid adds signed, tamper-evident decision evidence and policy-aware tool control to Claude Code. It connects six evidence MCP tools and four skills, with optional (off by default) PreToolUse/PostToolUse hooks for policy decisions, tool-result commitments, and independent verification through LoopGrid Core.

## Disclosure for marketplace reviewers

- No analytics, advertising, or external telemetry. The hooks make HTTP(S) requests only to the LoopGrid Core URL selected by the operator; the MCP server is separately installed through pinned `uvx --from loopgrid-mcp==0.1.0` and also talks to Core.
- Hooks register for Bash, file editing, and MCP tool classes but **automatic hook capture is off** until users explicitly set `LOOPGRID_CLAUDE_MODE=observe` or `enforce` **and** activate the individual project using `.loopgrid/claude-code.enabled`. Before reading any event payload, local state access, or network request, the hook checks the `CLAUDE_PROJECT_DIR` root for that explicit marker. It does not monitor unrelated projects. Hook matching can cover multiple tool types inside an opted-in project. Operators can restrict it using `LOOPGRID_CLAUDE_TOOLS`.
- When enabled, hook network payloads include tool name, SHA-256 input/result commitments, hashed session/tool-use IDs, and numeric `amount` if present; **no raw tool arguments or result text** are transmitted by hooks. MCP evidence skills may transmit additional user-approved evidence fields. Local SQLite tracks action correlation but is not an independent tamper-proof ledger.
- Enforcement requires a matching, configured Core policy and verdict `auto_allowed`. Otherwise the matched call is denied. Human-review-required decisions are not automatically resumed; Core signature verification does not establish reviewer identity or downstream truth.
- LoopGrid Core and Python 3.10+/`python`, plus `uvx` are prerequisites. A local or user-administered Core endpoint is required; remote Core endpoints must use HTTPS.
- The sandbox test-only add-on and all locally exported evidence/credentials are excluded from the release source.

## Local commands

```powershell
python -m unittest discover -s tests -q
python -m compileall -q scripts examples
claude plugin validate --strict .
python scripts/doctor.py
claude --plugin-dir .
```

## Submission path

Use https://platform.claude.com/plugins/submit for community review after publishing the source repository. Direct pull requests to the official directory are not the advertised submission route. Preserve the plugin `name` slug `loopgrid` and release tag `v0.1.0` once published.
