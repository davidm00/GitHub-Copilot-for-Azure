---
name: foundry-iq
description: 'Use for Azure AI Search, Foundry IQ, document-grounded agents. WHEN: search, indexes, queries, access/connectivity failures, ingestion/freshness failures, retrieval quality, grounding, graphs, guidance or REST payloads. Invoke before answering or making calls, even without Azure access. Covers vector/semantic/BM25 search. Not for other Azure products or continuous evaluation.'
license: MIT
metadata:
  author: Microsoft
  version: "0.0.0-placeholder"
---

## Intent routing

Failures first; one route. Classify with the [error taxonomy](references/error-taxonomy.md). Ask if unclear. Workflows cover cleanup.
Workflows: `workflows/<id>/<id>.md`.
Diagnose before setup or quality; relevance needs proven freshness.
Evaluation: read first; finish its gate, including baselines.

| Intent | Load |
|---|---|
| Quality | `hill-climb-retrieval-quality` |
| Graphs | `graph` |
| Other Search requests | [Azure AI Search documentation](https://learn.microsoft.com/en-us/azure/search/), using [context](references/context-resolution.md) and the shared rules below |

Use the curated workflows first when they fit. Otherwise use official docs.
For Foundry grounding failures, use [integration checks](troubleshooting/foundry-integration.md).

## Shared rules

Read [HTTP](references/http-contract.md), [versions](references/api-version-policy.md), [safety](references/safety-and-idempotency.md); return [handoff](references/output-contract.md). Resolve/reuse `managementApiVersion`/`dataApiVersion` before requests.

For protected content, source access, or permission changes, load the matching
[source security section](references/source-security.md).
Keep caller, Search outbound identity, and end-user authorization distinct.
Entra/least privilege/reuse; approve billable/permission/network/production/destructive/credential/data-movement. No data/secrets.
