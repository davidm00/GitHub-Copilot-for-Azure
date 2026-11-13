# Native retrieval setup

Use when adding topics for L1 Search/KB retrieval or enabling the Why Graph
diversity selector. A built/published explorer is not proof of native configuration.
Browsing alone needs no service-wide change. This is a required creation stage
for graph demos and Search/KB use, not a troubleshooting-only offer. Reuse an
existing verified generation; do not rebuild merely to activate it.

## Plan, approve, configure

1. Keep the original absolute `--state-dir`. If no verified generation exists,
   finish [plan and apply](plan-and-apply.md), then return here. Name the tenant,
   subscription, resource group and Search service before sign-in. Use the runtime
   launcher from [setup](../../graph-guide/references/install-and-checks.md#plugin-and-clis).
   Global scope flags precede the verb; omitted scope is recovered from the saved plan.
2. Select the verified generation and, for KB retrieval, the existing KS and KB
   that use its exact content index. Recommend stored default **off** to preserve
   relevance-only defaults while enabling explicit On/Off requests; **on** sets
   `balanced`. This affects every caller using the field/KS, not just this UI.
   For deferred ontology, wait until attach creates the KB; take both names from
   the final attached descriptor. Never reuse names from before a reingestion.
   Plan read-only:

   ```bash
   topic-graph-build --state-dir <absolute-state> --json plan-retrieval --generation-id <generation> --topic-diversity off --knowledge-source <existing-ks> --knowledge-base <existing-kb>
   ```

   Omit KS/KB only for Search-only setup. `plan-retrieval` reads back the exact
   generation inventory, source definition, KS target and KB membership. It uses
   `2026-11-01-preview`, native `vectorSearch.topicGraphProfiles` and
   `fields[].topicGraphProfile`, without changing the existing HNSW
   `vectorSearchProfile`. The profile's `indexName` is the verified topic index,
   with `defaultKind: none|balanced`; balanced uses pool size 1000.
   Selected searchIndex/azureBlob KS defaults are aligned via
   their parameter object's `topicGraph`. No persistent KB topic binding exists:
   its existing source reference is verified, not rewritten.
   Current mapped schema, vector dimensions, document count and embedding binding
   must still match the generation; no new-index capacity is needed for activation.
   This does not prove content freshness when documents change without a count change.
   Search redacts Blob connections even for managed identity. Preserve the exact
   returned `<redacted>` placeholder in the same-source update; the service keeps
   the stored connection. This is not evidence of its authentication type.
   The enrichment-cache connection is write-only and may be absent from GET.
   For an existing cache, the runtime sends `<unchanged>` to retain that same
   stored connection and preserves its identity; it never creates a cache.
   Never reconstruct credentials, change identities or read Blob data for this
   topic-only update. Visible connections must already use `ResourceId=`.
3. Show `approval_card.text` verbatim and ask one Approve/Stop question. Never
   substitute build or local publish approval. After explicit approval, run
   directly in the main shell (`initial_wait: 600`):

   ```bash
   topic-graph-build --state-dir <absolute-state> --json configure-retrieval --plan-id <approved-plan> --confirm-writes
   topic-graph-build --state-dir <absolute-state> --json verify-retrieval --plan-id <approved-plan>
   ```

   The updater checks all resources before writing, preserves unrelated raw
   November definitions, requires ETags/If-Match, journals each operation and
   reads it back. It never creates a missing index/KS/KB, changes access, uploads
   documents, calls models or changes the local published descriptor.
   Reapplying an already verified exact plan is a no-op. A single-field existing
   profile can be explicitly retargeted; the card names its old target and
   the plan retains prior topic settings. Old topic generations are not deleted.

## Verify actual queries

Configuration readback is not proof of query behavior. Report `live_queries:
not_run` honestly. After query/embedding/model usage is approved, test the same
question with **Use defaults**, **On (balanced)** and **Off** in Why Graph.
Check both KB and passage arms; explicit errors must not retry with defaults.
Alternatively use `entity-graph-consume query --query <question>
--topic-diversity default|on|off`, adding `--graph --query-mode kb` for the KB arm.
Both explicit On and Off need the native binding. Default omits the override;
it inherits stored KS/profile defaults, not necessarily Off. Raw GQL, traversal
and lexical-only retrieval do not accept explicit overrides. This full matrix is a
release or validation check; a live demo compares only On and Off on one question.

## Failure and return

Occupied/shared profiles, wrong KS targets, changed KB membership, missing ETags,
missing/unsupported Blob connection representations, drift or denied access stop activation;
report the typed blocker. No hand-written REST/SDK workaround.

Source and KS updates are not transactional. After any uncertain/partial update,
stop; run read-only `verify-retrieval` with the same plan, not build `reconcile`.
It reports each resource as configured, unchanged or conflict and reconciles the
journal. Inspect before explicitly approving resume of unchanged resources.
Conflicts require a fresh `plan-retrieval` and approval. Never blindly retry,
auto-roll back or delete a retained generation. Keep the state directory and
saved plan (safe prior topic deltas and definition digests, not raw KS secrets).

Do not declare retrieval setup complete until readback reports `state:
configured` for every selected resource. A declined gate leaves browsing usable
but retrieval setup incomplete. After reingestion or generation replacement,
repeat this gate with the new verified source/topic generation and final KS/KB;
old bindings and publication are not proof for the replacement.

Return the plan/generation/topic index, chosen default, exact resource states,
whether live query tests ran and the next safe action. Local browsing publication
remains a separate [publish](publish-and-readers.md) approval.
