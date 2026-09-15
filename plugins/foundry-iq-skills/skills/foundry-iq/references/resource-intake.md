# Select resources from names, URLs or observed choices

Use for unresolved resource selection or friendly-name/URL input. Do not make
users recall ARM IDs or configuration that Azure can supply. This is conversational
intake; helpers still receive their documented, resolved JSON inputs.
Execute only the applicable branch, not every discovery command on this page.

Reuse prompt/session choices. Otherwise use `az account show` and assume its
default subscription, stating that assumption; an explicit subscription wins.
Pass `--subscription <sub>` on reads; never silently change CLI context.
Account context and candidate listings are not access/readiness proof.

Exact supplied IDs need exact readback, not enumeration. Otherwise browse only
the relevant resource type: use the selected group when known, the selected
subscription when not. Read all pages within that query, never fan out across
subscriptions or enumerate unrelated resource types. Useful choices are worth
the discovery cost; do not replace discovery with a questionnaire about IDs.

## Search reuse

For a supplied name, resolve it with:

`az resource list --name <name> --resource-type Microsoft.Search/searchServices
--subscription <sub>`.

For an endpoint, extract the service name from its expected Search hostname
locally; do not fetch arbitrary URLs. Honor a supplied group by narrowing the lookup.
For unresolved reuse, a known group uses:

`az search service list --resource-group <group> --subscription <sub>`.

Without a selected group, browse Search services directly:

`az resource list --resource-type Microsoft.Search/searchServices --subscription <sub>`.

Show observed name, group and region; offer a recommendation, create new, and
freeform name/endpoint/ID entry. Bind the selected row to its returned ARM ID.
Do not ask the user to copy that ID. Freshly read the selected service's
endpoint/SKU/identity/network before declaring compatibility or readiness.
New intent uses the owner's concrete defaults, not a mandatory form for every setting.
Denied/no-match lookup needs a corrected name/scope or owner help; never infer
subscription-wide absence from a narrower query or broaden a denied lookup.

## Blob or ADLS container/folder URL

Accept `https://example.blob.core.windows.net/documents` as intake:
account `example`, container `documents`. A URL does not identify its Azure
subscription or resource group; the CLI default is only the initial lookup scope.
Also accept separately supplied names/IDs; do not ask again for URL-derived fields.

Also accept `https://example.dfs.core.windows.net/documents/onboarding`:
account `example`, filesystem/container `documents`, directory `onboarding`.
Keep the observed endpoint type (Blob or DFS); do not infer HNS from the hostname.

Parse locally: HTTPS, exact `<account>.blob.core.windows.net` or
`<account>.dfs.core.windows.net` host and an explicit container/filesystem path.
Reject user-info, query/SAS, fragments, custom hosts/ports and
malformed encoding without echoing the input; request a clean locator.
Decode path segments once, preserve case, and reject ambiguous encoded separators,
dot segments and control characters. Never use credentials from a pasted URL or
fetch its content during intake. Do not guess a folder from an individual blob URL.

Resolve the account by exact name/type in the selected subscription:

`az resource list --name <account> --resource-type Microsoft.Storage/storageAccounts
--subscription <sub>`.

Add `--resource-group <group>` when known. Read the returned exact ARM resource
and verify its account name, corresponding Blob/DFS endpoint and HNS setting.
DFS/ADLS intent requires verified HNS; resolve mismatches rather than silently
converting to Blob. A Blob hostname on an HNS account still uses ADLS rules.
Obtain the Storage
ID/group from that readback; do not invent them from the URL.
If inaccessible or absent from the selected scope, ask for the correct scope/ID;
do not scan every subscription, provision Storage or request broader access automatically.

Keep the supplied container; no container enumeration is needed. If it is unknown,
the Blob owner offers observed containers in the selected account using Entra login.
If the account is also unknown, offer Storage-account choices with
`az storage account list --subscription <sub>`, adding the known group filter.
Choose a returned account before enumerating its containers.

A container locator does not silently select every object. Preserve an explicit
folder choice, or resolve whole-container versus folder scope before inventory.
Ambiguous folder/blob paths need clarification, never automatic slash-appending
or parent-container expansion. Carry endpoint type and verified HNS to the owner:
Blob non-root prefixes end in `/`; ADLS directories do not. Never append `/`
merely to turn a file or arbitrary partial prefix into a folder.
No object inventory/download occurs before the data boundary is selected.

## Existing model choices

Only requested model-dependent paths discover accounts/deployments.
Known account/deployment IDs use exact readback. Otherwise offer relevant observed
accounts in the selected group, or selected subscription if no group is known:
`az cognitiveservices account list --subscription <sub>`.
Add `--resource-group <group>` when supplied; do not force users to remember it.

After account selection, list only that account's deployments:

`az cognitiveservices account deployment list --name <account>
--resource-group <group> --subscription <sub>`.

Show deployment name separately from model name/version and the account/region.
Filter recommendations to the requested embedding/chat capability; permit freeform
input and validate it. Do not enumerate deployments in every account, call models
to test selection, or change deployments. CU configuration/access still needs its
own verification; a listed account is not a ready CU dependency.
Lexical/minimal paths without models skip these calls.

New deployments additionally use `az cognitiveservices model list` and
`az cognitiveservices usage list` with `--location <region> --subscription <sub>`
to resolve model/version/SKU/quota units before approval. Existing deployments
need readback, not catalogs. Metadata proves neither capacity nor price/residency
suitability; the native owner retains those checks and executes approved changes.

Return resolved selections to the owner without restarting intake. Selection is
not mutation approval. Preserve explicit data boundaries, fresh pre-write checks,
complete selected-boundary inventories, and ownership/readiness verification.

## References

Authorities: failure/conflict/uncertainty only.

[Filtered ARM resources](https://learn.microsoft.com/rest/api/resources/resources/list).
[Blob resource URIs](https://learn.microsoft.com/rest/api/storageservices/naming-and-referencing-containers--blobs--and-metadata).
[ADLS filesystem/path](https://learn.microsoft.com/rest/api/storageservices/datalakestoragegen2/path/get-properties).
