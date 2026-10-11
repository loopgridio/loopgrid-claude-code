# Validation record and limitations

This document distinguishes real user-observed tests from tests still required for the **new** published launcher arrangement.

## Completed on Windows (October 11, 2026)

- Previous `uv run --locked` plugin: 50 Python tests passed; strict Claude Code plugin validation and genuine `uv.lock` check passed.
- Windows Claude Code 2.1.292: original plugin MCP connected with six LoopGrid tools in a clean disposable project.
- Original plugin + LoopGrid Core 0.8.1: recorded synthetic proposed refund decisions; retry with same idempotency key replayed without duplicating evidence.
- Fresh Core workspace `ws_6f03674a26654418`: synthetic five-event Core sandbox policy allow/deny, outcome evidence and signed workspace verification passed.
- Live Claude Code tool hook: local SQLite showed `Bash | result_recorded`; the corresponding Core decision `dec_009b1bdc33d64086a85eb8a4` verified `valid=true`, three checked decision events, no failures (10 workspace ledger events).
- Exported signed evidence ZIP: checksum matched; `loopgrid-verify==0.1.0` reported `[OK] VERIFIED`, bundle integrity attested. The signer key ID was supplied from Core; independent real-world signer identity was not established through separately trusted public-key material.
- A separate historical `default` workspace had a **known ledger hash-chain failure at event 89**. Never claim that workspace passed integrity checks; isolated test workspace was valid.

## Published Claude-only launcher tests

- `loopgrid-claude-launcher==0.1.0` was independently published to PyPI from `loopgridio/loopgrid-claude-launcher` using GitHub OIDC trusted publishing.
- User installed the published package with `uvx --from loopgrid-claude-launcher==0.1.0 loopgrid-claude-launcher`; Windows MCP stdio discovery returned **all six LoopGrid tools**.
- Security smoke test on the previously built launcher reported inherited AWS and machine-wide LoopGrid service keys filtered, explicitly selected service key forwarded, and remote non-HTTPS Core rejected.
- Launcher repository GitHub CI was green on Ubuntu, Windows, and macOS (Python 3.12).

## Current Claude plugin release checkpoint (October 11, 2026)

- **Completed:** Genuine `uv.lock` generated and checked on Windows (38 resolution entries; the published `loopgrid-claude-launcher==0.1.0` and `loopgrid-mcp==0.1.0` packages are represented).
- **Completed:** Clean Windows Claude Code `/mcp` smoke test using the pinned published `uvx` plugin showed a connected `plugin:loopgrid:loopgrid` server and all six tools. Strict manifest validation passed.
- **Completed:** GitHub `main @ 8b04b09` CI passed **49 unit tests** on Ubuntu and Windows, Python 3.10 and 3.12. A prior CI run failed because the diagnostic test assumed uv existed on bare runners; the test was corrected and CI passed.
- **Prepared:** A narrow scanner-review patch changes only hook environment selection, a few security test fixtures and submission documentation. It passes **50 local tests**. Re-run all GitHub CI jobs and Claude manifest validation after committing.
- **Captured Anthropic scan:** `main @ 8b04b09` structurally passed but still reported **4 policy holds** and **4 field warnings**. The next source scan is needed to determine which, if any, clear. The `uvx` transitive dependency review remains a substantive human-review question.
- **Before submission:** verify the form's compliance attestation for the three declared Python hook commands, confirm actual Core data retention matches the privacy description and obtain an Anthropic reviewer interpretation if necessary.

The plugin **does not** execute a real refund or other financial action. Tool-result receipts are not independently observed downstream business outcomes.
