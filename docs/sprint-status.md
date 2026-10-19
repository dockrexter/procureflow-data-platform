# Sprint status — 2026-10-19

## Implemented and verified locally

- Thirteen deterministic extracts with consistent company/supplier/material relationships and purchase-to-payment event chronology.
- Bootstrap: 10,000 POs, 30,025 PO items, 59,070 partial receipt events, 9,441 invoices / 28,376 invoice lines, 6,133 payments, 87,446 PO-history events, 450 synthetic exchange rates, plus all master data.
- Daily sample for 2026-10-20: 100 POs, 298 PO items, 658 receipts, 110 invoices / 332 invoice lines, 110 payments and 5 FX rates.
- Ten automated tests pass, including exact reconstruction over 40 daily increments, corruption rejection, chronology/totals, deterministic bytes and idempotent local landing.
- Local bootstrap landing is complete and checksum verified. Generated data is outside Git.
- ADF JSON parses and all dataset/linked-service references resolve locally.
- Subscription-scoped Azure Bicep compiles without warnings using the downloaded official Microsoft compiler.
- GitHub repository created as private; code publication and cloud validation are tracked below.

## Cloud verification in progress

Azure portal trial credit and expiry reviewed. Cloud Shell subscription API confirms FreeTrial_2014-09-01, Enabled, spendingLimit On. No upgrade was performed. Foundation deployment, first Azure landing, GitHub publication and CI results will be recorded after their actual results.

## Not yet an operational pipeline

SFTP host/Key Vault credentials, production delivery, ADF execution and Databricks execution are not proven by local tests. The Databricks bundle/notebook requires service-side validation. Silver, Gold and Power BI are outside this foundation sprint.
