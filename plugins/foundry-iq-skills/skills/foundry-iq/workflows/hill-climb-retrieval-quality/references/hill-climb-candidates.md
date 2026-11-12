# Choose a bounded improvement

Use after diagnosis in [Hill-Climb Retrieval Quality through Evaluation](../hill-climb-retrieval-quality.md).
Candidates are hypotheses, not recommended universal settings. Keep the judge,
query set, identities, output contract and all non-candidate settings fixed.

## Readiness before tuning

Read the [KB definition](https://learn.microsoft.com/rest/api/searchservice/knowledge-bases?view=rest-searchservice-2026-08-01-preview),
[source definition](https://learn.microsoft.com/rest/api/searchservice/knowledge-sources?view=rest-searchservice-2026-08-01-preview),
[index](https://learn.microsoft.com/rest/api/searchservice/indexes?view=rest-searchservice-2026-08-01-preview) and representative retrieval.
Verify source health, actual content/citation fields, effective search fields,
semantic configuration, and vector dimensions/profile/vectorizer when applicable.
Activity alone does not prove vector execution. Empty evidence, stale ingestion,
permission errors and partial sources need diagnosis, not an optimization sweep.

Resolve model deployment/version/SKU and access without creating a model or changing
roles. Use only parameters and bounds supported by the selected API and actual
target. Do not copy another API version's model list, limits or defaults. Missing
version support blocks that candidate rather than silently upgrading the service.
For example, reasoning effort `low`/`medium` requires api-version 2025-11-01-preview
or later; `auto` requires 2026-08-01-preview or later.

## Candidate choice from evidence

Prioritize one variable at a time by goal: for cost reduction, try a cheaper
supported target model or `auto` reasoning effort before instruction edits or
architecture changes; for quality with adequate content coverage, try a supported
model upgrade before retrieval or answer instructions.

| Observed problem or goal | One candidate to investigate | Keep separate |
|---|---|---|
| Useful evidence is filtered out | Per-source reranker threshold (`rerankerThreshold`): valid range 0-4; values above ~2.0 tend to remove too much relevant content; test the current effective value against 0 (no filtering) | Source routing, model, output budget |
| Expected source is skipped | That source's forced-query control, when supported | Other sources and thresholds |
| Useful evidence is truncated | Retrieved-evidence output budget (`maxOutputSize`): minimum 5000 tokens; never test below it; try 5000 -> 10000 -> 20000 tokens, stopping once quality plateaus | Model, ranking and reasoning |
| Reformulation or a second search could recover evidence | Supported reasoning effort | Output contract and synthesis settings |
| Reduce cost without a quality regression | `retrievalReasoningEffort.kind: auto`, a fourth value alongside `minimal`/`low`/`medium` from 2026-08-01-preview onward: initial minimal-tier probe, escalating to LLM reasoning only when confidence is low | Target model, Judge, data and quality floor |
| Evidence is good but synthesis is weak | Supported KB/application model choice | Judge deployment and evaluation rubric |
| Quality meets the goal but model cost is high | Cheaper supported target model | Judge, data and quality floor |
| A specific user-required citation/answer format is missed | Answer instructions | Retrieval logic and content coverage |
| A specific user-required domain or source-routing rule is missed | Retrieval instructions | Answer formatting |

Instruction edits are not a generic remedy for low scores. A post-reranking filter
can reduce context or synthesis work, but does not undo completed searches/reranking.
Smaller visible outputs do not prove lower hidden retrieval cost. Model or effort
changes require actual token/latency/quality measurements, not assumed savings.

For classic Search, inspect the existing query and index first; a supported
keyword/vector/hybrid or semantic-ranking change is a candidate only when its
required fields and configuration already exist or their setup is approved.
Architecture and extraction comparisons follow the workflow's evidence gates and use
isolated resources. Do not combine a KB migration and an extraction change in one
unattributed candidate.

## Execute and recover

Read the selected mutation operation, such as
[KB update](https://learn.microsoft.com/rest/api/searchservice/knowledge-bases?view=rest-searchservice-2026-08-01-preview), before
planning. Record its exact supported delta, prior definition/ETag, expected effect,
verification and rollback. Use the operation's concurrency contract; drift invalidates
approval. For request-only trials keep the server definition unchanged.

For a request-only candidate such as a per-source `rerankerThreshold` or
`alwaysQuerySource` override, there is no stored definition to read, PUT or
ETag-guard: fix the exact value in the request body for both baseline and
candidate runs, and rollback means reverting to the baseline's recorded value
on the next request, not a server-side restore.

For KB definition changes, read the KB definition first and capture it and its
ETag. Apply the approved delta via PUT with `If-Match: {ETag}` so concurrent
drift fails safely rather than being overwritten. Read back to confirm only the
intended field changed. To roll back, PUT the captured original definition with
the latest ETag as `If-Match`, then read back again to confirm the definition
matches the original.

After approval, apply only that delta and read it back. Probe readiness, evaluate
fresh outputs, compare with the frozen baseline, then retain or revert under the
predeclared policy. Verify rollback and retrieval before the next independent
candidate. Stop on exhausted budget, safety failure or unverified recovery.

Append each trial's baseline ID, candidate ID, variable, before/after, hypothesis,
approval, query/evaluator digests, run/report IDs, quality/latency/cost, slice
regressions, decision, retained state and rollback proof. Include failed, invalid,
inconclusive and not-run trials. An optimizer may enrich this guidance without
changing the workflow's measurement or approval contracts.

Sources: [retrieval reasoning](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort),
[retrieval API](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve).