import importlib.util
from pathlib import Path
import tempfile
import unittest
from test_generator import g,C,D
spec=importlib.util.spec_from_file_location('landing',Path(__file__).parents[1]/'scripts/landing.py')
l=importlib.util.module_from_spec(spec);spec.loader.exec_module(l)
class LandingTests(unittest.TestCase):
    def test_round_trip_idempotence_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=g.write_batch(C,D,'bootstrap',Path(tmp)/'out')
            dst=l.land(src,Path(tmp)/'landing')
            self.assertEqual(dst,l.land(src,Path(tmp)/'landing'))
            self.assertEqual(l.verify(src),l.verify(dst))
            (Path(dst)/'payments.csv').write_text('corrupt')
            with self.assertRaises(ValueError):l.land(src,Path(tmp)/'landing')
    def test_corrupt_or_incomplete_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=g.write_batch(C,D,'bootstrap',Path(tmp)/'out')
            (src/'po_items.csv').write_text('broken')
            with self.assertRaises(ValueError):l.land(src,Path(tmp)/'landing')
            self.assertFalse((Path(tmp)/'landing').exists())
    def test_missing_success_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=g.write_batch(C,D,'bootstrap',tmp);(src/'_SUCCESS').unlink()
            with self.assertRaises(FileNotFoundError):l.verify(src)
