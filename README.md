# ProcureFlow

One independent, deterministic synthetic SAP S/4HANA-style procurement source and an Azure data platform foundation. These are simplified extracts, not SAP database replicas or a production SAP connector. No real supplier or personal data is used.

## Run locally

Python 3.11+; generator and local landing have no external dependencies. From this repository:

```sh
python3 -m unittest discover -s tests -v
python3 data-generator/generate.py bootstrap --date 2026-10-19
python3 data-generator/generate.py daily --date 2026-10-20
python3 scripts/landing.py data/outbound/SAP_S4HANA/2026-10-19 --local-root data/landing
```

The bootstrap contains 90 days of history, 5 companies, 20 plants, 10 purchasing organizations, 1,000 suppliers, 5,000 materials, 10,000 POs and their lifecycle events through the bootstrap date. Daily batches add 100 POs and events falling on that date, including events for earlier POs. Future-dated sample batches are tests, not live production activity.

## Repository

- `data-generator/`: independent source simulator.
- `config/`: immutable source identity, seed, epoch and volumes.
- `sftp/`: local SSH-key-only SFTP fixture (localhost port 2222).
- `adf/`: parameterized SFTP-to-landing pipeline and linked services.
- `infrastructure/bicep/`: resource group, ADLS Gen2, ADF identity/access, optional Databricks workspace.
- `databricks/`: bundle and verified-batch Bronze Delta ingestion notebook; requires configured workspace/storage access and an existing cluster.
- `scripts/`: validation, local/Azure landing and deployment helpers.
- `.github/workflows/`: tests, infrastructure compilation, daily source artifacts.
- `docs/`: contracts, costs, operation and actual sprint status.

Generated data and credentials are ignored by Git. The scheduled source workflow produces retained GitHub Actions artifacts; optional atomic SFTP publication activates only when `SFTP_PUBLISH_ENABLED=true` and the documented secrets are configured. No SFTP host is connected yet. No Azure deployment is performed by a push or scheduled workflow.

See [data contract](docs/data-contract.md), [runbook](docs/runbook.md), [cost review](docs/cost-review.md) and [sprint status](docs/sprint-status.md).
