# Install and checks

Use the shared [runtime setup](../../graph-guide/references/install-and-checks.md).

## Act 1 commands

Run these yourself, in the main conversation, in order, and say what each does first.
`<package-root>` is the plugin folder holding `graph` and `skills`, five folders above this
skill's folder. Resolve it once from the loaded skill's path and reuse it; never search the
disk or list plugins for it.

```text
python -I "<package-root>\graph\runtime\preflight.py"
az account show --query "{subscription:name, id:id, tenant:tenantId, tenantName:tenantDisplayName, user:user.name}" -o json
python -I "<package-root>\graph\runtime\bootstrap.py" run entity entity-graph-provision discover --tenant-id <tenant> --subscription-id <id> --json
```

Never hand these to subagents, read or import runtime source such as `bootstrap.py`, or write
your own probe scripts. If one fails, show its error and next step; for sign-in or access, run
`bootstrap.py run entity entity-graph-provision doctor`, which checks the current Azure CLI tenant.

## Preflight

Before provisioning or any Entity Graph write, run preflight directly for the user with
an existing Python 3.12, 3.13 or 3.14. It is the expected first step; run it without asking.
It is not read-only: it may prepare the plugin's runtimes in the plugin cache.
It auto-prepares absent `entity`, `topicgraph` and `ontology` runtimes and validates wheels,
locks, dependencies and route CLI entrypoints through `bootstrap.py run ... --help`.
Apps are optional and are not launched. Grounding, when chosen at intake, is set up in Act 2;
its runtime is prepared on first use and checked by its own doctor ([grounding](grounding.md)).
It never runs doctor, signs in, calls Azure/models,
repairs corrupt caches, downloads Python/native binaries, executes native code or changes global configuration.
Local setup can download pinned dependencies from configured package sources.
It checks Topic Graph's native binary against its download receipt or checksum file.

If blocked, show the structured runtime/native results and next steps. Run
`bootstrap.py setup <domain>` directly when needed; never overwrite incomplete/corrupt caches.
Bootstrap run/status auto-discover local Python 3.12, 3.13 or 3.14 and auto-prepare an absent isolated
cache on first launch or wheel update. Warm calls retain the exact binding.
Re-run preflight after setup or any wheel, dependency, interpreter or binary change.

`topicGraphBuildTool` is not bundled inside the Python wheel; it is published on GitHub at
`Azure/foundry-iq-tool-releases`; the plugin uses it on Windows and Linux (`x64`/`arm64`). It isn't available on macOS. Preflight checks
the per-user runtime cache receipt (or an explicit `--native-binary` override) without downloading
or executing native code:

```text
python -I "<package-root>\graph\runtime\preflight.py" --native-binary "<absolute-binary-path>"
```

When no cached binary is present yet, `topic-graph-build plan` (or `download-native`) inspects the
latest `Azure/foundry-iq-tool-releases` release at plan time and adds an explicit download step
to the runtime approval card before downloading.

## Results and source gate

Exit `1` / `blocked` stops the demo. Exit `0` with `status: conditional` is not native readiness:
local checks passed, but the actual source has not been inspected yet, or the Topic Graph
executable is not cached yet (`native.status: download_pending`). That is normal on a first run:
say it will be downloaded at the Topic Graph plan step, behind its own approval; it is not a blocker.
Search creates Entity Graph's schema; managed `uid` can be nonfilterable. Explain this before ingestion.
Topic Graph reads the original index directly, in place: it needs a retrievable string key and stored, retrievable float32
vectors with an HNSW cosine or dotProduct profile (`scalarQuantization`/`binaryQuantization`
compression is fine). The executable's own preflight
checks that it can read the source. Route agreement never authorizes any leaf write.

As soon as the physical index exists, delegate actual schema inspection to `topic-graph-build`
before advancing the demo. Inspection does not pause or cancel managed ingestion already
running; do not silently change its schedule or freeze evidence. Topic Graph planning requires the
completed, frozen source. For an explicitly selected existing source,
inspect before any new Entity Graph work. This helper optionally performs the same read-only adapter
inspection, bypassing CLI state-directory creation:

```text
python -I "<package-root>\graph\runtime\preflight.py" --native-binary "<absolute-binary-path>" --inspect-source <Topic Graph-source-flag/value-pairs>
```

Select the original Entity Graph content index from its descriptor; retain its authority/provenance.
Use all explicit tenant, subscription, resource-group, search-service, source-index,
key/text/source/vector-field, embedding-model-id, and dataset flags from the leaf skill. No state, verbs, naming or write flags.
All source flags go after `--inspect-source`.
Name the tenant before this explicit live/authentication opt-in; never print identifiers/tokens.

Inspection needs stored, retrievable float32 vectors with an HNSW cosine or dotProduct profile;
unsupported or malformed sources block before any write.

`ready` requires local checks, a verified cached executable and verified source inspection.
Preflight never exports documents, creates or uploads an index, or runs native/model code.
Re-inspect at handoff; readiness is neither model/build readiness nor write approval.
Never mutate the original, bypass native verification, fake metadata or rewrite old plans.

## Subscription and models

Each leaf picks models only through `entity-graph-provision discover`. Don't list
subscriptions by default: intake item 2 offers the signed-in one by name. Only if the user
wants another, run `discover --tenant-id <tenant> --json` (every subscription they can see;
it can be long), ask for one by name, and show that list only if they ask.
`discover --subscription-id <id>` lists only usable chat and embedding deployments, by model
and region, with the ones the user holds a role on first; add `--all` only if they ask for
every resource. Show it as is and ask for the models by name. Map each choice to its `rows`
entry and pass the flags `discover --subscription-id <sub> --row <N> --discovery-id <id> --role <role>`
prints; never show row numbers. Never pick or guess for the user. If none fit, or the user
asks, create new ones: pass `--embedding-model <name> --chat-model <name>` to the resources
plan (the region's default version is used). Never run `az account set`; pass the subscription.

## Resources card

Plan with [new resources](../../entity-graph-provision/references/new-public-test-setup.md).
Search goes in a region where the graph features are available; ask the user if unsure, and never pick one
yourself. Pass the region the user names as `--search-location`; without it, Search,
storage and models all use `--location` (default `westus3`). The plan checks the region,
quota, roles and what already exists, so look nothing up yourself: no `az role assignment
list`, `rbac-check`, other `az rest` calls or help text. Plan, apply and connect print a
short summary; don't add `--json` or parse their output with scripts. Use only Search
services this demo created or the user names; never list or suggest anyone else's.

Show every runtime approval card verbatim, then ask one Approve/Stop question unless Approve
all covers it ([intake](intake.md#then-show-the-plan-and-ask-once)); never write
your own approval text or ask the user to type an ID. If the question is cancelled, show the
card again. After approval, run the plan's `apply_command` in this conversation with
`initial_wait: 600` and wait for it. Apply also runs connect and prints the build flags.
No time estimates; status: [apply status](../../entity-graph-provision/references/apply-status.md).
