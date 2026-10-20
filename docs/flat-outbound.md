# One folder per source, fixed filenames

Azure source: `pfsrcywlye2bmne5kc/outbound/SAP_S4HANA/`. Each upload replaces that source's files regardless of whether ADF consumed the prior batch. There are no date subfolders in outbound. Local generated folders and lake landing retain dates for reproducibility/history.

The uploader verifies its local batch, removes the old `_SUCCESS`, removes obsolete blobs only under this source prefix, overwrites and reads back each CSV and manifest, then writes `_SUCCESS` last. It does not query ADF, wait for consumption or check for an empty folder. GitHub uploads are serialized. Do not start an upload while ADF reads or deletes files: replacement is not atomic and there is no shared lock.

## ADF pipeline

`pl_blob_to_landing` uses the Array parameter `tableFiles`, whose default is the 13 filenames in `config/sap_s4hana_files.json`.

1. `CheckComplete` / `RequireComplete` require `_SUCCESS` before continuing.
2. `ReadManifest` reads `manifest.json` with a JSON dataset and Lookup.
3. `ListSourceFiles`, `ExpectedFilesPresent` and `RequireExpectedFiles` require the expected table names plus the two control files, and check the manifest source.
4. `ClearLandingMarker` removes the previous landing completion marker before a retry overwrites data.
5. `CopyTables` loops through the array, using `@item()` as the filename. Destination: `landing/<source>/<manifest.batch_date>/`.
6. `CopyManifest` and `CommitBatch` copy the control files last. Binary copy data-consistency checking is enabled.

These checks validate filenames and transfer consistency, not CSV columns, business rules or manifest SHA256 values inside ADF. The generator tests and uploader validate generated batches; downstream Silver validation remains a separate learning step.

Run the published pipeline manually after the GitHub upload succeeds. Defaults select the SAP source and existing storage accounts. No batchDate input is needed: the manifest supplies it. The trigger definition is Stopped and targets the flat source `_SUCCESS` path. No automatic ingestion is enabled.

Source deletion is not enabled. ADF currently has read-only source access; the uploader replaces files on the next run anyway. A future consume-and-delete step needs source delete permission and must happen only after successful landing validation, with no overlapping upload.

ADF Git mode shows the selected branch; live mode shows the deployed factory. Use main for these definitions, or merge main into your working branch before editing/publishing so older definitions do not replace them.

## Automate later

Keep manual Run workflow / Cancel workflow controls now. When the complete platform is ready, add a GitHub schedule (UTC) to generate.yml; scheduled runs need a daily mode/date default (supplied by scheduled_generate.py) AND the login/upload step conditions must allow github.event_name == 'schedule'. Merely adding a cron would otherwise generate without uploading. Update the run summary for scheduled inputs too. Choose a time when ingestion is not running. GitHub schedules can be delayed; explicitly replay missed dates. Keep bootstrap manual. ADF can then use `_SUCCESS` events, reading the manifest date. OIDC upload access is already configured; no password is needed. Scheduling is not enabled by this change.
