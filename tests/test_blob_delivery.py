import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from test_generator import g, C, D
sys.path.insert(0, str(Path(__file__).parents[1]/'scripts'))
import landing

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
            with patch.object(landing,'az',fake):
                landing.land(batch,account='sourcesample',container='outbound')
                daily=g.write_batch(C,D+timedelta(days=1),'daily',tmp)
                landing.land(daily,account='sourcesample',container='outbound')
                self.assertEqual(fake.blobs['SAP_S4HANA/payments.csv'],(daily/'payments.csv').read_bytes())
                self.assertEqual(fake.blobs['OTHER/file.csv'],b'keep')
                self.assertFalse(any(n.count('/')>1 for n in fake.blobs if n.startswith('SAP_S4HANA/')))
                self.assertTrue(fake.uploads[-1].endswith('/_SUCCESS'))
    def test_outage_leaves_no_success_then_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',tmp);fake=FakeAzure();fake.blobs['SAP_S4HANA/_SUCCESS']=b'old';fake.fail_name='payments.csv'
            with patch.object(landing,'az',fake):
                with self.assertRaises(RuntimeError):landing.land(batch,account='sourcesample',container='outbound')
                self.assertFalse(any(k.endswith('/_SUCCESS') for k in fake.blobs))
                fake.fail_name=None
                landing.land(batch,account='sourcesample',container='outbound')
                self.assertTrue(fake.uploads[-1].endswith('/_SUCCESS'))
