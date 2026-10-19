import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from test_generator import g,C,D
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from publish_sftp import publish
class FakeSftp:
    def __init__(self,root):self.root=Path(root);(self.root/'outbound').mkdir()
    def path(self,p):return self.root/p.lstrip('/')
    def stat(self,p):return self.path(p).stat()
    def mkdir(self,p):self.path(p).mkdir()
    def listdir(self,p):return [f.name for f in self.path(p).iterdir()]
    def open(self,p,m):return self.path(p).open(m)
    def put(self,s,d,confirm):shutil.copyfile(s,self.path(d))
    def rename(self,s,d):self.path(s).rename(self.path(d))
class SftpTests(unittest.TestCase):
    def test_atomic_publication_retry_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',Path(tmp)/'local')
            remote=Path(tmp)/'remote';remote.mkdir();client=FakeSftp(remote)
            target=publish(client,batch)
            self.assertEqual(target,publish(client,batch))
            self.assertTrue((client.path(target)/'_SUCCESS').exists())
            (client.path(target)/'payments.csv').write_text('bad')
            with self.assertRaises(ValueError):publish(client,batch)
    def test_failed_transfer_never_exposes_completed_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch=g.write_batch(C,D,'bootstrap',Path(tmp)/'local')
            remote=Path(tmp)/'remote';remote.mkdir();client=FakeSftp(remote)
            def fail(*args,**kwargs):raise OSError('simulated connection loss')
            client.put=fail
            with self.assertRaises(OSError):publish(client,batch)
            self.assertFalse(client.path('/outbound/SAP_S4HANA/'+D.isoformat()).exists())
