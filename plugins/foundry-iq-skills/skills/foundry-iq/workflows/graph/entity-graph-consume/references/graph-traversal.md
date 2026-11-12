# Graph traversal

## Use this path

Use this path for relationship or multi-hop questions when the published descriptor advertises graph retrieval.

## Graph flow

1. Confirm graph retrieval with `entity-graph-consume capabilities --descriptor <path> --json` when not already known.
2. Run `entity-graph-consume query --graph --descriptor <path> --query "<question>" --json`.
3. Bounds: `--depth` 1-3 (default 2), `--top` 1-10 (default 5), `--fanout` 1-50 (default 20). Widen only when the previous result stayed within limits.
4. The default `--json` output is `detail: "summary"`: the relationships most related to
   the question (`summary.top_relationships`, each with its cited `sources` files), counts,
   executed GQL and a budget note. Answer from it. `--detail full` returns every node, edge
   and chunk-level passage; `--detail compact` deduplicates identical evidence records while
   retaining distinct chunks and each edge's `source_ids`/`evidence_ids` links.

## Query modes

`--graph --query-mode traverse` is the default multi-hop path. It anchors on the names in the
question and first tries the ontology classes the question names or implies (for example
people for "who" or "executives"), falling back to the other classes only when those find
nothing. Its result includes `query_mode: "traverse"` and an ordered `executed_gql` list of
the statements actually sent.

Use `--graph --query-mode gql --query "<MATCH ... RETURN ...>"` for a single read-only
statement. Writes, multiple statements, comments, semicolons, control characters and
multiline quoted literals are rejected. Ordinary newline, carriage-return and tab whitespace
outside literals is allowed. The query is limited to 2048 characters and results to 1000 rows;
use an explicit `ORDER BY` and `LIMIT` for predictable bounded results.

`--graph --query-mode nl2gql` (or `--query-mode kb`) routes natural-language questions through
the descriptor's server-side Knowledge Base (`endpoints.knowledge_base` via
`POST /knowledgebases/<kb>/retrieve` with `outputMode: "answerSynthesis"` and server-side
`graphParameters` provenance hydration). Azure AI Search plans GQL against the linked Knowledge
Source (`graph_search` tool) and returns graph rows, hydrated source chunks, activity steps,
and an answer the service synthesizes from those rows and chunks with `[ref_id:N]` citations.
The runtime does not rewrite that answer. When a step fails (for example a graph search timeout),
the service still returns what it has and the runtime reports the step's error in `warnings`.
For a single-document question, the answer is withheld (it can draw on other documents) and the
scoped graph rows and passages are returned. Both modes require `endpoints.knowledge_base` in the descriptor.

Raw/NL results include the exact `executed_gql` string, `gql_columns`, clean `gql_rows`,
`graph_diagnostics` and `graph_stats`, including scalar projections without graph endpoints.
Returned endpoint bindings with source provenance are mapped to graph facts and use the same
source hydration and stale-source handling as traversal. Missing endpoint/predicate bindings
are not invented. Undirected matches and multi-edge rows without attributable relationship IDs
stay tabular rather than acquiring invented directions or edge-specific citations. Multi-label
nodes retain their returned labels and use the matched type, or a stable returned label, for display.
Compact results preserve query and table metadata.

## Question sets

For several questions (for example, a dataset's sample questions file), answer each in turn and report every answer before ending the turn:

1. Run one `query --graph` per question, in sequence; give each call enough time (about two minutes) and never leave one running in the background unreported.
2. Use `traverse` for who-relates-to-whom questions and `kb` or `nl2gql` for counts and rankings. If one mode returns nothing relevant, try the other once and say which you used.
3. Give each answer with its citations, or say plainly that the graph has no relationship to answer it, naming what is missing.

## Premise checking and limits

- Retrieve the named entities and asserted facts, not only the requested impact. If evidence contradicts the premise, say so and cite the correcting source; if neither confirmed nor contradicted, say it is unverified.
- Graph retrieval never falls back silently to document retrieval. If it is not enabled, say so and stop.
- Traversal is bounded by request budget with no completeness or total-count guarantee. If anchors were skipped or a warning appears, split the question and query from the intermediate entity.
- Keep entity IDs, aliases, directed predicates, warnings, and source citations intact. Never invent a missing passage or link.

## Optional presentation

An Apps-capable host may run the optional `entity-apps` server, whose `entity_present` and `entity_present_evidence` tools show bounded graph results. The operator binds the descriptor at start. It is read-only and never replaces the CLI.
The graph/evidence views use app-only `entity_graph_query` for bounded supporting reads. Sessions
without Apps expose no tools or resources. Resource bytes must match the accepted packaged
provenance; missing or altered HTML blocks startup with a reinstall instruction.
All three tools advertise `query_mode` with the same choices; JSON `null` means `traverse`.

## Return

Report the path, the sources behind each returned edge, any traversal warning, and whether the answer is confirmed, contradicted, or unverified.
