# HTTP contract

Use HTTPS, the exact `api-version` resolved for the request's plane by the [API version policy](api-version-policy.md), `Authorization: Bearer`, `Content-Type: application/json`, and a generated client request ID. Preserve service request IDs. Follow continuation URLs without reconstructing them. Honor `Retry-After`, bound retries to 408/429/5xx and idempotent operations, and never retry unsafe writes without an idempotency or state check.

Construct Search requests with resolved `managementApiVersion` or `dataApiVersion`,
never a copied default. A documentation URL's `view=...` selects a reference
contract, not the task's request version; adapt and verify the selected contract.

For Search data-plane `az rest`, explicitly pass `--resource https://search.azure.com`
so CLI acquires a Search-audience token rather than inferring an ARM audience.
Binary file uploads instead use `application/octet-stream` and the privately
acquired Search token; never serialize bytes through `az rest --body`.

## User-agent attribution

Add `foundry-iq-skill-v{skillVersion}` to `User-Agent` for skill-executed Search management and data-plane requests, including standalone operations, workflows, troubleshooting, retries, polling, and pagination. Resolve `skillVersion` from `metadata.version` in the [loaded skill](../SKILL.md), stamped by upstream packaging.

Preserve the client's identity and append the token once, scoped to these requests. Respect user or organization telemetry restrictions; never include private data or secrets.

| Interface | How to apply the token |
|---|---|
| Azure CLI `az rest` | Add `"User-Agent=$skillUserAgent"` to existing `--headers`; CLI retains its identity. Do not also set the token through `AZURE_HTTP_USER_AGENT`. |
| SDK | Use a supported application-ID or user-agent extension; retain `azsdk-*`. |
| Direct HTTP, including file upload | Append to the client's existing `User-Agent`; preserve other headers. |
| MCP or another managed client | Use a documented attribution option. If unavailable, report it; do not invent arguments or switch clients solely for telemetry. |

After resolving `$skillVersion` and `$dataApiVersion`:

On Windows PowerShell with `az.cmd`, replace `--url $url` with `--url ('"' + $url + '"')` and keep JSON in quoted `@file` arguments; see [Windows quoting](#windows-quoting).

```powershell
$skillUserAgent = "foundry-iq-skill-v$skillVersion"
$url = "https://<search-service>.search.windows.net/indexes?api-version=$dataApiVersion"
az rest --method get --url $url --resource https://search.azure.com --headers "User-Agent=$skillUserAgent"
```

Do not tag generated customer application code. Exclude the live-validation token `foundry-iq-skill-live-v1` from skill-usage counts, even when other inherited tags are present.

## Windows quoting

Use the installed `az rest` directly; no separate Python launcher is required.
On Windows, when `az` resolves to `az.cmd` or `az.bat`, ordinary PowerShell
quotes can be removed before `cmd.exe` sees the arguments. Preserve literal
double quotes around the validated URL with `--url ('"' + $url + '"')` so
`&` and OData parentheses remain data. Never include raw double quotes or line
breaks in a URL; encode dynamic values according to the URI/OData contract.
This is a recipe-specific convention, not general escaping for untrusted input.

Use Windows PowerShell 5.1's normal argument passing, or PowerShell 7's
`Windows`/`Legacy` mode; if PowerShell 7 was explicitly set to `Standard`,
restore `$PSNativeCommandArgumentPassing = 'Windows'` in the request invocation.
Do not add these literal quotes for native `az` executables or on Linux.
Do not add `--%` to variable-based examples: it stops `$dataApiVersion`,
`$skillUserAgent` and `$()` expressions from expanding.

Do not diagnose quoting or malformed header arguments as expired sign-in.
Keep each header one `Name=Value` argument. For quoted ETags or headers with
shell metacharacters, use `--headers '@headers.json'` with an approved local
JSON object instead of inline escaping; never put credentials in that file.
Use `--body '@request.json'` for JSON and quote file arguments containing spaces.
Do not print tokens, request payloads, raw private responses or `--debug` output.
Parse captured JSON instead of quoting JMESPath expressions for
`@odata.etag`/`@odata.nextLink`. Use documented OData paths;
documented slash-style paths are also valid, not guessed replacements.
Clean up owned local payload/header files per the
[retention and cleanup contract](safety-and-idempotency.md#scenario-cleanup).

## Discovery and pagination

PowerShell selection and pagination, without needing `$select` in the first URL
(`$dataApiVersion`, `$skillVersion` and endpoint come from task context):

On Windows PowerShell with `az.cmd`, replace `--url $url` with `--url ('"' + $url + '"')` and keep JSON in quoted `@file` arguments; see [Windows quoting](#windows-quoting).

```powershell
$skillUserAgent = "foundry-iq-skill-v$skillVersion"
$endpoint = "https://<search-service>.search.windows.net"
$next = "$endpoint/knowledgesources?api-version=$dataApiVersion"
while ($next) {
    if (([uri]$next).Scheme -ne 'https' -or ([uri]$next).Authority -ne ([uri]$endpoint).Authority) {
        throw 'Unverified continuation origin.'
    }
    $requestHeaders = @("User-Agent=$skillUserAgent", "Content-Type=application/json",
                       "x-ms-client-request-id=$([guid]::NewGuid())")
    $url = $next
    $json = az rest --method get --url $url --resource https://search.azure.com --headers @requestHeaders
    if ($LASTEXITCODE -ne 0) { throw 'Discovery failed; inspect the redacted error before retrying.' }
    $page = $json | ConvertFrom-Json
    $page.value | Select-Object name, kind, @{Name='etag'; Expression={$_.'@odata.etag'}}
    $next = $page.'@odata.nextLink'
}
```

Follow the returned continuation unchanged, including its version and escaped
query parameters. If `$select` is needed, construct its URL with a literal
single-quoted fragment plus the resolved version, as in the documentation's selected-
properties example. Never let PowerShell expand `$select`.

Bash uses `az rest` directly (set variables from task context, not leftover shells):

```bash
skillUserAgent="foundry-iq-skill-v${skillVersion}"
az rest --method get \
  --url "${endpoint}/indexes?api-version=${dataApiVersion}" \
  --resource https://search.azure.com --headers "User-Agent=${skillUserAgent}"
```

References: [SDK telemetry](https://azure.github.io/azure-sdk/general_azurecore.html#telemetry-policy), [Azure CLI REST](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/util.py), [Azure CLI Windows PowerShell quoting](https://learn.microsoft.com/cli/azure/use-azure-cli-successfully-powershell#pass-parameters-containing-the-ampersand-symbol).
