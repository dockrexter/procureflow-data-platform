# ProcureFlow

A learning project: synthetic SAP-style procurement data, independent daily delivery, and an Azure data platform. You will configure and activate each stage step by step. These extracts are simplified simulations, not a real SAP connector.

```text
GitHub Actions: manually started Python generator
    ↓ verified upload, completion marker last
Azure source Blob Storage: outbound/SAP_S4HANA/
    ↓ Azure Data Factory
Separate ADLS Gen2 account: landing/SAP_S4HANA/YYYY-MM-DD/
    ↓ Databricks
Bronze → Silver → Gold → Power BI (later stages)
```

No laptop, SFTP server, Docker container or continuously running VM is needed for the future cloud workflow. GitHub provides temporary runners; Azure stores the delivered files between runs. Scheduling is best effort, so missed dates must be replayed.

## Start locally

Python 3.11+; generator and tests use the standard library:

```sh
python3 -m unittest discover -s tests -v
python3 data-generator/generate.py bootstrap --date 2026-10-19
python3 data-generator/generate.py daily --date 2026-10-20
python3 scripts/landing.py data/outbound/SAP_S4HANA/2026-10-19 --local-root data/landing
```

Bootstrap includes 90 days of history, 5 companies, 20 plants, 10 purchasing organizations, 1,000 suppliers, 5,000 materials, 10,000 POs and related events through the bootstrap date. Daily batches add 100 POs and events for that day, including receipts/payments for earlier POs. The epoch is in `config/sap_s4hana.json`; do not change it mid-stream.

## Directory guide

| Folder | What you will learn |
|---|---|
| `data-generator/` | Python, business relationships and reproducible data |
| `config/` | Source settings such as dates, volumes and random seed |
| `data/` | Local generated files, excluded from Git |
| `scripts/` | Direct storage uploads and validation |
| `adf/` | Blob-source linked service, datasets and copy pipeline |
| `databricks/` | Bronze processing code and job configuration |
| `.github/workflows/` | Code checks and a manually started generation/upload workflow |
| `tests/` | Automated checks for correctness and delivery failures |
| `docs/` | Data contract, learning steps, costs and actual status |
| `powerbi/` | Reserved for later reporting work |

.yml files are instructions read by GitHub Actions or Databricks; `.py` contains logic, `.json` holds structured settings, and `.md` contains explanations. A definition file does not create a cloud resource on its own.

## Current learning setup

Azure resources already exist. Manage them through the Azure portal; infrastructure templates and deployment scripts have been removed. ADF is connected to Git by the user; build and publish the pipeline in ADF Studio.

Generation/upload is **manual only**: open GitHub Actions → Generate and upload (manual) → Run workflow. Choose a business date, bootstrap/daily, and generate_only/generate_and_upload. Use Cancel workflow on an active run to stop it. There is no daily schedule and no ADF execution.

See [manual controls](docs/manual-generation.md). Existing Azure resources have not been deleted; storage remains subject to charges. See [learning steps](docs/runbook.md), [data contract](docs/data-contract.md), [cost review](docs/cost-review.md), and [verified status](docs/sprint-status.md).

Source replacement and the ADF pipeline: [flat outbound guide](docs/flat-outbound.md). Learn to reproduce authentication and later scheduling: [GitHub/Azure setup](docs/github-azure-setup.md).
