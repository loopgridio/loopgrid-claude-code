# Validation record — Claude Code plugin 0.1.0 candidate

## Tests that can be performed without Claude API credits

- Plugin JSON manifest, hook JSON and MCP JSON parse and structure checks.
- Hook bridge pre/post/failure contract with deterministic Claude Code hook inputs.
- Only protected tools matched; LoopGrid MCP tools excluded to prevent recursion.
- Default off behavior; observe-mode best-effort handling; enforce-mode fail-closed without Core/policy.
- Auto-allowed policy permits normal host permission flow without returning `allow`.
- Blocked, human-approval-required, and unknown policy results denied.
- Input mismatch, forged post callback, replay/duplicate tool-use ID denied, SQLite ledger durability.
- Post-execution evidence persistence failure marked `needs_reconciliation`, with no automatic action replay or fictitious complete outcome.
- Credential leakage controls and canonical SHA-256 evidence commitments.

## Validated on Windows (October 2026)

- 40/40 standard-library Python security/contract tests passed after Windows SQLite cleanup and policy-denial wording fixes (`python -m unittest discover -s tests -q`); compilation passed.
- `claude plugin validate .` passed using **Claude Code CLI 2.1.292**. `uvx 0.12.17` available.
- `claude --plugin-dir .` loaded the four skills (`decision`, `review`, `verify`, `guard`) and all three plugin hooks (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`). The `loopgrid` MCP server connected and exposed six tools.
- **Real runtime observation:** Claude Code executed Bash `echo LOOPGRID_CLAUDE_HOOK_TEST` once, the plugin persisted `result_recorded` for a decision with three signed events, Core verification returned valid, and exported attested bundle `dec_d051d1d4563e4c20a89fec88` independently passed `loopgrid-verify==0.1.0`.
- **Real runtime missing-policy denial:** With `LOOPGRID_CLAUDE_MODE=enforce` and no policy ID, a Bash file-creation attempt failed closed; the file did not exist.
- **Real configured policy:** Core `claude-sandbox-refund` returned `manual_review_required` for a Bash call without an amount, and Claude Code blocked it. Denied decision `dec_522fa8f2892044b68de07cef` had two valid signed events; its attested bundle passed independent offline verification.
- **Real policy allow:** Test-only local MCP server `loopgrid_sandbox` invoked `sandbox_refund` with `amount=25` once, `executed_now=true`, `duplicate=false`, and `real_money_moved=false`. Independent SQLite receipt count was one. Hook ledger recorded `result_recorded` for `dec_06181a3ef97b484f9ec8811a`; real Core included `decision_created`, `policy_evaluated`, `tool_requested`, and `tool_result`, with valid Ed25519/SHA-256 verification of all four events. Policy payload is proof-only, so it does not reveal the `auto_allowed` value; the strict enforce bridge code permits tool execution only for exactly that Core verdict.
- **Real policy block:** The same sandbox MCP server invoked with `amount=2500` was rejected by `PreToolUse` as `blocked`; a read of the test-only server receipt database returned **zero** executions. No real payment ever occurred.
- **Real Core isolated E2E:** A new workspace (`ws_40da4a0313534178`) produced one local sandbox execution, separately observed outcome, five signed events, `lifecycle=evidence_complete`, and `verificationValid=true` on Core `0.8.1-design-partner`. This is distinct from the Claude tool-observation test, which did not claim an observed downstream outcome.
- **Historical workspace alert:** The earlier shared `default` workspace has one verifier failure at sequence 89 (`previous_chain_hash_mismatch`, `chain_hash_mismatch`) on another historical decision. The test workspace above is independently valid. The historical failure has **not** been repaired or hidden and must be investigated separately without deleting/reconstructing evidence.
- The separate local sandbox policy add-on was tested on Windows and is **not part of the publishable plugin**. Real Claude Code sessions use the user's Claude account; none of the evidence E2E actions moved money.

## Additional verification before submission

- Run `claude plugin validate --strict .` on the exact upload directory if supported by the installed CLI.
- Publish and confirm GitHub CI on a clean checkout, then test install from the published repository as a new user.
- Independent reviewer should inspect the default-off, broad hook matcher and network/data disclosures against the community marketplace's safety standards; narrow `LOOPGRID_CLAUDE_TOOLS` to the tools being governed.
- Test the configured plugin on another operating system and inspect any platform-specific path/stdio issues.
- Test authenticated Core and production reviewer authority separately if those features are advertised for your customer environment.

## Repeatable validation commands and review checklist

1. `python -m unittest discover -s tests -v` in a clean checkout.
2. `claude plugin validate ./loopgrid-claude-code` (prefer `--strict` after confirming Claude Code version supports it).
3. Run `claude --plugin-dir ./loopgrid-claude-code`, verify `/mcp`, execute each named skill, confirm `loopgrid-mcp==0.1.0` protocol/transport connects and that the six tools are present.
4. With local Core v0.8.x, run `python examples/core_sandbox_e2e.py` to create an isolated test workspace and policy, exercise a synthetic tool receipt and separately observed outcome, and verify the test workspace chain. Diagnose the old shared workspace using `python examples/inspect_workspace_integrity.py dec_...`. Then export the evidence ZIP and run standalone `loopgrid-verify` off-host. The script does not itself perform independent offline verification.
5. Configure `observe` with guarded harmless shell/file calls. Check a per-tool Core record and SQLite correlation. Test a simulated Core outage.
6. Configure `enforce` with an actual applicable auto-allow policy and sandbox tool. Check authorized, denied, missing policy, changed tool arguments, replay and failure-reconciliation cases. Verify Claude Code really honors the deny JSON and that local hook timeouts do not undermine your required security boundary.
7. Verify both Windows PowerShell and one Linux/macOS environment, including `uvx` and the `python` executable.
8. Run a second-person security review of consent, plugin installation side effects, and scopes before marketplace submission.

The existing LoopGrid n8n/Dify verified listings do not confer Claude Code verification. Community acceptance and Anthropic verification are separate decisions.
