# Evaluate the existing agent, not a substitute

Use this branch of [Hill-Climb Retrieval Quality through Evaluation](../hill-climb-retrieval-quality.md)
only when the customer's existing system is Foundry Agent + Search/KB. A KB-only
customer does not need an artificial agent or external-agent registration.

## Resolve and freeze

Read the selected project's existing agent name, exact version, model, instructions,
tool/connection definitions and retrieval identity. Preserve them. Agent creation,
replacement or tool reconfiguration is a separate approved workflow. Pin the
deployment version; never infer `latest`. Resolve the approved cloud judge in the
agent's owning project. A central judge URL does not prove that project can use it.

Use [query-set admission](dataset.md). Queries and stable IDs suffice;
the target generates answers during evaluation. Ground truth is optional. A
registered query dataset must be read back and hash-verified before reuse. Inline
query rows also transfer private data and persist cloud records.

Read the installed `microsoft-foundry` evaluation procedure when available and
delegate the bounded batch only. Require its return to identify the pinned agent,
dataset, mappings, judge, every run ID and actual retrieval evidence. Do not enter
prompt optimization, deployment, telemetry or recurring-evaluation steps.

## Native cloud request

The request builder in [evaluation_contract.py](../scripts/evaluation_contract.py)
supports responses-protocol native agent targets. After preflight and consolidated
approval, use that helper with the existing approved project OpenAI client:

```python
request = build_request(
    reviewed_query_rows,
    judge=approved_judge,
    agent={"name": selected_agent_name, "version": selected_agent_version},
    dataset_id=verified_query_dataset_id,
)
evaluation = client.evals.create(
    name=approved_run_name,
    data_source_config=request["data_source_config"],
    testing_criteria=request["testing_criteria"],
)
run = client.evals.runs.create(
    eval_id=evaluation.id,
    data_source=request["data_source"],
)
```

`verified_query_dataset_id` is null for inline mode. The template sends only
`query` to inference, not labels or metadata. The source is
`azure_ai_target_completions` with an `azure_ai_agent` target, not separate local
Responses calls followed by judging. Hosted invocations-protocol agents require
their documented request-body template; do not substitute this responses template.

The captured-row CLI is deliberately not an agent-target runner. Use the selected
Foundry procedure or this request through approved SDK tooling with zero automatic
retries, bounded per-call/poll/page timeouts, and retained partial artifacts.

## Prove actual evidence

Run one development-row probe with the selected mappings before the remaining rows.
For this profile, response maps to `sample.output_text`; Groundedness/Retrieval
context maps to `sample.tool_calls`. Verify the pinned service supports that mapping
and every probe criterion actually received extracted passages, not just tool
arguments, citations or a synthesized tool answer. Generic structured output is
not automatically valid context. Failed mapping stops this branch without a second
retrieval to refill context. Record all probe costs and failures.

For every returned row require the selected agent/version, actual KB invocation,
successful tool/source activity and nonempty same-run final answer and passages.
Missing call evidence or a partial/error result blocks full RAG coverage even if
numeric scores exist. Preserve call IDs, evidence hashes and private artifacts.
Do not infer hidden backend success from one exposed successful call.

Paginate all outputs, reconcile original row IDs/full-row hashes with multiplicity,
and retain finite per-criterion scores and reasons. Bind readbacks to the submitted
evaluation definition, target and dataset. Capture eval/run IDs and the returned
report URL, not a constructed endpoint. Return cloud coverage and limitations
separately from quality and [comparison](comparison.md).

Source: [Foundry model and agent targets](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-targets).