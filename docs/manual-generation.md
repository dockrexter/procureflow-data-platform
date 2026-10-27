# Start and stop generation/upload manually

Open https://github.com/dockrexter/procureflow-data-platform/actions/workflows/generate.yml.

Bootstrap uses **2026-10-19**. For increments, choose the next business date you want to generate after the batches you have already processed. The workflow does not track your ADF loads.

Each upload replaces the files directly under `outbound/SAP_S4HANA/`, whether or not ADF consumed the previous batch. There are no date subfolders in Azure outbound. Local/downloadable artifacts can retain date folders.

## Start

1. Click **Run workflow**, keeping branch **main**.
2. Enter **Datasource name**: `SAP_S4HANA`.
3. Enter **Date** in `YYYY-MM-DD` format.
4. Click **Run workflow**. It reads `config/sap_s4hana.json`, generates, validates and uploads the batch.

There are only two inputs. No mode or upload-action selection is needed. The config's epoch (`2026-10-19` for SAP_S4HANA) automatically selects initial history; later dates select daily increments. An earlier date or unknown datasource fails before Azure login/upload. Generate each date in order; missed dates are not filled automatically. Datasource names use uppercase letters, numbers and underscores and map to lowercase config filenames. Only SAP_S4HANA is supported today; new source types also need generator support.

The source path is `pfsrcywlye2bmne5kc / outbound / SAP_S4HANA /`. The workflow does not invoke ADF or Databricks. Independently configured Azure storage-event triggers may react to uploads; this cleanup does not change those triggers. No clock/schedule starts it. A completed run is stopped automatically; each click requests one batch, not a continuously running service.

## Stop

Open the running workflow and click **Cancel workflow**. Cancellation is not instantaneous and does not roll back files already uploaded. If the upload completed before cancellation, the batch remains complete.

Replacement removes the previous `_SUCCESS` first, overwrites the fixed filenames and writes a new marker last. If cancelled during upload, rerun the selected batch to replace it fully. Do not overlap upload with ADF reading or cleanup. The generator does not check consumption.

To prevent all future starts, use the workflow page's **… → Disable workflow**. Enable it again when ready. Disabling does not cancel an already running job: cancel that separately. Only one run is allowed to execute at a time; avoid queuing multiple dates and expect explicit replay if a pending run is replaced.

## What runs where

GitHub supplies a temporary computer. It generates and validates CSVs, retains a downloadable artifact for seven days, then authenticates through Azure OIDC and uploads the batch. No laptop needs to stay on. Storage and GitHub Actions usage remain subject to their normal charges/allowances.

The managed identity `id-procureflow-github-upload` trusts only this repository's main branch and receives Storage Blob Data Contributor only on the source outbound container. The workflow contains public resource identifiers, not passwords or storage keys. ADF Git integration is separate and is preserved.

Official instructions: [manual runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow), [cancelling runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/cancel-a-workflow-run).

The observed GitHub OIDC subject includes immutable owner/repository IDs: `repo:dockrexter@31271324/procureflow-data-platform@1425443797:ref:refs/heads/main`. Azure's trust record must match this exactly; it is not a password.
