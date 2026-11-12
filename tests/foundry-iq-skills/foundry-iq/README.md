# Foundry IQ entry-point regressions

The three Vitest cases run [entrypoint_regressions.py](entrypoint_regressions.py)
against the current public distributable, not the intentionally retired helpers:

- Runtime status rejects damaged wheel/lock files, escaping asset paths and an
  unsupported manifest before setup or cache creation.
- Runtime verification rejects stale receipts, pinned-package changes, added
  packages and a different Python environment without rewriting the receipt.
- The real prompt-binding CLI parses inputs and emits planned/blocked/created
  JSON. Planning and stale approval never write. Approved creation preserves
  existing settings and creates only a verified draft; failed or invalid
  readback never replays the write.

SDK clients, credentials and model objects are synthetic, following the former
offline fixture pattern. These tests do not verify Azure SDK serialization or
service acceptance. Socket connections, child processes and process replacement
are forbidden inside the fixtures. No Azure login, installation or model runs occur.

These are current-contract replacements, not equivalent coverage of retired
Search creation, File reuse/upload, Blob inventory or helper cleanup behavior.
Those business guarantees still need separately approved non-graph workflow
evaluations. Old direct/package helper imports are no longer supported routes.

Run from the repository root with Python 3.12 and the test dependencies installed:

```powershell
$env:PYTHON = 'C:\path\to\python.exe' # Optional when python on PATH is 3.12
npm --prefix tests test -- foundry-iq-skills/foundry-iq/helpers.test.ts
```

```bash
PYTHON=/path/to/python3.12 npm --prefix tests test -- foundry-iq-skills/foundry-iq/helpers.test.ts
```

The underlying standard-library suite can also run directly:

```powershell
python -B .\tests\foundry-iq-skills\foundry-iq\entrypoint_regressions.py
```

```bash
python3.12 -B ./tests/foundry-iq-skills/foundry-iq/entrypoint_regressions.py
```

No tests are skipped by platform. These checks do not replace CodeQL, native build,
client compatibility, graph eval discovery/executor or source export gates.
