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

## Pending before the one Claude plugin GitHub push

- **Completed:** Generated `uv.lock` on Windows (38 lockfile entries, both LoopGrid 0.1.0 pins, published-registry SHA-256 hashes); `uv lock --check` passed on October 11, 2026.
- **Completed:** On Windows, 48 Python tests passed and strict Claude manifest validation passed; the plugin source passed Python compilation. **Still pending:** clean Claude Code `--plugin-dir` six-tool discovery **from outside the source folder**, for this exact candidate.
- Confirm connection to local Core and at least one synthetic decision + successful fresh-workspace verification with the new launcher.
- Revalidate current Directory draft against the new GitHub commit and inspect scanner/Verified findings. These results remain unknown until the portal scans that commit.
- Obtain a permissible interpretation of the Directory compliance attestation covering **declared Python lifecycle hooks** before checking the box. Do not claim Anthropic Verified in advance.

The plugin **does not** execute a real refund or other financial action. Tool-result receipts are not independently observed downstream business outcomes.
