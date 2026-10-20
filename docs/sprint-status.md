# Verified status — 2026-10-20

## Completed

- Azure foundation exists: rg-procureflow-dev, source pfsrcywlye2bmne5kc, lake procureflowywlye2bmne5kc and adf-procureflow-ywlye2bmne5kc.
- Manual GitHub generation/upload uses OIDC with user-approved access only to outbound. There is no generation schedule.
- Run https://github.com/dockrexter/procureflow-data-platform/actions/runs/39406891778 successfully uploaded and read-back verified the bootstrap directly under outbound/SAP_S4HANA/. The uploader removes old dated subfolders and obsolete files within that source, replaces existing filenames unconditionally, and writes _SUCCESS last. It does not check consumption. Other sources are untouched.
- 12 local tests and GitHub CI passed. Tests cover replacement, cleanup, source isolation, interruption/retry and generator integrity.
- Main contains updated ADF source paths, config/sap_s4hana_files.json for the expected-table array, and learning guides for ADF and passwordless GitHub/Azure setup.

## ADF deployment

Published the flat-source linked service, source/manifest/landing datasets, filename-array pipeline and stopped trigger to the live factory on 2026-10-20. The pipeline reads its date from manifest.json; no batchDate parameter is needed. Test run `9a8fbf98-70c3-4d4f-8f4d-ad5697e2be8d` is in progress; a successful landing has not yet been confirmed for this version.

The ADF editor currently selects main. Refresh it to load the latest Git definitions. Git commits and live publication remain separate operations. Source cleanup is not enabled: ADF has read-only access to outbound, and the next upload replaces the existing source files without checking consumption.

Azure subscription is Enabled with FreeTrial quota and spendingLimit On, verified on 2026-10-20. Remaining credit was not re-measured. The test uses existing ADF and storage resources; no Databricks compute or new paid service was provisioned.

Do not overlap uploads with ADF reads/deletes: source replacement is not atomic and _SUCCESS does not lock files for an already-running reader. Daily files remain increments; preserve each consumed batch in landing before replacement if history matters.

Databricks compute has not been deployed or started. Bicep and automatic deployment scripts were removed at the user's request. No secrets or storage keys are committed.
