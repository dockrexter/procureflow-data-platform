# ProcureFlow source generator

Generate synthetic SAP S/4HANA-style procurement data and optionally upload it to `outbound/SAP_S4HANA/` using one manually triggered GitHub workflow.

## Run when you choose

Open [Generate and upload (manual)](https://github.com/dockrexter/procureflow-data-platform/actions/workflows/generate.yml), click **Run workflow**, and select **main**.

- **bootstrap**, date **2026-10-19**: initial history and master data.
- **daily**, a later date: transactions for that business date. Run dates in order when you need complete history.
- **generate_only**: downloadable files; no Azure login or upload.
- **generate_and_upload**: generate and replace files in source storage.

Each click runs one batch. There are no schedules, push/PR workflows, automated unit tests, ADF checks or deployments. Cancel an active run with **Cancel workflow**. Disable the workflow to prevent future manual starts.

Uploads always replace the same filenames in `outbound/SAP_S4HANA/`, without checking consumption. No date folders are used in outbound. The uploader verifies the local files and uploaded bytes, writes `_SUCCESS` last, and leaves other source folders alone. Do not overlap an upload with ADF reading or deleting files. The workflow does not invoke ADF; any independently configured Azure event triggers are managed separately.

## Files

| Path | Purpose |
|---|---|
| `.github/workflows/generate.yml` | The single manual workflow |
| `data-generator/generate.py` | Reproducible bootstrap and daily generator |
| `config/` | Source configuration and expected filenames |
| `scripts/publish_blob.py` | Batch validation and passwordless Blob upload |
| `tests/` | Optional local generator/uploader tests; Azure calls are mocked |
| `docs/` | Manual controls, data contract and authentication explanation |
| `adf/` | Existing definitions preserved; excluded from tests and workflows |

Your pipeline development remains on [dev_SAP_S4HANA](https://github.com/dockrexter/procureflow-data-platform/tree/dev_SAP_S4HANA). This cleanup does not modify that branch or any Azure resources.

## Optional local use

Python 3.11 or later; no Python packages are required.

```sh
python3 data-generator/generate.py bootstrap --date 2026-10-19
python3 data-generator/generate.py daily --date 2026-10-20
python3 -m unittest discover -s tests -v
```

Tests are run only when you execute the last command; they do not inspect ADF or connect to Azure. Generated-data validation during generation/upload remains enabled to avoid uploading corrupt files.

For a local upload, sign in using Azure CLI and run:

```sh
python3 scripts/publish_blob.py data/outbound/SAP_S4HANA/2026-10-19 --account pfsrcywlye2bmne5kc
```

GitHub uses the existing OIDC identity instead of a stored password. See [manual controls](docs/manual-generation.md), [authentication setup](docs/github-azure-setup.md), and [data contract](docs/data-contract.md).
