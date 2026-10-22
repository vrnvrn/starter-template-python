# Security patches, 2026-10-22

## Summary

`pip-audit` reported 52 known advisories across 8 packages in `uv.lock`. This change updates them to patched releases in the same major version. After the change, `pip-audit` reports none. An earlier fix from the same day (`certifi`) is listed below.

## Changes (`uv.lock`)

| Package | From | To | Advisories | Why it matters here |
| --- | --- | --- | --- | --- |
| aiohttp | 3.13.2 | 3.14.4 | 40 advisories, including CVE-2025-69224, CVE-2026-69243 and CVE-2026-111750 (request smuggling), CVE-2026-54275 (TLS SNI check bypass on connection reuse), CVE-2026-69244 (out-of-bounds read in C response parser), CVE-2026-34518, CVE-2026-47265 and CVE-2026-54276 (credentials and cookies sent across origins on redirect), several memory and CPU denial of service issues | web3 depends on aiohttp; the Arkiv SDK uses web3 for RPC calls to the node. |
| yarl | 1.22.0 | 1.25.1 | none directly; required by aiohttp 3.14.4 | Pulled in by the aiohttp bump. |
| idna | 3.11 | 3.15 | CVE-2026-45409 (CPU denial of service on crafted input) | Hostname handling in requests and aiohttp. |
| multidict | 6.7.0 | 6.9.1 | CVE-2026-104874 (reference leak in C extension, remote memory growth) | Header storage for aiohttp and yarl. |
| requests | 2.32.5 | 2.33.0 | CVE-2026-25645 (predictable temp file name in `extract_zipped_paths`) | HTTP transport used by web3 (RPC to the node) and by the Docker client that starts the test node. |
| urllib3 | 2.5.0 | 2.8.0 | CVE-2025-66418, CVE-2025-66471, CVE-2026-21441, CVE-2026-97689 (decompression and streaming memory exhaustion), CVE-2026-44431 (headers kept on cross-origin redirect), CVE-2026-97687 (proxy TLS settings) | Transport under requests. |
| python-dotenv | 1.2.1 | 1.2.2 | CVE-2026-28684 (`set_key` / `unset_key` follow symlinks) | Dependency of testcontainers, used to start the local test node. |
| pygments | 2.19.2 | 2.20.0 | CVE-2026-4539 (regex denial of service in a lexer) | Dependency of pytest (output highlighting). |
| pytest | 9.0.1 | 9.0.3 | CVE-2025-71176 (predictable `/tmp/pytest-of-{user}` directory on shared UNIX hosts) | Test runner. |

The lockfile was regenerated with `uv lock --upgrade-package <name>==<version>` for each package. A current uv (0.11.x) rewrites the whole file to lock revision 3 (about 3,300 changed lines), so the update was made with uv 0.5.5, which keeps the existing lock format. The diff only touches the packages above. Current uv versions read the file without changes (`uv lock --check` passes).

## Earlier fix today (commit 35fc532)

| Package | From | To | Reason |
| --- | --- | --- | --- |
| certifi | 2025.11.12 | 2026.10.19 | eMudhra CA compromise: private keys for 8 intermediate CAs were recoverable, so fraudulent certificates could be issued. certifi 2026.10.19 removes those intermediates. |

## Verification

| Check | Command | Before | After |
| --- | --- | --- | --- |
| Lock consistency | `uv lock --check`, `uv sync --locked` | pass | pass |
| Audit | `uv export --frozen --no-hashes --all-groups -o reqs.txt` then `uvx pip-audit -r reqs.txt --no-deps --disable-pip` | 52 advisories in 8 packages | none found |
| Test collection | `uv run python -m pytest --collect-only -q` | 24 tests collected | 24 tests collected |
| Tests | `uv run python -m pytest -n auto -q` | 24 errors | 24 errors (same cause) |
| Import and compile | `python -c "import arkiv, aiohttp, requests, urllib3, dotenv"`, `python -m compileall src tests` | pass | pass |

All 24 tests need a local Arkiv node, which the SDK starts from the Docker image `golemnetwork/golembase-op-geth:latest`. That image cannot be pulled from Docker Hub (`repository does not exist`), so every test fails at fixture setup with `ImageNotFound`, before and after this change. The tests could not confirm runtime behavior; they were checked for collection, imports and a clean lock only.

CI installs with `pip install -e .` and does not read `uv.lock`, so CI resolves its own versions. The lockfile matters for anyone who uses `uv sync`.

## Not fixed

Nothing. All advisories reported by `pip-audit` on 2026-10-22 have a patched release in the same major version.

## What users and forks should do

- Run `uv sync` to install the updated versions, or recreate `.venv`.
- If you installed with pip, run `pip install -U aiohttp idna multidict requests urllib3 python-dotenv pygments pytest certifi`.
- Projects created from this template before this date should apply the same updates to their own lockfile.
