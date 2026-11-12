# Entity Graph provision

Read [runtime setup](../graph-guide/references/install-and-checks.md#plugin-and-clis); use its launcher. Load one path only.

| Intent | Load |
|---|---|
| Readiness ("Am I ready?") | Only run `entity-graph-provision doctor`; report CLI, sign-in, tenant/sub, journal; no reference or questions. |
| Use existing Azure resources | [Connect existing](references/connect-existing-resources.md) |
| Create new Azure resources | [New public-test](references/new-public-test-setup.md) |
| Quota, TPM, RBAC, smoke, cleanup | [Capacity, RBAC, smoke](references/capacity-rbac-smoke.md) |

## Shared rules

Run that doctor first and after any block; follow `next_step`. Name tenant before sign-in; never run `az account tenant list` or `az account set`. Offer **Use existing** or **Create new** Azure resources; never ask for tenant, sub or RG in `az account show`.

Write gates (`plan`, `connect`, `plan-capacity`, `plan-rbac`) return `APPROVAL:`. Blockers: explain, offer a re-plan, no card. Otherwise show the runtime `approval_card` verbatim; never write or paraphrase your own approval text, never promise behavior the plan omits, create nothing outside the CLI (no raw `az`/REST), and stop and report the blocker. Show each `discover` tier verbatim; user picks a subscription (unless named), a named model per role (or new ones) and the cache account; never guess, narrow scope or reuse source as cache. Ask one Approve/Stop question; never ask the user to type an ID; re-show the card if cancelled. Run `apply`, `connect-apply`, `rbac-grant` or `capacity-update` with `--plan-id <id> --confirm-writes` here and wait. Never retry or clean up alone.

`gpt-5.6-luna` (extraction) and `text-embedding-3-small` are the defaults; `--chat-model latest` is the newest. Terra, Sol fine; keep embeddings unless named (fixed at ingestion). No made-up scores.

Only public-test, public-data and connect write. No secrets or build/query.
