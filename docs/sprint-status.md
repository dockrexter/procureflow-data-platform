# Current change — 2026-10-20

Source publishing now replaces fixed filenames under outbound/SAP_S4HANA/ without checking consumption. Obsolete dated folders within this source are removed during publication. Other sources are untouched. Local generator output and historical landing retain dated folders.

12 tests pass, including replacement of a prior batch, stale folder cleanup, source isolation and interruption recovery. The ADF source path definition was adapted; the expected filename array is in config/sap_s4hana_files.json. The existing trigger definition is paused and its obsolete folder-date mapping cleared; a manifest Lookup should supply the date before reactivation. This repository change does not publish ADF automatically.

Live migration verification is pending. See flat-outbound.md for the learning steps and concurrency limitations.

## Previous deployment evidence

## Completed

- Synthetic SAP-style generator, reproducible bootstrap/daily data and direct Blob upload helper.
- Azure foundation deployment returned Succeeded: resource group rg-procureflow-dev, source storage pfsrcywlye2bmne5kc, ADLS procureflowywlye2bmne5kc, and factory adf-procureflow-ywlye2bmne5kc in North Europe.
- User connected ADF to Git. Its factory, publish_config.json and updated ls_adls were found in remote commit de04f4f and preserved.
- Removed Bicep, infrastructure deployment commands and automatic ADF execution helpers.
- Added a manual-only generation/upload workflow at the user’s request. It has no schedule and does not start ADF. See manual-generation.md for start/cancel controls.

## Upload evidence and remaining work

- Source bootstrap uploaded and read-back verified by GitHub run 39289889086: 13 CSVs, manifest.json and _SUCCESS at outbound/SAP_S4HANA/2026-10-19/. First ADF landing ingestion has not been run by this agent.
- The attempted ADF publication failed on ls_adls URL format before the user updated that linked service. No subsequent publication or pipeline execution was attempted.
- Manual publisher OIDC setup is complete with user-approved container-only access. Daily scheduling remains absent.
- Databricks workspace/compute was not deployed. Bronze code is a later learning step.
- Existing Azure resources were retained; removing code does not delete resources or eliminate storage charges.

## Validation

12 local tests cover generation, data integrity, landing and Blob upload retry/conflict behavior using mocked cloud calls. ADF JSON reference checks are offline checks, not proof of a working live pipeline. The manual workflow can supply source files while the user builds the ADF pipeline.

Successful cloud run: https://github.com/dockrexter/procureflow-data-platform/actions/runs/39289889086

The first attempt failed authentication because the GitHub OIDC subject included immutable owner/repository IDs. The trust record was corrected to match the same approved repository and main branch; the next run succeeded. No storage keys or passwords were committed.
