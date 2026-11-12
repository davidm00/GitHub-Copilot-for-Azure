# Graphs

## Activation

Use when the user wants to build, query, explain or demo a graph over their
content: an Entity Knowledge Graph, a Topic Graph topic index, an ontology, or a
grounding index with graph-backed passages. Start with
[Graph choose](graph-choose/graph-choose.md); it picks one procedure below.
The starter prompt "Show me what Foundry IQ graph can do." and "Continue my
Foundry IQ demo" go straight to the guided [graph demo](graph-demo/graph-demo.md).

Do not use this workflow for:

- existing denied access, 401/403, DNS or timeout failures, missing files, stale
  answers or stalled ingestion: use
  [official Search documentation](https://learn.microsoft.com/en-us/azure/search/)
  with [shared context](../../references/context-resolution.md) first;
- retrieval-quality tuning of an existing index or knowledge base without a graph:
  load [hill-climb-retrieval-quality](../hill-climb-retrieval-quality/hill-climb-retrieval-quality.md);
- general Search setup, other Azure products, or continuous evaluation.

Resume graph work only after the existing failure is resolved.

## Procedures

| Need | Load |
|---|---|
| Choose a route, read-only checks | [graph-choose](graph-choose/graph-choose.md) |
| Explain techniques | [graph-guide](graph-guide/graph-guide.md) |
| Guided end-to-end demo | [graph-demo](graph-demo/graph-demo.md) |
| Entity Graph | [provision](entity-graph-provision/entity-graph-provision.md), [build](entity-graph-build/entity-graph-build.md), [consume](entity-graph-consume/entity-graph-consume.md) |
| Topic Graph | [build](topic-graph-build/topic-graph-build.md), [consume](topic-graph-consume/topic-graph-consume.md) |
| Ontology | [build](ontology-build/ontology-build.md), [consume](ontology-consume/ontology-consume.md) |
| Grounding | [provision](grounding-provision/grounding-provision.md), [build](grounding-build/grounding-build.md), [consume](grounding-consume/grounding-consume.md) |

## Required inputs

Ask only for what the chosen procedure needs next:

- what the user has (documents, an OWL file, a Search index with chunk vectors,
  or a Topic Graph build) and what answer they need (one passage, a multi-hop
  path, or corpus-wide themes);
- the tenant, subscription and target Search service, plus source storage and
  model deployments for build routes;
- which identity runs the work and which identities will read the results.

If a required input is missing, ask for it; do not guess resource names, tenants
or identities, and do not run sign-ins or installs on the user's behalf. Preflight and
bootstrap setup only prepare the plugin's own runtimes; they are not installs.

## Shared contracts

Use the shared [HTTP contract](../../references/http-contract.md),
[API version policy](../../references/api-version-policy.md),
[access safeguards](../../references/safety-and-idempotency.md#access-and-credentials),
[safety and idempotency](../../references/safety-and-idempotency.md),
[context resolution](../../references/context-resolution.md),
[source security](../../references/source-security.md) and
[output contract](../../references/output-contract.md).

## Approval and security

- Show the plan and wait for explicit approval before any billable, permission,
  network, production, destructive, credential or data-movement action. Route
  agreement is not write approval.
- Approve each runtime card with one Approve/Stop question. Pass the plan ID from
  the command output yourself; never ask the user to type an ID. If the question
  is cancelled or interrupted, show the card again.
- Before a provision procedure proposes a new Search service, read
  [service selection](../../references/service-provisioning.md). Run the
  [shared access check](../../references/safety-and-idempotency.md#access-and-credentials);
  ask before granting missing permissions or provide administrator instructions.
- Only call a runtime command or API that the procedure documents; do not imply
  an operation exists without a verified tool or API contract.
- Keep source authorization separate from Search access. Graph triples,
  summaries, topic indexes, caches and other derived artifacts do not inherit
  source permissions. Preserve provenance to source documents, and verify who
  can read the derived artifacts, how they refresh, and how revoked source access
  is removed.
- Remove only resources a graph procedure created, with that procedure's retire
  or cleanup commands, under the shared
  [scenario cleanup](../../references/safety-and-idempotency.md#scenario-cleanup) authorization.

## API version preflight

The graph runtimes pin their own versions. They do not read
`managementApiVersion`, `dataApiVersion` or task overrides; this is a known gap.
Report the pinned version a procedure used instead of the shared setting.

| Search data-plane pin | Used by |
|---|---|
| `2026-11-01-preview` | Entity, Topic Graph, Ontology and grounding graph and knowledge features |
| `2026-04-01` | Entity consume; Topic Graph build, live checks, consume and doctor |
| `2024-07-01` | Entity `ekg_core/doctor.py`, `ekg_provision/connect/spec.py`, and the default for Entity build and consume adapters |

ARM, Storage and Azure OpenAI calls also use fixed per-resource versions in each
runtime and are likewise not overridable.

## Completion

Done means the chosen procedure finished its own completion check: the plan was
approved, the run or query succeeded or failures were explicitly accepted, the
result's provenance and reader access were verified, and a handoff was returned
with the [output contract](../../references/output-contract.md), including the
pinned API versions used. If the work stops, return the resume point the
procedure recorded.
