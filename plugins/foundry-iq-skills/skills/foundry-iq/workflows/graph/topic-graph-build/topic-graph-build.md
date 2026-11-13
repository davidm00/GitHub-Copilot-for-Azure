# Topic Graph build (preview)

Use [runtime setup](../graph-guide/references/install-and-checks.md#plugin-and-clis)'s `run <domain>` launcher; load one path.

| Intent | Load |
|---|---|
| Inspect, plan, apply or verify a build | [Plan and apply](references/plan-and-apply.md) |
| Publish or manage reader access | [Publish and readers](references/publish-and-readers.md) |
| Activate native L1 topics/diversity, including existing builds | [Retrieval setup](references/retrieval-setup.md) |
| Recover writes or retire staging | [Reconcile and retire](references/reconcile-and-retire.md) |

## Shared rules

Named runs: [run naming](../graph-guide/references/run-naming.md). Reuse one absolute state directory.

Run `topic-graph-build doctor --json` first/after blocks. Use `--json` and `next_step`; skipped/blocked Azure checks need [prerequisites](../graph-guide/references/install-and-checks.md#missing-prerequisites). Name tenant, subscription, resource group and Search service before sign-in. Entra only; no keys/tokens.

Write gates return `approval_card`: present `approval_card.text` verbatim; ask one Approve/Stop question; never ask the user to type an ID; never write or paraphrase your own approval text; never promise behavior outside the plan. No Azure/Search/RBAC writes outside the CLI, no raw `az`/REST workarounds; stop and report the blocker. Ask the user to choose the Foundry/OpenAI chat resource for labels, never infer it. Run `apply`, `verify`, `publish`, `configure-retrieval` in the main shell (`initial_wait: 600`), not subagents. Reconcile uncertain writes before retry.

Build stays within its approved topic-index prefix and restores temporary source changes. Publish is local-only. Search/KB topic retrieval needs the separate activation gate after verification; browsing does not. Never touch aliases, create a KS or change KB membership. Retain completed generations/output folders. Not `globalRetrieve`.
