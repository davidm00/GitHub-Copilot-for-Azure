# Capture the existing workload

Read from [Hill-Climb Retrieval Quality through Evaluation](../hill-climb-retrieval-quality.md).
Preserve the evaluated system; do not add an answer model or rewrite its request
settings merely to fill evaluator fields.

| Existing target | Evaluation capture |
|---|---|
| Classic Search only | Actual result passages as context; Retrieval needs query/context, not an answer. Add ranking only with qrels. |
| Classic retrieval plus answering app | Final application response and the passages that actually reached its answer model, from the same invocation. |
| KB-only | Selected REST/SDK/native MCP output. For answer synthesis capture response and context; extractive-only uses context/ranking profiles. |
| Existing Foundry Agent + KB | Version-pinned native agent target during cloud evaluation; final response and actual same-run retrieval tool results. |

Follow the shared Search API policy. Missing support for a required version is a
blocker, not permission to change it. Read [Search](https://learn.microsoft.com/rest/api/searchservice/documents?view=rest-searchservice-2026-08-01-preview)
or [retrieve](https://learn.microsoft.com/rest/api/searchservice/knowledge-retrieval?view=rest-searchservice-2026-08-01-preview) before the
selected operation. Do not run all transports or substitute SDK submission for
proof of SDK-backed retrieval.

## Identity and evidence

Keep service authentication separate from evaluated-user identity. Permission-
sensitive retrieval needs the supported runtime end-user flow, including raw
`x-ms-query-source-authorization` where applicable, plus verified source permissions.
Never save tokens in files or widen roles to make a row succeed. Unsupported flows
block that identity slice. A managed agent's principal is not arbitrary user identity.

Enable required references/source data only through the approved request. Select
actual configured content fields, not an assumed `snippet`. The deterministic
`capture_kb_row` adapter in [evaluation_contract.py](../scripts/evaluation_contract.py)
preserves input metadata and rejects missing configured evidence and activity errors.
It applies to KB REST/SDK envelopes, not to classic or MCP response shapes.

For an application, capture context actually used for synthesis, not a second
retrieval. For MCP, discover the advertised schema and preserve tool call/result
IDs. Query arguments, citations alone and synthesized tool answers do not prove
extracted passages. Map native `sample.tool_calls` only after the one-row probe
proves actual context. If a service does not expose enough same-run evidence, stop
context-dependent scoring and name that limitation; never invent or refill it.

Ranked documents need source-qualified, collision-resistant IDs matching qrels.
Never use citation IDs or basenames. Deduplicate chunks by canonical document and
the declared score rule; preserve order where the surface is order-based. Do not
invent reranker scores. Record filters, output mode, source selection, extraction,
reasoning effort and application synthesis settings with the run.

## Measure efficiency and failures

Record per-row monotonic elapsed target time, retries, status and request/tool IDs.
Measure p50/p95 on the same request population; report failure counts separately.
Cloud evaluation wall time includes queuing/judging and is not retrieval latency.

Capture actual planning/synthesis/agent/judge usage separately when exposed. Bind
prices to verified model/version, deployment, SKU, region, currency, date and source.
Do not apply one model's price to another stage. Source-document counts and visible
text token estimates are not billable Search or hidden MCP usage. Unattributable
Search, agent or judge cost remains null with a reason; an unknown total is not a
proven budget. Include paid probes and failed attempts, not only successful rows.

Retain failed captures in the run ledger. Do not feed empty values to the judge,
drop failed queries from the denominator or overwrite successful prior evidence.
Batch approval includes data movement and spend even when Search configuration
is unchanged.

Source: [Retrieve and query-time permissions](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve).