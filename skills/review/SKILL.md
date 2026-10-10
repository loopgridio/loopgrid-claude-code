---
name: review
argument-hint: "decision_id"
description: Prepare a real human review for a LoopGrid decision that requires approval or rejection, without spoofing reviewer identity.
---

# LoopGrid: human review

Inspect the supplied decision `$ARGUMENTS` and recorded policy outcome before suggesting a review. Present the proposed action, evidence commitments, policy reason, and the requested approval scope to the authorized **human** reviewer. Never infer consent from silence.

The LoopGrid MCP `loopgrid.record_review` tool is **disabled by default**. It should only be enabled by an operator who configured a real reviewer identity and whose MCP host requires explicit human confirmation. If disabled, tell the user how to use their authenticated LoopGrid review workflow. The model must never fabricate a review, impersonate a reviewer, or convert a model output into a human-approval event.

After a real review, confirm the Core record reflects it. A review of decision A does not authorize a different tool name, arguments, workspace, or decision B. If the Claude Code hook is running in `enforce` mode, its current v0.1.0 gate accepts only `auto_allowed`; a `human_approval_required` verdict remains blocked until a separately validated review/resume workflow is implemented.
