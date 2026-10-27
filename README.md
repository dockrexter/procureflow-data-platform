# ProcureFlow source generator

Generate synthetic SAP S/4HANA-style procurement data and upload it to `outbound/<datasource>/` using one manually triggered GitHub workflow.

## Run when you choose

Open [Generate and upload (manual)](https://github.com/dockrexter/procureflow-data-platform/actions/workflows/generate.yml), click **Run workflow**, and select **main**.

The workflow has exactly two inputs:

1. **Datasource name**: `SAP_S4HANA` or `SAP_S4HANA_2` (loads the matching lowercase filename in `config/`).
2. **Date**: the business date, in `YYYY-MM-DD` format.

Every successful run generates and uploads. The configured epoch date produces the initial history and master data automatically; later dates produce daily increments. Dates before the epoch are rejected. Generate dates in order when you need complete history. Both sources simulate separate SAP systems using the same generator adapter, with different seeds and volumes. A different ERP format would need its own adapter.

Each click runs one batch. There are no schedules, push/PR workflows, automated unit tests, ADF checks or deployments. Cancel an active run with **Cancel workflow**. Disable the workflow to prevent future manual starts.

Uploads always replace the same filenames in `outbound/<datasource>/`, without checking consumption. No date folders are used in outbound. The uploader verifies the local files and uploaded bytes, writes `_SUCCESS` last, and leaves other source folders alone. Do not overlap an upload with ADF reading or deleting files. The workflow does not invoke ADF; any independently configured Azure event triggers are managed separately.

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

The `adf/` folder was copied unchanged from [dev_SAP_S4HANA](https://github.com/dockrexter/procureflow-data-platform/tree/dev_SAP_S4HANA). Only its ADF files were imported into main; its workflows and scripts were not merged. The development branch and Azure resources were not modified.

## Optional local use

Python 3.11 or later; no Python packages are required.

```sh
python3 data-generator/generate.py --source SAP_S4HANA --date 2026-10-19
python3 data-generator/generate.py --source SAP_S4HANA --date 2026-10-20
python3 -m unittest discover -s tests -v
```

Tests are run only when you execute the last command; they do not inspect ADF or connect to Azure. Generated-data validation during generation/upload remains enabled to avoid uploading corrupt files.

For a local upload, sign in using Azure CLI and run:

```sh
python3 scripts/publish_blob.py data/outbound/SAP_S4HANA/2026-10-19 --account pfsrcywlye2bmne5kc
```

GitHub uses the existing OIDC identity instead of a stored password. See [manual controls](docs/manual-generation.md), [authentication setup](docs/github-azure-setup.md), and [data contract](docs/data-contract.md).

## Try the second datasource

Run the manual workflow on main with **Datasource name = SAP_S4HANA_2** and **Date = 2026-10-19** for the initial dataset. Use **2026-10-20** for its first daily increment. Its config is `config/sap_s4hana_2.json`; uploads go to `outbound/SAP_S4HANA_2/`, leaving `outbound/SAP_S4HANA/` alone. Both sources use the same 13 fixed CSV filenames plus manifest and completion marker.

The second source has seed 99, 1,500 initial POs, 30 new POs/day, 200 suppliers and 1,000 materials. Keys belong to their source; include the source identifier when combining datasets. Adding the generator does not configure ADF ingestion for it. The imported ADF definitions are exactly the development branch version.
