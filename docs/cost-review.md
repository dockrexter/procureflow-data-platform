# Azure trial cost review — 2026-10-19

Observed in the signed-in Azure portal before provisioning: the selected trial subscription is active, user is Owner, the portal notification shows EUR 175.99 credit remaining; subscription overview shows USD 200 remaining with 29 days to expiry, current cost 0.00 and no active resource usage. These are portal displays in different currencies, not a calculated conversion. The account also has another subscription with the same display name; deployment must use the explicit selected trial subscription ID locally.

Cloud Shell read-only subscription API also confirmed FreeTrial_2014-09-01, state Enabled, spendingLimit On. The spending-limit API check must be repeated before a later deploy. Trial credit is finite and billing data can lag. Do not upgrade the subscription or remove its spending limit for this sprint.

Exposure by component:
- Resource group: organizational container.
- ADLS Standard LRS: stored bytes, storage operations and applicable transfer are metered. Public blob access, shared keys and native storage SFTP are disabled. The authenticated network endpoint is public for this learning environment; production should use private networking.
- ADF: copy activity/orchestration and integration runtime use are metered. No trigger or mapping-data-flow session is activated.
- Databricks: workspace definition is optional and off by default. No cluster, SQL warehouse, serverless task or scheduled job is started. Running the bundle later incurs compute charges.
- SFTP: localhost container only; there is no Azure SFTP hourly endpoint or cloud VM in the default deployment.
- GitHub private Actions: subject to the account's included minutes/storage and billing settings. Artifacts expire after 30 days; no unlimited retention is implied.

There is no guaranteed zero-cost promise and no fixed monetary estimate without region-specific meters and verified runtime quantities. Budgets notify and do not act as a hard spending cap. The trial spending limit protects most covered usage, but not every Marketplace purchase; no Marketplace products are needed here.

References checked:
- https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/spending-limit
- https://azure.microsoft.com/en-us/pricing/free-trial/
- https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
- https://azure.microsoft.com/en-us/pricing/details/data-factory/data-pipeline/
- https://azure.microsoft.com/en-us/pricing/details/databricks/
