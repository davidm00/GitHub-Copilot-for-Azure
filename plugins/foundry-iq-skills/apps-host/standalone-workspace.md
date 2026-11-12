# Graph Playground and query modes

Open the exact `Graph Playground ready: http://127.0.0.1:<port>` address, not
`localhost` or a machine name. Startup discovers real MCP resources and App-only
reads. Readiness and `/health` describe MCP connections, not upstream Search
health, corpus availability or successful model calls.

**Connected Sources** counts connections and checks their current health.
**Connected** opens **Reconnect server**; **Disconnected · Connect** connects
directly. Disconnected servers reconnect on page load without querying.
A submitted query reconnects a disconnected source and retries a stale
connection once; other failures remain visible without replay.
**Technical details** contains operator metadata and selected-context diagnostics.

The **Graph Playground** has keyboard-accessible **Knowledge Graph**,
**Topics**, **Ontology** and **Grounding** tabs for configured domains.
Tabs retain inputs, results and context. Topics, Ontology and Grounding
load once on first activation; reopening reuses the result.
Knowledge graph never submits an initial query.
**Why Graph** never queries on activation, reopening or reconnect. Starters only
fill the question; **Ask** submits. Comparison and **Synthesize (KB)** require a
nonempty KB endpoint and explicit document, graph and agentic retrieval in the
selected descriptor, not a tool enum. Missing/invalid metadata disables comparison
with a reason, not ordinary graph queries. Local metadata is checked at connection
and KB dispatch without Azure probes. Reconnect clears comparison results and
discovered starters; results are not cached. Descriptor changes require reconnect
and explicit submit.

For Knowledge graph, Topics and Ontology, each tab defaults directly
to its main presenter and inline Evidence panel.
The Entity Graph query or
selected ontology type/version or Topic Graph chunk is retained; otherwise enter a
verified selector. Required selectors are visible;
optional bounds remain in **Query options**. Reconnect clears evidence results/selectors without replay.

Enter **Question or entity** and choose **Explore**. Blank queries are rejected,
not replaced with demo queries. **Query options** uses the discovered schema's
typed bounds/enums; untouched optional fields retain server defaults.
`InvalidParams` errors are sanitized without retiring healthy connections.
Sources with `query_mode` expose **Traverse / Ask / GQL** (Ask runs Knowledge Base retrieval, or NL→GQL when no Knowledge Base is published); older sources
offer Traverse only. GQL supports multiline input. Mode switches and
**Edit in GQL →** do not execute. The **Executed GQL** ribbon shows only actual
returned statements; the server owns translation/execution. Loaded ontology
chips are syntax helpers, not proof the graph shares that schema.

Without Knowledge graph, the first available tab opens. Cross-tab exploration
requires a discovered `entity_present`; unavailable targets fail visibly without
navigation. `hostContext.knowledgeWorkspace.knowledgeGraph` and `queryModes`
are app-owned navigation/editor flags, not MCP capabilities.

[Prerequisites and setup](standalone-setup.md) | [Launch](standalone-launch.md)
