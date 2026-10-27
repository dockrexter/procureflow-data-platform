import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from test_generator import g, C, D
sys.path.insert(0, str(Path(__file__).parents[1]/'scripts'))
import publish_blob

class FakeAzure:
    def __init__(self):self.blobs={};self.uploads=[];self.fail_name=None
    def __call__(self,*args):
        value=lambda key:args[args.index(key)+1]
        assert value('--auth-mode')=='login'
        assert value('--container-name')=='outbound'
        if args[2]=='list':return json.dumps([n for n in self.blobs if n.startswith(value('--prefix'))])
        name=value('--name')
        if args[2]=='delete':self.blobs.pop(name,None);return ''
        if args[2]=='exists':return json.dumps({'exists':name in self.blobs})
        if args[2]=='download':Path(value('--file')).write_bytes(self.blobs[name]);return ''
        if args[2]=='upload':
            if name.endswith(self.fail_name or '\0'):raise RuntimeError('simulated outage')
            assert value('--overwrite')=='true'
            self.blobs[name]=Path(value('--file')).read_bytes();self.uploads.append(name);return ''
        raise AssertionError(args)

class BlobDeliveryTests(unittest.TestCase):
    def test_replace_and_remove_old_layout_without_touching_other_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',tmp);fake=FakeAzure()
            fake.blobs={'SAP_S4HANA/2026-10-19/old.csv':b'old','OTHER/file.csv':b'keep'}
            with patch.object(publish_blob,'az',fake):
                publish_blob.publish(batch,account='sourcesample')
                daily=g.write_batch(C,D+timedelta(days=1),'daily',tmp)
                publish_blob.publish(daily,account='sourcesample')
                self.assertEqual(fake.blobs['SAP_S4HANA/payments.csv'],(daily/'payments.csv').read_bytes())
                self.assertEqual(fake.blobs['OTHER/file.csv'],b'keep')
                self.assertFalse(any(n.count('/')>1 for n in fake.blobs if n.startswith('SAP_S4HANA/')))
                self.assertTrue(fake.uploads[-1].endswith('/_SUCCESS'))
    def test_outage_leaves_no_success_then_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',tmp);fake=FakeAzure();fake.blobs['SAP_S4HANA/_SUCCESS']=b'old';fake.fail_name='payments.csv'
            with patch.object(publish_blob,'az',fake):
                with self.assertRaises(RuntimeError):publish_blob.publish(batch,account='sourcesample')
                self.assertFalse(any(k.endswith('/_SUCCESS') for k in fake.blobs))
                fake.fail_name=None
                publish_blob.publish(batch,account='sourcesample')
                self.assertTrue(fake.uploads[-1].endswith('/_SUCCESS'))

    def test_corrupt_batch_is_rejected_before_any_azure_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch = g.write_batch(C, D, 'bootstrap', tmp)
            (batch / 'payments.csv').write_text('corrupt')
            with patch.object(publish_blob, 'az') as azure:
                with self.assertRaises(ValueError):
                    publish_blob.publish(batch, account='sourcesample')
                azure.assert_not_called()
