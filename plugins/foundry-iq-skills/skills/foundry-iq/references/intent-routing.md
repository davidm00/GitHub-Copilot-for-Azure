# Intent, handoffs and completion examples

Read for ambiguous or compound goals, or uncertainty about whether the requested
outcome is complete. These examples guide interpretation, not keyword-first matching.

## Intent and completion

Route by the user's end result, not the first connector/resource keyword.
Within Foundry IQ, "make these documents searchable" or "ask questions over these
documents" means a usable KB with validated retrieval. Default to Create KB,
not a source-only operation. Words such as files, Blob, index or embeddings
identify prerequisites; they do not downscope a broader goal.

Confirm the intended finish once in normal intake, in user terms: "I'll make
these documents searchable through a knowledge base and check retrieval against
them. Do you want that full outcome, or only the knowledge source?"
Do not re-ask an already explicit or confirmed goal. Use source-only only when
the user explicitly requests or confirms that narrower outcome; never infer it
from an intermediate step. Goal confirmation is not approval for Azure writes.

Retain the confirmed goal, selected data, explicit exclusions and remaining steps
across handoffs. A child's `completed` result is not overall completion.
For a KB goal, resume the KB owner after Search/model/source prerequisites with
returned IDs and fresh source/readiness evidence. Present and approve the concrete
KB plan, create/reuse and read back the KB, then run supported-question and
unrelated-question retrieval checks under the selected API/output mode.
Require source-backed results and original-source citations; source ingestion,
KB existence or HTTP success alone is not validated retrieval.

Finish only when every requested outcome is verified. Otherwise report completed
prerequisites, the blocker and remaining steps; never mark the whole goal complete
or silently downgrade it to KS-only. Resume after an approved prerequisite rather
than asking the user to restart. Never preapprove an unknown KB mutation.
Explicit source-only, infrastructure-only and read-only requests remain bounded;
never create an unrequested KB/agent. Explicit classic Search work still routes out.

## Scenario examples

Read the whole request; broader goals and explicit limits take precedence over a
mentioned child step.

| User request | Start | Required finish |
|---|---|---|
| Make these local documents searchable. | [Create KB](../knowledge-bases/create.md) | Confirm KB outcome; File prerequisite, valid KB and validated retrieval. |
| Make this Blob container searchable. | [Create KB](../knowledge-bases/create.md) | Confirm KB outcome; Blob prerequisite, valid KB and validated retrieval. |
| Create a Blob knowledge source, then a knowledge base and test it. | [Create KB](../knowledge-bases/create.md) | Both resources and validated retrieval; do not stop at the KS. |
| Use my existing Search service to make these files searchable. | [Create KB](../knowledge-bases/create.md) | Reuse Search; finish the KB and retrieval, not just infrastructure. |
| Create only a Blob knowledge source; no KB. | [Blob family](../knowledge-sources/create-azure-blob.md) | Verified source only; no KB or agent creation. |
| Set up only a Search service. | [Search](../search-services/create.md) | Verified service only; no source or KB creation. |
| Query this existing KB. | [Retrieve](../knowledge-bases/retrieve.md) | Read-only source-backed retrieval; no creation. |
| Connect this KB to my existing Foundry agent. | [Connect](../agents/connect.md) | Verified requested connection and agent retrieval; configuration alone is insufficient. |
| Make OneLake and Blob searchable together. | [Diagnose](../troubleshooting/diagnose.md) | Explain unsupported scope; never substitute a Blob-only success. |
| Build a classic Search index and query it from my app. | Outside this skill | Classic Search handoff; do not invent a KB requirement. |
