# Entity Graph build

Read [runtime setup](../graph-guide/references/install-and-checks.md#plugin-and-clis); use its launcher. Load one path only.

| Intent | Load |
|---|---|
| Plan, apply, reconcile or publish; choose ontology and bind the planned KB | [Plan and publish](references/plan-and-publish.md) |
| OWL trial, published update or retirement | [Trial, update, retire](references/trial-update-retire.md) |
| Status, progress, failed documents, telemetry or protected generations | [Status and telemetry](references/status-and-telemetry.md) |
| Attach an ontology to a build made without one (default) | [Deferred ontology](references/deferred-ontology.md) |

## Shared rules

Named runs: [run naming](../graph-guide/references/run-naming.md). Reuse the binding and journal; read planned names.

Run `entity-graph-build doctor --json` first and after any block; follow `next_step`. Name tenant before sign-in. Pass `--json` and absolute paths.

Write plans (`plan`, `plan-update`, `plan-retire`, `plan-attach-ontology`) return `APPROVAL:`. Show the runtime `approval_card` verbatim; never write or paraphrase your own approval text, never promise behavior the plan doesn't state, never create Azure objects or roles outside the CLI (no raw `az`/REST), and stop and report the blocker when it blocks. Then ask one Approve/Stop question; never ask the user to type an ID; re-show the card if cancelled. Run the write verb with `--plan-id <id> --confirm-writes` in the main shell (`initial_wait: 600`), not a subagent. Never retry uncertain writes; reconcile first. Publish only verified state.

Never invent inventory, grants or health. Keep secrets, tenant details and document text out of output.

Failed documents (`INGESTION_PARTIAL`, `ATTACH_PARTIAL`) pause the build. Run `failures`, then offer investigate or accept-and-continue ([Failed documents](references/status-and-telemetry.md#failed-documents)); never just stop.
