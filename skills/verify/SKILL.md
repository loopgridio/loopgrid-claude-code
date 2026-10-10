---
name: verify
argument-hint: "decision_id"
description: Retrieve and verify LoopGrid signed decision evidence; distinguish connected Core verification from independent offline bundle verification.
---

# LoopGrid: verify decision evidence

Get the decision ID from `$ARGUMENTS`. Use `loopgrid.verify_evidence` on the installed LoopGrid MCP server. Report the exact fields returned, including verification validity, coverage or missing stages if provided. Do not guess a verification score.

For portability, use `loopgrid.get_evidence` with `include_payloads: false` unless the operator explicitly authorizes disclosure. This saves the bundle to the operator-configured evidence directory and returns its checksum. Check the bundle out-of-band with the standalone `loopgrid-verify` CLI if independent offline verification is requested.

A valid hash chain/signature demonstrates evidence integrity and provenance under the relevant key-trust assumptions. It does **not** by itself prove policy correctness, legitimate reviewer identity, absence of omitted events, or the truth of upstream business facts. Connected-service verification is **not** the same as independent verifier execution.
