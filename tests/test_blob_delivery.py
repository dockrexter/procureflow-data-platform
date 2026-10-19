import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_generator import g, C, D
sys.path.insert(0, str(Path(__file__).parents[1]/'scripts'))
import landing
import run_adf

class FakeAzure:
    def __init__(self):self.blobs={};self.uploads=[];self.fail_name=None
    def __call__(self,*args):
        value=lambda key:args[args.index(key)+1]
        assert value('--auth-mode')=='login'
        assert value('--container-name')=='outbound'
        name=value('--name')
        if args[2]=='exists':return json.dumps({'exists':name in self.blobs})
        if args[2]=='download':Path(value('--file')).write_bytes(self.blobs[name]);return ''
        if args[2]=='upload':
            if name.endswith(self.fail_name or '\0'):raise RuntimeError('simulated outage')
            assert value('--overwrite')=='false'
            self.blobs[name]=Path(value('--file')).read_bytes();self.uploads.append(name);return ''
        raise AssertionError(args)

class BlobDeliveryTests(unittest.TestCase):
    def test_publish_retry_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',tmp);fake=FakeAzure()
            with patch.object(landing,'az',fake):
                landing.land(batch,account='sourcesample',container='outbound')
                self.assertTrue(fake.uploads[-1].endswith('/_SUCCESS'))
                count=len(fake.uploads)
                landing.land(batch,account='sourcesample',container='outbound')
                self.assertEqual(count,len(fake.uploads))
                fake.blobs['SAP_S4HANA/'+D.isoformat()+'/payments.csv']=b'conflict'
                with self.assertRaises(ValueError):landing.land(batch,account='sourcesample',container='outbound')
                self.assertEqual(count,len(fake.uploads))
    def test_outage_leaves_no_success_then_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',tmp);fake=FakeAzure();fake.fail_name='payments.csv'
            with patch.object(landing,'az',fake):
                with self.assertRaises(RuntimeError):landing.land(batch,account='sourcesample',container='outbound')
                self.assertFalse(any(k.endswith('/_SUCCESS') for k in fake.blobs))
                fake.fail_name=None
                landing.land(batch,account='sourcesample',container='outbound')
                self.assertTrue(fake.uploads[-1].endswith('/_SUCCESS'))
    def test_adf_uses_manifest_date_and_reports_failure(self):
        env={'AZURE_SUBSCRIPTION_ID':'sub','AZURE_RESOURCE_GROUP':'rg','ADF_FACTORY':'adf',
             'SOURCE_STORAGE_ACCOUNT':'source','LANDING_STORAGE_ACCOUNT':'lake'}
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,env):
            batch=g.write_batch(C,D,'bootstrap',tmp)
            def reply(args,**kwargs):
                if 'post' in args:
                    params=json.loads(Path(args[args.index('--body')+1][1:]).read_text())
                    self.assertEqual(params,{'source':'SAP_S4HANA','batchDate':D.isoformat(),'sourceAccount':'source','account':'lake'})
                    return json.dumps({'runId':'run-1'})
                return json.dumps({'status':'Succeeded'})
            with patch.object(run_adf.subprocess,'check_output',side_effect=reply):
                self.assertEqual(run_adf.run(batch),'run-1')
            with patch.object(run_adf.subprocess,'check_output',side_effect=['{"runId":"run-2"}','{"status":"Failed"}']):
                with self.assertRaises(RuntimeError):run_adf.run(batch)
