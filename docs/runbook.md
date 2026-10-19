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

## Upload source data for pipeline development

The retained uploader uses Azure CLI login, checks file hashes and row counts, verifies uploaded bytes, and writes `_SUCCESS` last. Identical retries are accepted; conflicting files are not overwritten. The future publisher needs Storage Blob Data Contributor on the source outbound container, not subscription-wide access.

The user has enabled manual generation and source uploads for pipeline development. The equivalent command is:

```sh
python3 scripts/publish_blob.py data/outbound/SAP_S4HANA/2026-10-19 --account pfsrcywlye2bmne5kc
```

## Manual laptop-independent automation

Use [manual generation controls](manual-generation.md) to start or cancel a batch in GitHub. The active workflow offers generate_only and generate_and_upload and has no schedule. It never starts ADF. The older inactive template was removed to keep one source of truth.

`.github/workflows/ci.yml` runs validation separately on code changes. Databricks configuration is retained for a later lesson and is not deployed.
