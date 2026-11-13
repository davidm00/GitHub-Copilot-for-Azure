# Errors and acceptance limits

Missing runtime payload, Python, verified bootstrap setup or a supported MCP
version prevents readiness. Inspect bootstrap `status` and complete `setup`
with configured pip sources; do not point the host at an old console executable or
remove negotiation/sandbox checks. Domain failures and disconnected servers are
visible, not empty successful graphs. A cancelled server needs explicit reconnect.

`PROTOCOL_UNSUPPORTED` identifies an explicit incompatible version reply.
`NEGOTIATION_FAILED` means discovery did not establish protocol support: check
bootstrap setup and server startup/dependency failures, not just SDK versions.
The pinned protocol and no-fallback policy are unchanged. Owned servers run the
`server/discover` probe in place on the one supervised process, so startup
diagnostics cover the process that failed. `NEGOTIATION_FAILED`,
`APPS_UNAVAILABLE` and `PROTOCOL_UNSUPPORTED` messages end with a bounded
(at most 20 lines, 2 KiB), redacted tail of that server's stderr (tokens, keys,
signatures, URL query strings and the home directory are masked), or state that
the server wrote none. Logs keep byte counts only; the full retained tail stays a
private, non-enumerable property of the error.

Source/protocol fixtures and real-browser host regressions are separate evidence
from installed-plugin and genuine-data acceptance. Earlier Python MCP 2.3.0
metadata-only sessions covered Entity, Topic Graph and ontology and their six HTML resources,
not grounding, without tool/model/Azure calls. Those checks do not prove
a new live data journey or stock product-host compatibility. Historical direct-CLI
ZIP/live receipts do not certify this new distribution.

Descriptor-scoped comparison guard evidence establishes the unavailable state
and no automatic dispatch, not full comparison acceptance. Supported-path local
mocks prove regression behavior only. Full-product acceptance requires separately
verified live scopes, including a real KB, and installed browser qualification.

The first external-host candidate is stock Claude Desktop: its primary Apps guide
documents local stdio configuration. Installation, version/account/policy, actual
rendering and agent consumption remain separately scoped acceptance work. No
patched product host or model-backed standalone conversation is part of this host.

[Prerequisites and setup](standalone-setup.md) | [Launch](standalone-launch.md)
