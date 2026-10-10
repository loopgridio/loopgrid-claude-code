---
name: guard
argument-hint: "off | observe | enforce"
description: Explain and configure optional LoopGrid tool evidence hooks for Claude Code with explicit modes and policy failure behavior.
---

# LoopGrid: Claude Code tool hooks

`$ARGUMENTS` selects the desired mode. Never change environment variables or configuration automatically; provide operator instructions.

- `off` (default): MCP and the evidence skills work, but automatic hooks do nothing.
- `observe`: native PreToolUse/PostToolUse hooks attempt to record decision and tool-receipt commitments with LoopGrid. Unavailable Core does not block the operation; therefore a complete audit trail is **not guaranteed**.
- `enforce`: for configured guarded tool names, PreToolUse requires a reachable LoopGrid Core, a configured policy ID, a recorded evaluation with **exactly** `auto_allowed`, and a persisted request record. Otherwise the hook returns `permissionDecision: deny` before the tool executes. It NEVER returns `allow`, so Claude Code's other permission checks still apply.

Only operate on explicitly opted-in projects: require `.loopgrid/claude-code.enabled` in the project root supplied by Claude Code via `CLAUDE_PROJECT_DIR`. Without this marker the hooks perform no capture or enforcement even if the global mode is `observe` or `enforce`. Tell the operator how to create or remove the marker; never create it on the model's initiative.

Configure `LOOPGRID_CLAUDE_MODE`, `LOOPGRID_BASE_URL`, `LOOPGRID_WORKSPACE`, `LOOPGRID_SERVICE_KEY`, and (for enforce) `LOOPGRID_CLAUDE_POLICY_ID` in the operating system environment *before launching Claude Code*. `LOOPGRID_CLAUDE_TOOLS` optionally sets a comma-separated allowlist of tool-name patterns. Mode settings do not authorize non-matching tools, cover other clients, or prevent an administrator from disabling a plugin.

The current Core policy evaluator chiefly implements `amount_threshold`: a generic Bash action will not produce the required numeric policy evidence and should be **denied** in enforcement mode. Model-supplied amount data is not independently trusted. Human-approval-required decisions are deliberately denied by this v0.1.0 automatic gate; use LoopGrid's authentic review workflow and do not claim automatic resume/approval support.

The hook stores tool arguments and results as SHA-256 commitments, not raw text. PostToolUse is an execution receipt, not independently observed business outcome. Read `README.md`, `SECURITY.md`, and `VALIDATION.md` before enabling enforcement.
