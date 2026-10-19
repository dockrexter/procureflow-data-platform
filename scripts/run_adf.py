"""Run and monitor ADF after source publication, using the batch manifest's date."""
import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote
from landing import verify


def run(batch, timeout=1800):
    manifest=verify(batch)
    env=lambda key: quote(os.environ[key],safe='')
    base=(f"https://management.azure.com/subscriptions/{env('AZURE_SUBSCRIPTION_ID')}"
          f"/resourceGroups/{env('AZURE_RESOURCE_GROUP')}/providers/Microsoft.DataFactory"
          f"/factories/{env('ADF_FACTORY')}")
    params={'source':manifest['source'],'batchDate':manifest['batch_date'],
            'sourceAccount':os.environ['SOURCE_STORAGE_ACCOUNT'],
            'account':os.environ['LANDING_STORAGE_ACCOUNT']}
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'parameters.json';path.write_text(json.dumps(params))
        result=json.loads(subprocess.check_output(['az','rest','--method','post','--url',
            base+'/pipelines/pl_blob_to_landing/createRun?api-version=2018-06-01',
            '--body','@'+str(path)],text=True))
    run_id=result['runId'];print('ADF run:',run_id,flush=True)
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        result=json.loads(subprocess.check_output(['az','rest','--method','get','--url',
            base+'/pipelineruns/'+quote(run_id,safe='')+'?api-version=2018-06-01'],text=True))
        status=result['status']
        if status=='Succeeded':return run_id
        if status in ['Failed','Cancelled']:raise RuntimeError(f'ADF {status}: {run_id}')
        time.sleep(15)
    raise TimeoutError(f'ADF still running; inspect {run_id} before retrying')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');a=p.parse_args();run(a.batch)
