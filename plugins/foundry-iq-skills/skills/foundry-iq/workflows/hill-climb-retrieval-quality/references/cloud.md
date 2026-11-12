# Run Foundry Cloud Evaluators

Use [Hill-Climb Retrieval Quality through Evaluation](../hill-climb-retrieval-quality.md)
after [query admission](dataset.md) and [capture](capture.md).
Local `azure-ai-evaluation` runners are not a supported path or fallback.

## Select only justified metrics

| Profile | Required data | Cloud evaluators |
|---|---|---|
| `answer` (default) | query, response, context | Groundedness, Relevance, Retrieval; no ground truth |
| `context` | query, context | Retrieval for classic/extractive search without an answer |
| `reference` | answer fields plus verified ground_truth/provenance | Answer profile plus Response Completeness |
| `ranking` | query, canonical qrels and retrieved documents | Document Retrieval; deterministic, server-side |

All rows have stable IDs. Missing gold must never block the default answer profile.
Ranking and reference scores supplement, not replace, the reference-free signals.
Record evaluator scales, rubric/version and threshold sources. A built-in pass flag
is not the customer's acceptance policy or proof that incomplete answers are complete.

## Preflight and composition

Resolve the existing project, supported evaluator/catalog versions, approved judge
deployment and actual model/version. Check Entra access, region, network and data
boundaries. An arbitrary AOAI URL is not a cloud judge binding; admin-connected
judges require a supported project connection. Missing binding blocks scoring.
Project/model/RBAC/network setup is separately approved, not an evaluator fallback.

When installed, read `microsoft-foundry` and the selected evaluation procedure.
Delegate an exact project/target/version, dataset digest, evaluator mappings, judge,
budget, deadline and allowed assets. Return for independent row/run verification.
Do not invoke its optimize/deploy/monitor steps or assume a sibling filesystem path.
Otherwise use supported Foundry SDK/REST. `foundry-iq-cli` is not required.
For an existing Foundry Agent + KB, read [native agent evaluation](native-agent.md)
instead of passing query-only rows to the captured-row CLI.

## Captured-row execution

The [runner](../scripts/evaluate_cloud.py) defaults to a no-call dry-run. Install
`azure-ai-projects>=2.5,<3`, `azure-identity>=1.25.3,<2` and `openai>=3.3.1,<4`
in the approved workload environment; freeze resolved versions before approval.
Resolve `<workflow-root>` as `workflows\hill-climb-retrieval-quality` beneath the
installed skill using [script path resolution](../../../references/context-resolution.md#script-paths),
not this repository or the current directory:

```powershell
python "<workflow-root>\scripts\evaluate_cloud.py" --rows captured.jsonl --project-endpoint <project-endpoint> --judge <deployment> --output <new-private-run-directory>
```

Review the exact request digest, data destination, all row/judge calls, retention
and spend. Only after approval, repeat with `--approve-plan <approved-digest>`.
The parent artifact directory must exist. The runner never overwrites a run or
uploads a dataset implicitly. Inline rows still transfer data and persist runs.

For reusable regression datasets, separately approve `project.datasets.upload_file`
with an unused name/version, read back that exact version and verify its content
digest. Reuse an existing verified version when requested. Pass `--dataset-id` only
after this check. A local path is not a registered ID. Never overwrite a version.

Run one development probe first, then remaining rows under the same frozen contract;
retain both run IDs and count every query once. No automatic resubmission. Timeout
retains the remote run ID, which may remain active; cancellation needs its own
approved action. Local readback or inspection is not a new target execution.

Cloud completion can precede publication of every output row. The runner retains
each output-page attempt and polls a short result set within the same approved
deadline. It never resubmits the run or repeats inference. Exhausted time, errored
counts, duplicate rows and malformed pages remain invalid; do not drop missing
rows or overwrite the original receipt during a later independent readback.

The runner verifies returned schema/evaluator mappings, judge binding and run source
against the approved request, reconciles rows and composite metric keys, and retains
losing results. It surfaces exposed judge usage; target measurements and complete
cost remain explicitly unknown unless separate capture evidence supplies them.
For a catalog variant, freeze explicit metric names with `--metric-contract` before
the probe. Never relax the contract after seeing results. Use
[comparison and handoff](comparison.md) for acceptance, not exit code alone.

## Failed cloud probe or run

Retain the request digest, returned eval/run IDs, service error/correlation ID,
row counts and any partial outputs. A failed probe or missing usable cloud rows
blocks the evaluated baseline and candidate acceptance. Inspect the selected
evaluator schema/mappings, project connection, actual judge deployment/version,
permissions and service-capacity error read-only. Return the specific owner
action or separately approved correction; do not invent a root cause.

Do not resubmit automatically, deploy a replacement judge, change the frozen
metric/profile or substitute local/custom scores to obtain a pass.

## Inspect saved results without inference

Use the standard-library-only [saved report helper](../scripts/summarize_evaluation.py)
to revalidate existing local artifacts and extract quality and judge usage:

```powershell
python "<workflow-root>\scripts\summarize_evaluation.py" --run-directory <saved-run-directory> --output <new-private-summary.json>
```

This command makes no network, retrieval or judging calls. It verifies plan/row/run
identity, definitions, scores and counts, including agreement with a valid original
receipt; preserves the original receipt verdict;
and writes a new file outside the immutable run directory. Raw reasons and evidence
remain private. For a registered dataset, also supply its original `--rows` file;
the helper verifies the frozen digest rather than downloading or resubmitting it.

For saved KB REST/SDK captures, optionally pass `--capture-ledger <capture.jsonl>`
and repeat `--context-field <actual-sourceData-field>` for the original mapping.
Each ledger entry has `id`, `elapsed_seconds` and the original retrieve `response`.
Require exactly one same-call response per evaluated row. The helper reconstructs
and checks the evaluated answer/context before reporting p50/p95 target latency,
exposed search counts and planning/synthesis tokens by stage/model. This adapter
does not support classic, MCP or native-agent telemetry shapes; retain those through
their owning capture procedure. Missing or partial telemetry stays unknown.

These measurements cover the selected run only. Attach the complete attempt ledger,
including other probes and failures. No component prices or full Search bill are
inferred, and total cost remains null. A saved report cannot prove that the live
target is still unchanged; the workflow's separate target-readback gate still applies.

## Helper ownership

These helpers implement the bounded captured-row SDK contract and are not a
dependency on a separate Foundry IQ CLI. Prefer
an available supported owning workflow when it preserves the approved plan,
data boundary, row identity, no-retry policy and retained results. Do not substitute
an unverified CLI operation or local evaluator. Maintainers must keep helper
contract tests and repository security scanning current; a future replacement
must preserve these controls before the helpers can be retired.

Sources: [cloud datasets](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets),
[RAG evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rag-evaluators).