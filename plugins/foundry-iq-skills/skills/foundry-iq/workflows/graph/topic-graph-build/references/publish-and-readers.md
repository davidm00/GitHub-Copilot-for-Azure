# Publish and readers

## Quick starts

- "Publish the verified Topic Graph generation."
- "Which readers will lose access if I publish this generation?"
- "Add this principal as a reader on the next build and re-plan."

## Use this path

Use this path after `topic-graph-build verify` passed and the operator wants the generation to become the current build.

## Publish

1. Confirm `verify` succeeded for the exact generation ID. If it did not, return to the plan-and-apply path.
2. Show the approval card that `verify` returned verbatim and ask its own Approve/Stop question.
3. Run `topic-graph-build publish --generation-id <id> --approve-publish --json` (including the global `--state-dir ...` flags before `publish`). This atomically selects the verified physical descriptor for new readers on this machine. It never calls Search alias APIs or changes existing consumers. Each source has its own current record, so publishing another source never makes this approval stale; only a newer publish of the same source does (`PUBLICATION_CHANGED`).
4. Run the publish result's `browse.command` verbatim to show the topics; it needs no other flags. Roll the explicit descriptor and matching reader access out to other machines and restart bound MCP consumers separately; existing sessions keep their startup binding.

## Reader access

Search roles scoped to one physical index do not follow local publication. Readers carry forward from the matching local current descriptor; pass `--previous-descriptor <path>` to carry them from another prior descriptor. `plan` lists direct grants under `reader_grants`, `apply` grants them on the new index before upload, and `publish` checks coverage.

- If `publish` stops with `READERS_MISSING`, say who would lose access. Do not drop readers on your own; re-run `apply` with the same plan, or re-plan with `--drop-reader <principal-object-id>` only when the operator asks.
- Use `--reader <principal-object-id>` only for a principal the operator names.
- `READER_GRANTS_FORBIDDEN` means the build identity cannot read or write role assignments on the Search service; report it and stop.
- Grants inherited from the service or resource group are not copied.

## Return

Report whether local publication ran, the physical descriptor, reader gaps and remaining consumer rollout. Never retry an uncertain publication; reconcile first. After a successful local publication, offer the [Graph Playground](../../graph-guide/references/install-and-checks.md#graph-playground) once.
