# Operations

## Azure foundation

Use Azure CLI with an authenticated account, or Azure Cloud Shell. Identify the trial by ID, not its non-unique display name. Read the credit/expiry page, then:

```sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
python3 scripts/cost_preflight.py --subscription "$AZURE_SUBSCRIPTION_ID"
az deployment sub what-if --location northeurope --template-file infrastructure/bicep/main.bicep
az deployment sub create --name procureflow-foundation --location northeurope --template-file infrastructure/bicep/main.bicep
```

Default deployment creates only the foundation. `deployDatabricks=true` adds a workspace but no compute. `githubOwner=dockrexter` sets ADF repository metadata after repository access is established; native GitHub OAuth consent may still require the user in ADF Studio. Main is the collaboration branch; work in feature branches, PR to main, then publish/deploy. A repository link alone is not a successful connection or published pipeline.

ADF has a managed identity and a landing-container-scoped Storage Blob Data Contributor assignment. For a user's initial upload, that user needs a separate data role; subscription Owner alone does not necessarily grant blob data access. Never use storage account keys as a fallback. Confirm role-assignment authority before applying. RBAC propagation can take several minutes.

For first landing with Entra authentication:

```sh
python3 scripts/landing.py data/outbound/SAP_S4HANA/2026-10-19 --account "$STORAGE_ACCOUNT"
```

This verifies every downloaded blob against the local source and publishes the completion marker last. This direct upload is a foundation smoke test, not an ADF/SFTP end-to-end run.

## SFTP and ADF

Create a dedicated SSH key outside the repository; put only its public key at ignored `sftp/keys/source.pub`. Generate the bootstrap first. Run `docker compose -f sftp/compose.yaml up --build -d`. Port 2222 is localhost-only. Host keys are ephemeral in this fixture and change if the container is recreated; verify the new fingerprint explicitly. Stop with `docker compose -f sftp/compose.yaml down`.

ADF's cloud runtime cannot reach localhost. To use this fixture with ADF, provide an appropriate self-hosted integration runtime on a supported reachable host, or separately provision a reachable hardened SFTP source. The committed cloud SFTP linked service uses port 22. Change its port/connectVia for your selected runtime. Do not expose the local fixture to the internet as-is.

A real delivery service must publish each immutable date directory only after all files exist, using a staged directory and atomic rename. The GitHub generator produces artifacts and optionally publishes through `scripts/publish_sftp.py`. Configure secrets `SFTP_HOST`, `SFTP_USER`, `SFTP_PRIVATE_KEY`, `SFTP_KNOWN_HOSTS` and variables `SFTP_PORT` and `SFTP_PUBLISH_ENABLED=true`. Verify the server host key out of band; unknown keys are rejected. The remote account needs a writable `/outbound`. Publication stages and verifies files then atomically renames the date directory; conflicting existing batches fail. The localhost fixture is read-only because it serves the generator output directly. GitHub cron is best effort; manually dispatch missed business dates. Bootstrap once before daily consumption. Artifact retention is not a permanent ERP archive.

Store the SFTP private key as a Key Vault secret (the base64 private-key content expected by ADF). Supply host, username, verified host-key fingerprint, vault URL and secret name as pipeline parameters. Grant ADF read access only to the needed secret. No secrets belong in JSON or workflow files. The Key Vault and SFTP host are not created by this foundation.

Deploy ADF JSON in dependency order: linkedService, dataset, pipeline, after replacing/configuring environment-specific parameters in Studio. The pipeline checks `_SUCCESS`, copies CSVs, then manifest, then marker. No trigger is supplied or started. Run one manual batch and inspect its activity result and landed hashes before adding a daily trigger. Published ADF runs and Git authoring are separate states.

## Databricks

Set the host with the CLI's supported authentication; configure a dedicated storage identity/external location with landing read and Bronze write access. Validate `databricks bundle validate` with `cluster_id`, `landing_path` and `bronze_path` variables, then deploy. The existing cluster must have suitable runtime/Delta/storage configuration. No cluster is created by this bundle. Running the job starts billable compute if the chosen cluster is stopped. Validate checksums and counts, then inspect the Bronze receipt. Silver, Gold and Power BI transformations are next-phase work.

## Cleanup

Stop workloads first; review what is in `rg-procureflow-dev` before deleting the group through Azure. Deleting storage destroys data; download anything needed. If Databricks was enabled, review its managed resource group too. Do not delete unrelated resources or disable subscription protection.
