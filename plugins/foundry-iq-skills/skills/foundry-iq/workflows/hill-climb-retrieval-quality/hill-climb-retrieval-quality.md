# Hill-Climb Retrieval Quality through Evaluation

Quality failures need evidence. Start
from the existing architecture; no KB prerequisite.
This workflow owns the complete loop: queries, baseline, diagnosis, approved change,
re-evaluation, retain/revert. Evaluation is a reusable stage, not improvement's endpoint.

## Scope and inputs

Approved setup: read [service selection](../../references/service-provisioning.md).
Run the [access safeguards](../../references/safety-and-idempotency.md#access-and-credentials);
ask before granting missing permissions or provide administrator instructions.
For protected or mixed-source evaluation, read the matching
[source security](../../references/source-security.md) sections. Preserve
per-user authorization through captured answers, citations and derived artifacts.

## API version preflight

Resolve classic Search/application, KB-only or Agent + KB, answer owner, interface,
sources and identity. Resolve `dataApiVersion` and needed `managementApiVersion`
under shared policy before requests. Reuse resources; ask for missing boundaries,
goals and approvals.
Do not require a prepared dataset or ground truth.

Fixed-batch improvement, not continuous
evaluation. No monitoring, live-trace harvesting, external-agent registration
or recurring rules. Inspect read-only; retrieval, generation and cloud
judging cost money and move private data.

## 1. Establish an evaluation set

Read [query-set admission](references/dataset.md).
Reuse suitable supplied questions. Otherwise review failing examples and approved
source excerpts/query exports; propose questions covering topics, formats, languages
and critical/identity slices. Review relevance/coverage, not invented answers.
Review synthetic questions; generation-only requests stop here.

Preserve stable IDs and provenance/metadata. Freeze the user's test set;
do not proactively split it or require a holdout. No ground truth is required for
Groundedness, Relevance and Retrieval: use actual target query/response/context.
With verified gold answers, strongly recommend Response Completeness as the primary
quality metric (`--profile reference`), keeping reference-free metrics as guardrails;
string matching is supplementary unless the user chooses otherwise.
Preserve `ground_truth` and its provenance in captured rows, including custom
adapters; if provenance is unclear, confirm it instead of silently ignoring gold.
Document Retrieval needs reviewed qrels. Never promote generated answers to gold.
Do not silently subsample an agreed comparison set to save money.

## 2. Record the existing baseline

Read [target capture](references/capture.md) and selected
[cloud evaluation](references/cloud.md) profile.
Freeze configurations, corpus, caller, query/split digests, judge/model/evaluator
versions and mappings. Agree primary metric/direction, user bounds, repetitions,
attempts and spend. No default percentage gain or all-metric improvement requirement;
disclose tradeoffs for user choice.
Approve data/project/assets/retention/calls; approve missing setup separately.
Without acceptance criteria, report a baseline, not
a quality pass or permission to retain a change. Unknown cost remains null, not zero.

Use [Search](https://learn.microsoft.com/rest/api/searchservice/documents?view=rest-searchservice-2026-08-01-preview)
(`Documents_SearchPost`) or [KB retrieve](https://learn.microsoft.com/rest/api/searchservice/knowledge-retrieval?view=rest-searchservice-2026-08-01-preview)
(`KnowledgeRetrieval_Retrieve`) through the existing application's actual path.
Use the pinned existing agent for native evaluation; no artificial KB-only agent.
Test the selected surface, not every transport. Preserve query-time ACL identity.

Probe one test row, then the remaining rows; count the probe once. Capture
answer/evidence from the same invocation; never retrieve again to fill context.
A search-only target uses Retrieval, plus Document Retrieval with qrels, without
inventing an answer. Answering systems use all three reference-free evaluators.
Use Foundry Cloud Evaluators only; never fall back to local evaluators.
If the cloud probe fails or returns no usable rows, stop optimization and follow
the cloud failure handoff. Component probes may diagnose the cause but cannot
replace the original target's evaluated baseline or authorize retaining a change.

### Complete each evaluation

Before returning or considering a candidate:
1. Reconcile every query, metric and failure; retain actual cloud run/report IDs.
2. Read back the target configuration against the frozen snapshot. Record unchanged,
  changed or unverified with evidence; read-only intent is not verification.
3. Report cloud execution, evidence integrity, target verification and workload
  quality separately. Cloud completion alone is not verified task completion.

Baseline-only requests stop only after these checks and the final report. Skip
optimization, never verification. Missing checks mean incomplete verification.

## 3. Identify likely failure modes

Inspect failing rows/citations for ingestion, extraction, retrieval, reasoning,
synthesis, freshness or authorization defects. Reference-free scores do not prove
completeness. Log hypotheses, affected slices, evidence and discriminators.
For an answering app/agent, distinguish missing retrieved context from failure
to invoke retrieval. Inspect actual same-run tool activity and source citations;
an independently successful KB query does not prove the agent used it. Any
retrieve-first instruction or tool-choice change is a separate approved candidate,
not a hidden addition to a search-fields experiment.

- Missing information in tables, figures, diagrams or other multimodal content:
  inspect extraction before blaming ranking. Compare basic extraction against
  Content Understanding Standard only when that evidence justifies it.
- Classic retrieval fails on decomposition, multiple searches, ambiguity or
  synthesis across evidence: consider a classic-versus-Knowledge-Base experiment.
- Classic search already meets the target with better latency and cost: retain it;
  do not introduce agentic retrieval merely because the skill supports it.

## 4. Change one meaningful variable

Read [candidate guidance](references/hill-climb-candidates.md) and
[comparison policy](references/comparison.md).
Choose quality or cost improvement within approved bounds; use failure evidence
for one reversible candidate. Re-measure stale or different-workload baselines.
Treat any proposed candidate as unretained until a re-evaluation against the frozen
baseline confirms it meets the predeclared policy, even when the request only asks
for the change itself.
Do not stop an improvement request after evaluation: complete candidate
re-evaluation and the retain/revert decision.

Log one variable, before/after, hypothesis, controls, actions, cost and rollback.
Read the operation; approve deployed/billable/data/ingestion changes. Preserve other
settings; query-time trials need data/spend approval.
Keep an append-only trial log, including failed and not-run candidates. Apply only the approved delta;
verify its definition/request and retrieval readiness before evaluation.

Approve architecture/extraction experiments separately. Use isolated candidate resources
with the same workload, corpus, judge and answer contract; declare implementation
differences as the treatment. Delegate setup to its owner.
Never rebuild shared production sources/indexes just for comparison.

## 5. Re-evaluate and retain or revert

Regenerate target outputs for every candidate on the same frozen test set;
never score baseline answers as new retrieval. Recheck controls and record drift.
Return to the verified baseline between independent candidates. Adopting a winner
requires a new baseline ID; record the transition before another hypothesis.
Compare paired rows and critical slices, quality, p50/p95 target latency, searches,
target/judge tokens and attributable cost with price source/date. Separate target
latency from cloud evaluation wall time. Include failed attempts and losing runs.
Report retrieved-context coverage and irrelevant/historical passages separately
from final answer quality. Include wrong-source citations, tool/429 failures and
missing outputs in the original workload denominator; assess error rates and
latency against the approved bounds before retaining an agent candidate.

Retain primary-goal improvement within user-approved tradeoffs; disclose decreases.
Preserve safety/integrity. Otherwise restore baseline and verify
rollback, or record blocked recovery. Holdout checks are user-requested only.
An invalid or incomplete candidate cloud run cannot establish improvement:
restore the approved baseline and verify recovery, or report blocked rollback.
Stop at the agreed
attempt/spend bound. Never claim statistical significance from a smoke sample.
Read back the retained configuration; verify its retrieval path. A test
or user instruction to stop after evaluation overrides steps 3-5 for that run only;
this workflow is not evaluation-only.

## Verify and return

At each step report candidate changes, baseline metrics, decision and retain/revert.
End with candidate and baseline-versus-final tables, including regressions/missing
values; attach questions, retained configuration, rollback proof, reports and limitations.
Verify comparability, security boundaries and the evaluation checks above.
Cleanup is separately approved: use [scenario cleanup](../../references/safety-and-idempotency.md#scenario-cleanup)
for run-owned assets; retain evidence/ownership.
Manual success is not proof of skill-value improvement.