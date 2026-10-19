# Sprint status — 2026-10-19

## Implemented and verified locally

- Thirteen deterministic extracts with consistent company/supplier/material relationships and purchase-to-payment event chronology.
- Bootstrap: 10,000 POs, 30,025 PO items, 59,070 partial receipt events, 9,441 invoices / 28,376 invoice lines, 6,133 payments, 87,446 PO-history events, 450 synthetic exchange rates, plus all master data.
- Daily sample for 2026-10-20: 100 POs, 298 PO items, 658 receipts, 110 invoices / 332 invoice lines, 110 payments and 5 FX rates.
- Twelve automated tests pass, including exact reconstruction over 40 daily increments, corruption rejection, chronology/totals, deterministic bytes and idempotent local landing.
- Local bootstrap landing is complete and checksum verified. Generated data is outside Git.
- ADF JSON parses and all dataset/linked-service references resolve locally.
- Subscription-scoped Azure Bicep compiles without warnings using the downloaded official Microsoft compiler.
- Private GitHub repository published: https://github.com/dockrexter/procureflow-data-platform
- GitHub CI succeeded on initial code commit 61b9aedd23d5ba3da3254849ddfaff565bb7f0af: https://github.com/dockrexter/procureflow-data-platform/actions/runs/39237749986
- Optional host-key-verified SFTP publisher implemented; mocked transport tests cover retries, conflicts and interrupted publication.

## Cost check completed; cloud deployment blocked

Azure portal trial credit and expiry reviewed. Cloud Shell subscription API confirms FreeTrial_2014-09-01, Enabled, spendingLimit On. No upgrade was performed. No ProcureFlow Azure resource was provisioned. Local Azure CLI/authentication is unavailable; the authenticated Cloud Shell was reachable for the read-only check, but file upload was blocked by the browser extension setting, then browser control became unavailable. The deployment preview did not execute.

Remaining: Azure resource group/ADLS/ADF deployment, native ADF GitHub authorization, real SFTP/Key Vault configuration, first Azure landing and ADF run, Databricks service-side validation/execution. Bicep and scripts are ready for those steps. The local Docker daemon is not running, so the SFTP container was not started. No secrets or generated CSVs were committed.

## Not yet an operational pipeline

SFTP host/Key Vault credentials, production delivery, ADF execution and Databricks execution are not proven by local tests. The Databricks bundle/notebook requires service-side validation. Silver, Gold and Power BI are outside this foundation sprint.
