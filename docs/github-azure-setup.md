# Reproduce the GitHub-to-Azure connection yourself

This is the setup already used by the manual workflow. You do not need to create a second identity to use it.

1. In Azure Portal, open **Managed identities → Create**. Choose the project resource group and region. We created `id-procureflow-github-upload` in `rg-procureflow-dev`.
2. Open that identity and note its **Client ID** and **Tenant ID**. These identifiers are not passwords. The client ID is `2d095ccd-e9fc-4dbf-89de-86c2d52d4dc3`; the tenant is `0bfae774-6764-417a-9602-94c5eacc6c24`.
3. Open **Federated credentials → Add credential**. Configure the GitHub trust with issuer `https://token.actions.githubusercontent.com`, audience `api://AzureADTokenExchange`, and the exact repository/main-branch subject. Our observed subject is `repo:dockrexter@31271324/procureflow-data-platform@1425443797:ref:refs/heads/main`. Match the actual token subject shown by Azure Login rather than guessing the older name-only format.
4. Open the storage account `pfsrcywlye2bmne5kc`, then its `outbound` container and **Access control (IAM)**. Assign **Storage Blob Data Contributor** to this managed identity at the container scope only. This built-in role includes reading, writing and deleting blobs; it is not subscription Contributor and grants no ADF execution permission. The user explicitly approved this scope.
5. In the GitHub workflow give the upload job `contents: read` and `id-token: write`. The latter allows GitHub to issue an identity token; it does not itself grant Azure permissions.
6. Use `azure/login@v2` with the client ID, tenant ID and subscription ID. Our workflow contains these non-secret identifiers. Do not add client secrets, account keys or access tokens to Git.
7. Run the workflow on **main**. GitHub issues a short-lived signed token; Azure checks the issuer, audience and subject, then issues an access token for the managed identity. Azure Storage separately checks the container role assignment. The uploader uses `--auth-mode login`.
8. Inspect the run: generation, login, upload and read-back verification should each succeed. A failed login may indicate an incorrect subject; a storage authorization failure may indicate role scope or propagation delay.

The trust and role assignment persist, but each run obtains temporary tokens. ADF's GitHub source-control connection is a separate integration and does not give GitHub Actions permission to Azure Storage.

## Automate after the platform is ready

Keep manual controls until testing is complete. To add daily delivery later, add a UTC `schedule` event to generate.yml and update BOTH login/upload `if` conditions to include scheduled events. scheduled_generate.py already defaults to UTC today and daily mode when manual inputs are absent. Keep workflow_dispatch so you can manually replay a date. Make the run summary handle absent manual inputs as well.

Choose a run time after the previous ADF ingestion/cleanup is finished. Upload overwrites unconditionally; it will not wait for consumption. ADF event triggering on `_SUCCESS` is appropriate only once the pipeline reads the batch date from manifest.json and validates the files. Replacing files is not an atomic folder transaction. For stronger guarantees later, coordinate the jobs rather than assuming a marker locks files.

To stop: cancel an active GitHub run. To prevent future starts: disable the workflow; cancel an existing run separately. Disable the ADF trigger separately if you also want ingestion stopped. No daily schedule has been enabled here.

References: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure and https://github.com/Azure/login
