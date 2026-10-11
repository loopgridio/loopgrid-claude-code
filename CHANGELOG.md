# Changelog

## 0.1.0 — Claude Directory submission candidate

- Claude Code plugin with four evidence/review/verification/guard skills.
- Configured to use the published `loopgrid-mcp==0.1.0` Python stdio server.
- Native optional PreToolUse/PostToolUse/PostToolUseFailure bridge for decision-scoped proof and tool receipts.
- Operator-controlled observe and fail-closed enforce modes with policy integration and durable SQLite receipt tracking.
- Windows SQLite initialization-failure connection cleanup fix; concurrency cleanup regression test.
- No claims of marketplace approval or of independent downstream outcome observation from the tool hooks.

### Release validation (October 2026)

- Windows: 40/40 tests; Claude Code 2.1.292 plugin validation; native MCP and hook discovery.
- Real observed tool, configured policy auto-allow/block and review-required denial, signed Core evidence and independent attested bundle verification.
- Fixed Windows SQLite initialization cleanup and clarified hard policy block versus human-review-required messaging.
- No external money moved. The plugin is not yet approved or endorsed by Anthropic.

### Directory candidate update (October 11, 2026)

- Uses published standalone `loopgrid-claude-launcher==0.1.0` via pinned `uvx`, without modifying `loopgrid-mcp==0.1.0`.
- Adds link and data-handling disclosures and separates Verified-specific release checks from core functionality.
- Includes registry-resolved 38-entry `uv.lock` from Windows; the pinned `uvx` command does not enforce this lock at runtime.
- Still requires a clean Claude Code smoke test with this exact candidate and fresh Anthropic revalidation before submission.
