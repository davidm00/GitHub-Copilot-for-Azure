# Capacity, RBAC, smoke

## Quick starts

- "Review TPM quota, RBAC, and the smoke plan for this environment."
- "Raise the chat deployment capacity."

## Use this path

Use this path for model quota and capacity, scoped role assignments, the synthetic smoke test, and cleanup evidence.

## Capacity

New deployments use the free quota up to 200K TPM for embeddings and 250K TPM for chat; with less free, the card says what it took (at least 50K).
Explicit role capacities override these defaults. Connect preserves observed
existing capacities and never automatically resizes a deployment. Even when
200K is desired, resizing an existing deployment needs its own exact approval.

1. `entity-graph-provision quota` (read-only) reads regional usage and the model catalog with the same deployment flags.
2. `entity-graph-provision plan-capacity --capacity-deployment <name> --capacity <K>` shows current and desired capacity (thousands of tokens per minute), quota headroom, and the plan ID. Only SKU capacity changes; PTU is out of scope.
3. After the user approves the card, run `entity-graph-provision capacity-update` with the same flags plus `--plan-id <id> --confirm-writes`. It refuses on drift or insufficient quota and verifies by fresh read. Above the quota limit, a quota request comes first.

## RBAC

1. `plan-rbac` and `rbac-check` are read-only and check the active tenant, subscription and object ID. A role you already hold directly, through a group (nested too) or at a parent scope is left off the card with an "Already held" note.
2. After approval, `entity-graph-provision rbac-grant` grants only the remaining exact scoped data roles; it rereads first and stops if what you hold changed.
3. Content Understanding (optional `--content-understanding-name`) lets Build read PDFs, Office files and images. `rbac-grant` does not cover it: the operator grants the Search identity Cognitive Services User on that account, which must be in a Content Understanding region (not centralus) with a deployment named like the Build's chat deployment. Text-only corpora never need it.
## Smoke test

`plan-smoke` then `smoke-run` tests one synthetic Blob, a Search index, a document push and query, and an optional embedding. It needs its own approval, verified ARM posture, a pre-existing container, and conditional cleanup. It does not prove an Entity Graph workflow.

## Cleanup

`plan-cleanup --run-id <id>` is offline and manual-only. `cleanup-approve --run-id <id> --plan-id <id>` records approval and never deletes Azure resources. Never enable trusted services or widen ingress to make indexers reach Storage or OpenAI.

## Return

Separate reviewed plans from applied changes, and give one safe next action.
