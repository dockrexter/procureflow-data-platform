# Current status: cloud-storage delivery architecture

## Local changes completed

- Replaced the SFTP/Docker configuration with a Blob source linked service, source dataset and `pl_blob_to_landing` ADF pipeline.
- Added a separate source-storage account/outbound container to Bicep. ADF reads the source and writes the separate lake's landing container.
- Added verified Blob publishing using Azure CLI/Entra authentication, plus optional ADF invocation and status monitoring after publication.
- Updated GitHub Actions to use OIDC and separate opt-in switches for generation, uploads and ADF execution.
- Updated the step-by-step learning guide. Existing generator, schemas and local generated data are preserved.

## Existing data foundation

Bootstrap: 10,000 POs, 30,025 PO items, 59,070 partial receipts, 9,441 invoices / 28,376 invoice lines, 6,133 payments, 87,446 history events and 450 FX rates, plus all master data. A reproducible daily sample and checksum-verified local landing also exist.

## Validation

- 13 local tests pass, including interrupted Blob upload/resume, conflicting retries and ADF manifest parameter/failure handling with mocked cloud calls.
- ADF JSON/reference checks pass.
- Updated subscription-scoped Bicep compiles without warnings.
- No live cloud integration test was run.

## Not deployed or activated

The user has now requested publication and deployment. Publication and Azure deployment verification are in progress; do not infer deployed resources from the definitions. Daily generation and live uploads remain disabled unless explicitly activated after verification. The repository is retained, not deleted.

The earlier Azure check found an enabled trial with spending protection On, 29 days remaining and EUR 175.99/USD 200 displayed. This is historical, not a refreshed billing check. Review billing before deployment.

Next user-led steps: understand the generator, choose/create the repository, publish revised code, review Azure costs, deploy foundation, configure GitHub OIDC permissions, upload bootstrap, publish/test ADF, backfill needed dates, then enable daily automation. Databricks execution remains a later step.

The former SFTP publisher and its mocked tests were removed because that transport is no longer part of the design. New tests cover Blob publishing and ADF invocation without contacting cloud services. Local validation does not constitute a live Azure integration test.
