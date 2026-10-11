# Anthropic Claude Directory — reviewer notes

**Plugin:** LoopGrid Decision Evidence (`loopgrid`) · **Contact:** hello@loopgrid.io · **Privacy:** https://loopgrid.io/privacy/ · **Terms:** https://loopgrid.io/terms/

This repository does **not** claim to be approved or Anthropic Verified. The scanner must be run again after the new GitHub commit is pushed.

## Declared execution surfaces

- `.mcp.json`: one local `stdio` server, `uvx loopgrid-claude-launcher==0.1.0`. This **published** Claude-only launcher delegates to **unchanged** `loopgrid-mcp==0.1.0`. The direct pinned `uvx` shape is proposed to satisfy the scanner's prior `LAUNCHER_UNSUPPORTED` finding.
- `hooks/hooks.json`: three native Python lifecycle hooks for PreToolUse, PostToolUse and PostToolUseFailure. Hooks are **off** unless both an operator sets `LOOPGRID_CLAUDE_MODE=observe|enforce` and a project has `.loopgrid/claude-code.enabled`. Enabled hooks run as separate declared local commands; they are not part of the MCP subprocess.
- `scripts/doctor.py`: manual **offline** diagnostic; no network requests.
- `tests/test_hook.py`: developer-only mock/loopback tests, not executed on install; no executable PNG references.
- `.claude-plugin/icon.png`: asset file only; not an executable.

## Network and credentials

MCP tools and enabled hooks contact the **operator-configured LoopGrid Core**; neither subsystem contacts a separate analytics provider. MCP tools can submit user-authorized decision/evidence payloads (including personal information if present) and Core may retain them beyond 30 days. Opted-in hooks send tool names, input/result SHA-256 commitments, hashed identifiers and numeric policy fields, not raw tool contents. Hooks keep local SQLite correlation records. Default bundle export excludes raw payloads.

Claude's sensitive `userConfig.service_key` option is the only intended source of the MCP and hook service key. The Claude-only launcher clears inherited arbitrary application environment values **after `uvx` starts**, but `uvx` itself receives the initial parent environment during dependency installation. That limitation cannot be eliminated by Python-level filtering alone; assess package-manager/network proxy controls and trusted registry access separately.

The repository's `uv.lock` is generated from published registry versions for review. **It is not an enforced runtime lock for direct `uvx`**. We do not claim otherwise. Confirm whether the Directory's Verified checker accepts this packaging shape.

## Prior scanner findings (commit f2cb2de, not a new scan)

1. Launcher package review / transitive dependencies: a pinned `uvx` launcher replaces unsupported `uv run`; generated `uv.lock` provides audit snapshot. **Outcome pending rescan**.
2. Executable test referencing PNG asset: removed test-only asset reference. **Outcome pending rescan**.
3. Credential + remote fixture combination: changed tests to isolated/local/documentation fixtures; legitimate plugin key access remains. **Outcome pending rescan**.
4. Combined environment access + network diagnostic: `doctor.py` now offline; enabled hooks still intentionally contact configured Core. **Outcome pending rescan and possible human review**.

## Three reviewer demo prompts

1. “Record a **synthetic** $15 refund proposal in LoopGrid, **without executing a refund**, and report the returned decision ID.”
2. “Describe the LoopGrid guard modes and project-local opt-in marker. Do not activate a hook or modify permissions.”
3. “Verify a test decision, then export its evidence ZIP. Distinguish service-side verification from independent offline verification.”

Reviewer test access to a temporary Core sandbox may need to be coordinated privately. Do not commit service keys or real customer records.

## Compliance attestation caution

The Directory UI asks whether the plugin exfiltrates credentials or executes code outside declared MCP servers. This plugin has three **declared Python hook commands outside the MCP process**. Obtain confirmation from Anthropic on the intended interpretation before acknowledging a statement that might be literally inaccurate. Any credential exfiltration must be ruled out through actual review, not by checkbox selection.
