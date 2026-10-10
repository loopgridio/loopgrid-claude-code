---
name: decision
description: Record a consequential agent decision with LoopGrid, capture policy evidence, and guide an authorized external action through separately recorded execution and observed outcome.
argument-hint: "what action and why"
---

# LoopGrid: decision evidence

For `$ARGUMENTS`, identify the **specific proposed action**, what system would execute it, the decision authority, and the business context. Confirm with the user which facts and sensitive data are appropriate to record.

Use the LoopGrid MCP server (`loopgrid.record_decision`) with `privacy_mode: redacted` or `proof_only` and `proposed_action` that identifies the action. Include a policy ID **only when it is provided by the operator**. Never invent an authorized policy or claim a policy approved an action without the recorded decision.

Check the response for `decision_id`, policy evaluation verdict and any review requirement. If policy demands human approval, stop and request a real authorized reviewer outside the model; never self-approve, spoof a reviewer identity, or use the model's statement as human authorization.

For real actions, perform the external tool call only through the host's own permission/security checks and any LoopGrid policy gate the operator has configured. After a tool genuinely returns, record an execution receipt with `loopgrid.record_action`. Record `loopgrid.record_outcome` **only after** observing downstream state independently (e.g. reconciling a transaction ID with the payment provider, or checking deployment status).

Finally call `loopgrid.verify_evidence`, identify it as *connected-Core verification*, and offer an exported evidence bundle with `loopgrid.get_evidence`. Independent off-host verification requires `loopgrid-verify` on the bundle.

Always distinguish: proposed, policy evaluated, human reviewed, executed, outcome observed, verified. Do not label a chain complete when any required stage is absent.
