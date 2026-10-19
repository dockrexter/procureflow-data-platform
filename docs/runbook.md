# Step-by-step learning setup

## Current stage: build the pipeline yourself

Manage Azure resources in the portal. There are no Bicep templates or automated deployment scripts. ADF is already connected to Git by the user. Preserve its factory definition, publish settings and linked services; make pipeline changes in ADF Studio and commit them there. A Git commit and publishing to the live factory are different actions.

The intended flow is: generator → direct Blob upload → your ADF pipeline → lake → later Databricks transformations.

## Generate locally when ready

Use Python 3.11 or later:

```sh
python3 data-generator/generate.py bootstrap --date 2026-10-19
python3 data-generator/generate.py daily --date 2026-10-20
```

The epoch and seed are fixed in config/sap_s4hana.json. Bootstrap uses the epoch; daily batches follow it. Generate backfills in date order. Local generation does not upload data.

## Upload only after completing the pipeline

The retained uploader uses Azure CLI login, checks file hashes and row counts, verifies uploaded bytes, and writes `_SUCCESS` last. Identical retries are accepted; conflicting files are not overwritten. The future publisher needs Storage Blob Data Contributor on the source outbound container, not subscription-wide access.

Do not execute uploads yet. When ready, the command is:

```sh
python3 scripts/publish_blob.py data/outbound/SAP_S4HANA/2026-10-19 --account pfsrcywlye2bmne5kc
```

## Future laptop-independent automation

`docs/templates/generate-upload.yml.example` is an inactive example, not an executable GitHub workflow. It generates data and uploads directly to Blob Storage, with no ADF invocation. It currently has no schedule. Keep it outside `.github/workflows/` until the complete pipeline has been built and tested.

Later, configure GitHub-to-Azure OIDC and repository variables AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, SOURCE_STORAGE_ACCOUNT and AZURE_SOURCE_PUBLISH_ENABLED. Do not store passwords or storage keys in Git. Only then move the template into the workflows folder and test an explicit bootstrap date. Add daily scheduling as a separate final step. Missed dates require explicit replay.

`.github/workflows/ci.yml` only runs validation; it neither generates production batches nor uploads, provisions or runs ADF. Databricks configuration is retained for a later lesson and is not deployed.
