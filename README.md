# ProcureFlow

A learning project: synthetic SAP-style procurement data, independent daily delivery, and an Azure data platform. You will configure and activate each stage step by step. These extracts are simplified simulations, not a real SAP connector.

```text
GitHub Actions: scheduled Python generator
    ↓ verified upload, completion marker last
Azure source Blob Storage: outbound/SAP_S4HANA/YYYY-MM-DD/
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
| `scripts/` | Publishing, validation and running an ADF batch |
| `adf/` | Blob-source linked service, datasets and copy pipeline |
| `infrastructure/bicep/` | Resource group, source storage, ADLS, ADF and optional Databricks definitions |
| `databricks/` | Bronze processing code and job configuration |
| `.github/workflows/` | Code checks and the future daily workflow |
| `tests/` | Automated checks for correctness and delivery failures |
| `docs/` | Data contract, learning steps, costs and actual status |
| `powerbi/` | Reserved for later reporting work |

`.yml` files are instructions read by GitHub Actions or Databricks; `.bicep` describes Azure resources, `.py` contains logic, `.json` holds structured settings, and `.md` contains explanations. A definition file does not create a cloud resource on its own.

## Not activated

The revised architecture is prepared for publication and deployment. See docs/sprint-status.md for verified deployment results. The repository is retained at the user’s request.

The revised workflow has three independent switches, all disabled when unset: `DAILY_GENERATION_ENABLED`, `AZURE_SOURCE_PUBLISH_ENABLED`, and `ADF_RUN_ENABLED`. A manual generation run can create an artifact without Azure access. No push or workflow provisions Azure resources. Cloud identities, access and cost checks must be completed before activation.

See [step-by-step runbook](docs/runbook.md), [data contract](docs/data-contract.md), [cost review](docs/cost-review.md) and [current status](docs/sprint-status.md).
