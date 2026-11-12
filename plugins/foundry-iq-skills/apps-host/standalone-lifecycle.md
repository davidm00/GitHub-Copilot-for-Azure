# Selection, cancellation and shutdown

Selecting a graph or schema record updates its scoped reference automatically;
there is no separate **Select evidence** action in the Graph Playground.
Open **Connected Sources**, then expand
**Technical details** to inspect the exact packet, server, session and resource.
No agent conversation is connected and no
model consumed the packet. The shared views show chat-specific selection wording
only when a host genuinely advertises `message.text`; context-only viewers do not
direct users to a nonexistent host chat or show an unavailable Explain action.
This viewer advertises context receipt but never `message.text`, sampling or an
agent backend. In embedded context-only hosts, **Select evidence** remains an
explicit receipt action. Selection uses the official `updateModelContext` exchange;
the copy does not add or simulate a capability.

**Clear results** sends public `ui/resource-teardown` through the official bridge
while the transport still exists. It waits at most five seconds for the matching
successful response, then removes listeners/frame and releases the session.
Missing, wrong-ID, late or rejected responses produce an explicit teardown error,
not a successful graceful-close claim. Retained graph/evidence sessions are all
released; repeated disposal is idempotent. **Cancel request** aborts pending work
and clears that tab's results without changing the other tabs.
**Reconnect server** retires that server's old sessions and reconnects explicitly;
there is no CLI fallback or background retry.

Type `quit` and Enter, or press Ctrl+C, in the launcher terminal to stop the
loopback servers and their owned MCP processes. Keep that terminal open while
using the viewer. Closing a browser tab is not the documented host stop operation.
On shutdown the connector stops owned processes, rather than claiming graceful
browser teardown after the browser is gone.

[Prerequisites and setup](standalone-setup.md) | [Launch](standalone-launch.md)
