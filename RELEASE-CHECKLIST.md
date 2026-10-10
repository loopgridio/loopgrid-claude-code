# Release checklist

- [x] Plugin skeleton with `.claude-plugin/plugin.json`, `.mcp.json`, skills, and hooks.
- [x] Reuse published loopgrid-mcp 0.1.0 instead of maintaining a duplicate MCP implementation.
- [x] Distinguish proposed/policy/review/executed/outcome/verified evidence; no false complete claims.
- [x] Default safe opt-in for automatic hooks; deterministic, selective fail-closed enforcement mode.
- [x] Local Python unit and serialization tests green in Linux sandbox (40 tests, 12 repeated runs).
- [x] Windows rerun 40/40 passing after SQLite cleanup fix.
- [x] `claude plugin validate .` green on Claude Code 2.1.292 (Windows).
- [x] Real Claude Code MCP discovery (6 tools) and all four skills / three hook registrations verified.
- [x] Corrected real Core E2E in isolated workspace on Windows 0.8.1 with `verify.valid: true` and five events.
- [x] Corrected isolated-workspace E2E passed in local Core source test harness v0.8.0.
- [x] Identify original `default` workspace verification failure at seq 89 without deleting/mutating evidence. Investigation of its historical origin is separate and open.
- [x] Export attested evidence ZIPs for real observed execution and policy-review denial and independently verify with `loopgrid-verify`.
- [x] Publish independent GitHub repository and validate GitHub Actions (`632bcf0`, green).
- [ ] Publish and Windows-validate the project-scoping security patch (recheck CI).
- [ ] Obtain a second-person permissions/privacy review before marketplace submission.
- [ ] Submit to Anthropic community plugin form (NOT a direct PR to the official plugin repository).
- [ ] Community directory approval recorded only after Anthropic actually approves.

The runtime hook, MCP discovery and offline-verification gates passed on Windows. Publishing and independent submission review remain separate milestones.
