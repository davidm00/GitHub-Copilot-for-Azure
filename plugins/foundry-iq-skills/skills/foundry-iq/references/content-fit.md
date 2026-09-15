# Content-fit intake for ingestion

Read when File or Blob/ADLS content/answer needs are unknown or a mode conflicts
with the goal, even if a processing mode was explicitly named.
Honor explicit processing choices only when informed and compatible with the
confirmed outcome; reuse known content descriptions and answer needs without
asking again. Explain a known mismatch and clarify before planning: never
override the choice or silently reduce the requested outcome.
Unknown content requires assessment before a recommendation, even if the user
already confirmed a technical plan. Neither suffix/MIME nor inventory metadata
establishes suitability; service-detected file type remains admission authority.

## Explicit choice checks

| Request | Before planning |
|---|---|
| Use Minimal for these PDFs; I have not checked whether they contain searchable text or scans. | Assess unknown structure/answer needs through authorized samples or questions; naming Minimal does not bypass assessment. |
| Use Minimal, but answers must include scan-dependent figures. | Explain the mode/goal conflict and clarify a supported outcome; do not silently omit visual answers or override the mode. |
| I understand those visual answers are excluded; use Minimal for supported searchable text only. | Preserve this informed reduced outcome without repeating answered questions; retain the exclusion and service-admission checks. |

## Two routes, not a file-sharing requirement

Offer: "I can inspect a few representative samples you authorize, or you can
describe the content. Is it born-digital/searchable text, scans, or a mixture?
Are there images, charts, diagrams, complex tables or important page layout?
What answers do you need, and do they rely on that visual information rather
than the searchable text alone?"

- **Description:** a useful answer is sufficient; do not force files or repeat
  answered questions. If answers depend on figures or table relationships, ask
  only what remains unclear. A searchable PDF can still need visual extraction.
- **Samples:** agree exact local paths, file/page count, byte/output limits,
  inspection purpose and permitted content exposure first. Use only available,
  supported local read-only viewers/parsers within those limits; never install
  tooling, execute document scripts/macros, unpack archives or follow links.
  Choose tools for the host platform; PowerShell is not required. For a selected
  text sample, Windows/PowerShell can use
  `Get-Content -LiteralPath "<approved-file>" -TotalCount <approved-lines>`;
  Linux/macOS POSIX shells can use `head -n <approved-lines> < "<approved-file>"`.
  Substitute the approved path and positive line count, with host-appropriate
  quoting. Both examples require file bytes and output to fit the agreed limits
  before reading; line count alone is not a byte bound. If no safe supported
  viewer can inspect the needed structure, use the description route.
  For Blob/ADLS ask for customer-provided local representative copies; do not
  download blobs to decide. Never scan/download an entire container or widen
  the selected root/prefix. Metadata discovery is not content inspection consent.
  Never upload samples to CU, embeddings or chat-model services just to choose.
  Do not retain raw sample content in plans, logs or summaries.
- **Mixed content:** cover each relevant content family and answer-critical
  structure, not just the first/easiest text file. Ask how representative the
  samples are; describe uninspected portions and uncertainty. A small sample is
  not corpus-wide extraction proof.
- **Inspection unavailable, declined or unreadable:** ask the focused content
  questions instead. Never infer text-only from failure, refusal or no samples.
  If content/answer needs remain unknown, leave processing unresolved and pause
  source planning; no automatic Minimal or forced file sharing.

## Recommend, then approve

Recommend **Minimal** when supported searchable text supplies the needed answers,
including ordinary text tables whose relationships survive text extraction.
Explain that it avoids additional CU cost, dependencies and processing latency;
ordinary Search/ingestion and independently selected embeddings can still cost.

Recommend **Standard (Content Understanding)** when scans or answer-critical
visual/layout structure needs richer extraction, subject to supported formats
and the source-specific recipe. Explain billable CU, potentially higher
processing latency, required region/configuration/access, data movement and
retention. Standard is not universally better; tables/extensions alone do not
select it. No timing/quality guarantee. These helpers disable image verbalization:
do not promise chart/diagram interpretation the recipe cannot provide. Unsupported
answer needs require a capability handoff/blocker, not hidden model calls.

State the observed or customer-described basis, coverage/uncertainty, recommended
mode and tradeoff in user terms; retain that rationale with the workflow handoff,
not a fabricated helper evidence boolean. Ask only the unresolved mode decision.
Cost refusal, denied permissions or unavailable CU blocks that choice; explain
limitations and alternatives, but never silently downgrade. A customer may
explicitly choose a supported reduced outcome after learning its limitations.

Selection and sample consent are not ingestion/dependency consent. Return to the
source owner's concrete-plan approval and applicable CU/data-movement approvals
before writes; never auto-provision CU, change local auth, enable preview or widen
data boundaries. File standard uses its approved CU ENV-key path/August preview;
Blob CU uses existing keyless dependencies/GA or selected preview, ADLS preview.
Do not transplant recipes. Extraction is independent of lexical/vector indexing,
KB reasoning/synthesis and agent models; no model calls to make this decision.
