# Learn and activate one stage at a time

The files are prepared locally, but the user performs the setup. Do not run a deployment simply to follow this document from top to bottom. Finish and understand one stage first.

## 1. Understand and generate data

Start with suppliers, PO headers and PO items. Understand their keys before adding receipts, invoices and payments. The generator's configuration fixes the epoch and seed. Bootstrap must use the epoch date. Daily dates must follow it. Generate bootstrap first, then every subsequent business date in sequence. Existing identical batches are accepted; conflicting retries fail.

## 2. Understand GitHub automation

Publish the revised project to the repository you choose when ready. The previous repository still has its previous code until explicitly changed or deleted. `.github/workflows/ci.yml` runs tests and compiles Bicep. `generate.yml` runs the generator and retains a downloadable artifact for 30 days.

Scheduled generation at 03:15 UTC is skipped unless `DAILY_GENERATION_ENABLED=true`. Manual dispatch is available independently. Supply an explicit date and select bootstrap for the first run. A default daily dispatch on the epoch date is invalid. Re-run missed dates explicitly: GitHub cron can be delayed or skipped, and this implementation does not automatically discover gaps. Generate and ingest backfills sequentially. Retained artifacts are not permanent source storage.

## 3. Review cost, then create the foundation

The Bicep templates define two independent accounts: source Blob Storage (`outbound`) and the platform's ADLS Gen2 (`landing`, `bronze`, `silver`, `gold`). They also define ADF and its storage permissions. Databricks remains optional and disabled by default. No compute or Azure schedule is started by these definitions.

Refresh trial credit, expiry and spending protection before provisioning. Use the intended subscription ID; subscription names need not be unique. Commands for the later deployment lesson:

```sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
python3 scripts/cost_preflight.py --subscription "$AZURE_SUBSCRIPTION_ID"
az deployment sub what-if --location northeurope --template-file infrastructure/bicep/main.bicep
# Review the preview before running the following command:
az deployment sub create --name procureflow-foundation --location northeurope --template-file infrastructure/bicep/main.bicep
```

Outputs include `sourceStorageAccount`, `storageAccount` (the lake), `factoryName` and `resourceGroup`. Public blob access and shared-key authentication are disabled. Authenticated endpoints are publicly reachable for this learning setup. ADF gets Storage Blob Data Reader on `outbound` and Storage Blob Data Contributor on `landing`. These role assignments are definitions until deployment.

## 4. Connect GitHub to the source account

Configure a dedicated Microsoft Entra application/service principal or user-assigned identity with GitHub OIDC federation. Restrict trust to the chosen repository and `main` branch (`repo:OWNER/REPOSITORY:ref:refs/heads/main`); issuer is `https://token.actions.githubusercontent.com` and audience is `api://AzureADTokenExchange`. Avoid long-lived client secrets or storage keys.

Give this publisher Storage Blob Data Contributor on the source account's **outbound container only**. Read access is needed to verify uploads. It does not need lake write access. Identity creation and this publisher role are not included in the foundation template; they are a separate setup lesson.

Set these GitHub repository variables:

| Variable | Value |
|---|---|
| `AZURE_CLIENT_ID` | Publisher application's/identity's client ID |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Selected subscription ID |
| `SOURCE_STORAGE_ACCOUNT` | Source account output, not the lake |
| `AZURE_SOURCE_PUBLISH_ENABLED` | `true` only after configuration and cost review |

`azure/login@v2` obtains a short-lived token using `id-token: write`. Identifiers are not passwords. The upload script uses `az storage blob ... --auth-mode login`.

For a manual smoke test from an appropriately authorized Azure CLI session:

```sh
python3 scripts/publish_blob.py data/outbound/SAP_S4HANA/2026-10-19 --account "$SOURCE_STORAGE_ACCOUNT"
```

It checks manifest hashes/counts, compares existing blobs, verifies uploaded content by read-back, and writes `_SUCCESS` last. Consumers ignore directories without the marker. Blob publication is not an atomic directory rename. An interrupted upload resumes on retry; a different existing file fails instead of being overwritten. Use one writer per source/date and keep published batches immutable.

## 5. Configure and test ADF ingestion

Publish the source definitions in dependency order with `scripts/deploy_adf.py`, or build them together in ADF Studio. The pipeline is `pl_blob_to_landing`; its parameters are `source` (SAP_S4HANA), `batchDate`, `sourceAccount` and `account` (the lake).

The managed-identity Blob linked service reads the source account. The ADLS linked service writes landing. The pipeline checks `_SUCCESS`, copies CSVs, then manifest, then completion marker. It is serial (`concurrency: 1`). Only immutable batches may be replayed; Bronze validates checksums before processing. ADF copy success alone is not a semantic data-quality check.

Run one manual bootstrap ingestion and inspect the activity results and landing files. Native ADF GitHub authorization is a separate setup: `githubOwner` in Bicep supplies repository metadata, but does not grant OAuth consent. Main is the collaboration branch and `/adf` is the root. Source control and publishing to the live factory are distinct.

## 6. Activate end-to-end daily delivery

The GitHub workflow can start ADF **after a successful upload**, avoiding a second independent clock. For this step, grant the publisher identity a custom role scoped to the dedicated factory with these actions: `Microsoft.DataFactory/factories/pipelines/createRun/action` and `Microsoft.DataFactory/factories/pipelineruns/read`. Configure the role and verify it in a manual test before enabling automation; it is not deployed by the foundation template.

Additional variables: `AZURE_RESOURCE_GROUP`, `ADF_FACTORY`, `LANDING_STORAGE_ACCOUNT`, and `ADF_RUN_ENABLED=true`. `scripts/run_adf.py` takes the source/date from the batch manifest, starts the copy and monitors its status. Failures fail the workflow. A monitoring timeout does not cancel the Azure run: inspect the displayed run ID before retrying. No Databricks run is triggered by this workflow.

After the bootstrap and needed backfill dates have landed, set `DAILY_GENERATION_ENABLED=true`. Keep all switches off until the preceding lessons are complete. To pause, unset the generation or publication switch. Existing cloud storage remains billable until removed or emptied appropriately.

## 7. Later: Databricks and reporting

Configure Databricks authentication, an existing cluster and storage access. Validate the bundle with `cluster_id`, `landing_path` and `bronze_path`, then deploy and run when ready. The bundle does not create compute; running a job can start billable compute. Bronze verifies all file checksums/counts, replaces source/date partitions on replay and writes a final receipt. Silver, Gold and Power BI are later learning stages.

## Official references

- https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure
- https://github.com/Azure/login
- https://learn.microsoft.com/en-us/azure/data-factory/connector-azure-blob-storage
- https://learn.microsoft.com/en-us/azure/data-factory/connector-azure-data-lake-storage

## Cleanup

Review resources and preserve needed data before deleting the project resource group. Never remove unrelated resources or turn off subscription spending protection as a shortcut. GitHub repository deletion is a separate action and has not been completed.
