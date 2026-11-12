# Grounding provision

First read [runtime setup](../graph-guide/references/install-and-checks.md#plugin-and-clis); use its `run <domain>` launcher.

Load one path only.

| Intent | Load |
|---|---|
| Pick an existing Search service, or check roles and preview API readiness | [Connect and doctor](references/connect-and-doctor.md) |
| Create a resource group and Search service for grounding | [Create a service](references/create-service.md) |

## Shared rules

Run read-only `grounding-provision doctor` first. If it reports no endpoint, or skips or blocks a check, follow [prerequisites](../graph-guide/references/install-and-checks.md#missing-prerequisites) instead of its raw `next_step`. State the tenant and subscription before any Azure call; the CLI prints both to stderr, and `--tenant` aborts on mismatch. Entra auth only: never request, pass, or store keys.

Writes stay on the CLI. `grounding-provision create` is a dry run until the user approves its card (one Approve/Stop question; never ask them to type an ID); present only the runtime `approval` card verbatim (never write or paraphrase your own approval text, never promise behavior the plan doesn't state, never create Azure/Search objects or role assignments via raw `az`/REST, and stop and report the blocker when the CLI blocks); only then re-run it with `--plan-id`. Always ask the user to explicitly choose the service when connecting. Never delete anything. Report role gaps and who must grant them; do not work around them. When the service is ready, hand off to `grounding-build` with the saved endpoint.
