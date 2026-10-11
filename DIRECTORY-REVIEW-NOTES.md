# Claude Directory reviewer notes — LoopGrid Decision Evidence

**Plugin:** `loopgrid` · **Publisher:** LoopGrid · **Contact:** hello@loopgrid.io
**Privacy:** https://loopgrid.io/privacy/ · **Terms:** https://loopgrid.io/terms/

This source is a Directory submission candidate, **not an Anthropic-approved or Verified plugin**. The latest captured portal scan evaluated `main @ 8b04b09` and reported four policy holds and four listing-field warnings. Run **Re-validate** again after this patch is pushed; do not assume that a scanner finding has cleared merely because its source was improved.

## Actual executable surfaces and user consent

- **MCP:** `.mcp.json` launches the published, pinned `uvx loopgrid-claude-launcher==0.1.0`, which depends on **unchanged** `loopgrid-mcp==0.1.0`. The server exposes six decision/evidence tools. It does not make a refund or execute an external business action.
- **Hooks:** three declared Python commands handle `PreToolUse`, `PostToolUse`, and `PostToolUseFailure`. These commands execute **outside the MCP subprocess** and are visible in `hooks/hooks.json`. They exit without reading hook events, writing state, or contacting Core unless both `LOOPGRID_CLAUDE_MODE=observe|enforce` **and** the current project's `.loopgrid/claude-code.enabled` marker are set.
- **Diagnostics/tests:** the offline diagnostic does not contact Core. Developer unit tests use mocked Core responses and loopback HTTP only. Security tests that check HTTPS policy use reserved non-operational example hostnames; they do not send requests to those hostnames.
- **Icon:** the plugin's image is a static manifest asset. No command or interpreter executes or reads that image as program code.

## Network boundaries and service key

- Enabled hooks send tool names, input/result SHA-256 commitments, hashed identifiers and numeric policy fields to the **operator-configured LoopGrid Core**. The hooks do not send raw tool arguments or response bodies; a commitment of low-entropy text may still reveal information through guessing.
- Invoked MCP tools can transmit additional user-approved decision/evidence records, possibly including personal information. The Core may retain those records longer than 30 days. Correlation state is also stored locally in SQLite. There is no separate analytics destination.
- The only **intended** service-key source is Claude's `userConfig.service_key` with `sensitive: true` (`CLAUDE_PLUGIN_OPTION_SERVICE_KEY` for an explicitly configured session). The hook **does not read `LOOPGRID_SERVICE_KEY`** and extracts only named plugin/operational settings using `os.getenv`, never enumerating the full environment as its configuration. HTTPS is mandatory for remote Core; only loopback permits HTTP. Credential-bearing requests reject HTTP redirects.
- The published launcher filters unrelated inherited application environment settings **after `uvx` starts**, but the package-manager process receives its parent's environment beforehand. This is an explicitly disclosed dependency-installation boundary, not proof that an API credential was exfiltrated.

## Captured scan findings and reviewer disposition

1. **`LAUNCHER_PACKAGE_REVIEW` (policy hold):** `uvx` pins the launcher distribution at `0.1.0`, but that invocation does not enforce the adjacent `uv.lock` for transitive runtime installation. `uv.lock` is a registry-resolved **audit snapshot**, **not** a launch-time lock. The upstream package is published separately. We request human review of the dependency chain; we do not claim the Verified-specific rule is automatically satisfied.
2. **`UNREAD_ASSET_REFERENCED` (policy hold on the former reviewer notes):** the referenced image is static and never an executable. This document no longer spells its asset path. Please check the actual interpreter/command targets; none points to the image.
3. **`MCP_FORWARDS_CREDENTIAL_ENV` (test finding):** the prior scanner matched a remote-address syntax in developer security tests with a credential-bearing mock environment. The HTTPS test now uses a reserved `.invalid` documentation hostname without making a network request; credential-bearing transport tests operate on loopback. These tests are not run at plugin install.
4. **`MCP_FORWARDS_CREDENTIAL_ENV` (combined plugin finding):** named runtime settings are read locally, and an explicitly selected service key is sent only in the `X-LoopGrid-Key` header to the configured Core. The hooks do not enumerate all environment variables or send machine-wide service keys. Please review the declared hooks and Core transport together; these are legitimate product behaviors, not a claim of zero credential use.

The Directory also reports the four fields `documentationUrl`, `privacyPolicyUrl`, `supportUrl`, and `termsOfServiceUrl` as unknown **to the Claude Code runtime** while confirming they are used for the Directory listing. These can remain. The static image and local-only MCP information notices are not policy holds by themselves.

## Reviewer demonstration (synthetic data only)

1. Record a *fictional* refund proposal in LoopGrid, without executing a refund, and note the returned decision ID.
2. Explain `off`, `observe`, and `enforce` modes and the explicit project activation marker; do not activate anything without permission.
3. Verify a sandbox decision and export its evidence ZIP, distinguishing Core-side verification from the separate offline verifier.

Reviewer test access to a temporary Core sandbox can be arranged privately. Never commit service keys, real customer records or personally identifiable test data.

## Compliance attestation — clarification needed before submission

The Directory form states that the plugin does not exfiltrate credentials **or execute code outside declared MCP servers**. The plugin has three **separately declared Python lifecycle-hook commands**, and their execution is not inside the MCP subprocess. The form currently shows four acknowledgements checked. Seek Anthropic's interpretation or adjust the attestation before submitting if this makes the statement inaccurate; transparency is more important than removing a warning.
