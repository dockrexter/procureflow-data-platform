"""Read-only deployment gate. Never upgrades subscriptions or removes limits."""
import argparse
import json
import subprocess
p=argparse.ArgumentParser();p.add_argument('--subscription',required=True);a=p.parse_args()
url=f'https://management.azure.com/subscriptions/{a.subscription}?api-version=2022-12-01'
r=json.loads(subprocess.check_output(['az','rest','--method','get','--url',url],text=True))
result={'subscriptionId':r['subscriptionId'],'state':r['state'],'spendingLimit':r.get('subscriptionPolicies',{}).get('spendingLimit','Unknown')}
print(json.dumps(result,indent=2))
if result['state']!='Enabled' or result['spendingLimit']!='On':
    raise SystemExit('STOP: enabled trial spending protection was not confirmed; review billing before provisioning.')
print('Trial spending-limit check passed. Confirm remaining credit and expiry in the portal before deploying.')
