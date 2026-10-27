# Source contract v1

Local generated batches retain `SAP_S4HANA/YYYY-MM-DD/` for reproducibility. In Azure outbound, the latest selected batch is stored directly at `SAP_S4HANA/` with 13 header-bearing CSVs, a row-count/SHA-256 manifest and `_SUCCESS` containing the manifest SHA-256. IDs are strings (preserve leading zeroes); money is fixed two-decimal text; quantities are whole EA units; dates are ISO business dates. FX is synthetic EUR per one unit of currency; EUR/EUR is one. No real market rates are implied.

| Extract | Primary key | Relationships |
|---|---|---|
| companies | BUKRS | company currency |
| plants | WERKS | BUKRS |
| purchasing_organizations | EKORG | BUKRS |
| suppliers | LIFNR | fixed synthetic master |
| materials | MATNR | fixed EA unit |
| exchange_rates | GDATU, FCURR, TCURR | daily EUR conversion |
| po_headers | EBELN | supplier, company, purchasing organization |
| po_items | EBELN, EBELP | PO, material, company-matching plant |
| goods_receipts | MBLNR | PO item |
| invoice_headers | BELNR | PO, supplier, company, currency |
| invoice_items | BELNR, BUZEI | invoice and PO item |
| payments | PAYMENT_ID | invoice, company, currency |
| po_history | EVENT_ID | exact receipt and invoice event reconciliation |

Full schemas and column order are declared in `data-generator/generate.py:SCHEMAS`.

Bootstrap is a snapshot as of the configured epoch. Daily is an insert-only event extract for one business date. Master data is intentionally stable: daily master CSVs contain headers only. There are no tax, credit memo, reversal, master CDC, invoice hold, or accounting ledger simulations in v1. Payments are simplified invoice settlements, not BKPF/ACDOCA replicas. PO IDs use explicit synthetic cohort prefixes rather than SAP's numeric field-width rules.

Each PO has 2–4 lines; each line receives two partial receipts at day +1/+2. Invoice occurs at day +3 to +7, payment 30 days later. Bootstrap therefore includes open orders, received/uninvoiced orders, unpaid invoices and paid invoices. Invoice amounts equal net line values; taxes are excluded. Counts of events are derived from chronology rather than forced to arbitrary target counts.

Determinism includes source configuration, generator version, cohort and index. Persist the Git commit and config alongside batches. Never change the config for a running source stream; version/migrate a source instead. Re-run any missed date individually; load bootstrap then increments in date order. No mutable checkpoint is required. Full-state reconstruction currently grows linearly with history and is appropriate for this learning-scale dataset; a production implementation would use persisted event state.

The writer stages locally then renames the completed local batch. Outbound is mutable: publishing removes the prior readiness marker, removes obsolete files and former date subfolders within the selected source only, overwrites each file, verifies uploaded bytes and writes `_SUCCESS` last. It never checks ADF consumption or waits for an empty folder. Other source prefixes are untouched. The batch date and mode remain in manifest.json.

Replacement is not atomic. `_SUCCESS` helps a new reader avoid an incomplete upload, but does not protect an already-running reader. Do not upload while ADF copies or deletes source files. Consumers must validate the manifest and hashes before accepting a landing batch. Cancellation or failed replacement can leave a partial folder; rerun the upload. Daily mode still means increments, not a full historical snapshot; archive each batch in landing before the next replacement if history matters.

A new source should provide its own adapter/config, source identifier and contract. Landing is source/date parameterized; do not mix incompatible schemas under SAP_S4HANA.

## Second simulated SAP system

`SAP_S4HANA_2` uses `config/sap_s4hana_2.json` and the same SAP adapter, table schemas and relationships. It has independent seed/volume settings and writes under its own source prefix. Both configurations start on 2026-10-19. Identifiers can overlap across systems: downstream joins and keys must include the source identifier. Each source must have its own bootstrap followed by daily increments.
