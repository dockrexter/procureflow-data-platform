# One folder per source, fixed filenames

Azure source: `pfsrcywlye2bmne5kc/outbound/SAP_S4HANA/`. Each selected upload replaces that source's files regardless of whether ADF consumed the prior batch. No date subfolders remain in outbound. Local generated folders and lake landing retain dates for reproducibility/history.

The uploader verifies its local batch before making changes, removes the old `_SUCCESS`, removes obsolete blobs only under this source prefix, overwrites and reads back each CSV and manifest, then writes `_SUCCESS` last. It does not query ADF, wait for consumption or check for an empty folder. Concurrent GitHub uploads are serialized; manually run ADF only after upload finishes, and wait for ADF cleanup before another upload. There is no lock shared with ADF.

## Build your ADF checks

Copy the JSON array from `config/sap_s4hana_files.json` into a pipeline Array parameter named `tableFiles`. Keep the source dataset folder parameter equal to `@pipeline().parameters.source`. Use `@item()` as filename inside ForEach.

1. Check `_SUCCESS` exists.
2. Use Get Metadata childItems to list source files. Verify all array entries are present before any copies; ignore only the two control files. Filenames alone do not validate columns or data types.
3. Read `manifest.json` using a JSON dataset and Lookup. Use its `batch_date` as the landing date; do not derive it from the source folder or event timestamp.
4. ForEach over tableFiles copies each CSV to your historical landing folder. Copy the manifest and validate row counts/hashes before accepting the batch.
5. Add Delete activities only after successful landing validation. Delete only that consumed source's files. Do not overlap deletion and generation.

The existing repository pipeline source paths were updated. Its landing still takes batchDate explicitly; pass the manifest date during manual testing. The array and manifest-lookup steps above are your next ADF learning steps, not a claim that they are deployed. Your event trigger definition is paused for the layout migration; rework its date mapping before publishing and enabling it. The old folder-name date expression cannot work with this layout.

## Automate later

Keep manual Run workflow / Cancel workflow controls now. Once ADF is complete, add a GitHub schedule (UTC) to generate.yml; scheduled runs need a daily mode/date default (supplied by scheduled_generate.py) AND the login/upload step conditions must allow github.event_name == 'schedule'. Merely adding a cron would otherwise generate without uploading. Choose a time when ingestion is not running. GitHub schedules can be delayed; explicitly replay missed dates. Keep bootstrap manual. ADF can then use `_SUCCESS` events after its manifest-date handling is ready. OIDC upload access is already configured; no password is needed. Scheduling is not enabled by this change.
