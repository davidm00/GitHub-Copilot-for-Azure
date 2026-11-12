# Topic Graph build (preview)

First read [runtime setup](../graph-guide/references/install-and-checks.md#plugin-and-clis); use its `run <domain>` launcher.

Load one path only.

| Intent | Load |
|---|---|
| Check machine, inspect source index, plan, apply, or verify a build | [Plan and apply](references/plan-and-apply.md) |
| Publish a verified generation or manage reader access | [Publish and readers](references/publish-and-readers.md) |
| Recover a failed write or retire owned incomplete staging | [Reconcile and retire](references/reconcile-and-retire.md) |

## Shared rules

Run `topic-graph-build doctor --json` first and after any block. Pass `--json` and follow `next_step`; if Azure checks skip or block, use [prerequisites](../graph-guide/references/install-and-checks.md#missing-prerequisites). Name tenant, subscription, resource group, and Search service before sign-in. Entra only; no keys/tokens.

Every write gate (`plan`, `verify`, `plan-retire`) returns `approval_card`. Present only `approval_card.text` verbatim, then ask one Approve/Stop question; never ask the user to type an ID; never write or paraphrase your own approval text, never promise behavior the plan doesn't state, never create Azure/Search objects or role assignments outside the skill CLI (no raw `az`/REST workarounds), and stop and report the blocker when the CLI blocks. Always ask the user to explicitly choose the Foundry/OpenAI chat resource for topic labels; never infer a default. Run `apply`, `verify`, and `publish` in the main shell (`initial_wait: 600`), not a subagent. Never retry uncertain writes; reconcile first.

Topic Graph creates only `topicgraph-` indexes and never touches aliases. Its only source-index changes are the temporary ones on the approval card, reverted when the build finishes. Retain completed generations and their output folders. Not `globalRetrieve` or a Knowledge Source.
