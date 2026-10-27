import copy
import hashlib
import importlib.util
import json
from datetime import date,timedelta
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('generate',Path(__file__).parents[1]/'data-generator/generate.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
C={'source':'SAP_S4HANA','seed':42,'epoch':'2026-10-19','history_days':40,'bootstrap_pos':120,'daily_pos':5,'suppliers':20,'materials':50}
D=date.fromisoformat(C['epoch'])
class GeneratorTests(unittest.TestCase):
    def test_reproducible_bytes(self):
        self.assertEqual(g.build_files(C,D,'bootstrap'),g.build_files(C,D,'bootstrap'))
        changed=dict(C,seed=43)
        self.assertNotEqual(g.build_files(C,D,'bootstrap'),g.build_files(changed,D,'bootstrap'))
    def test_daily_union_equals_snapshot_and_cross_batch_references(self):
        total=g.batch(C,D,'bootstrap')
        old={r['EBELN'] for r in total['po_headers']}
        for offset in range(1,41):
            daily=g.batch(C,D+timedelta(days=offset),'daily')
            if offset==1:
                self.assertTrue(any(r['EBELN'] in old for r in daily['goods_receipts']))
            for t,rows in daily.items(): total[t].extend(rows)
        g.validate(total)
        expected=g.snapshot(C,D+timedelta(days=40))
        for t in total:
            self.assertEqual(sorted(total[t],key=lambda r:json.dumps(r,sort_keys=True)), sorted(expected[t],key=lambda r:json.dumps(r,sort_keys=True)),t)
    def test_integrity_and_corruption(self):
        t=g.snapshot(C,D)
        g.validate(t)
        for table,field,value in [('po_items','NETWR','0.01'),('invoice_headers','RMWWR','0.01'),('payments','WRBTR','999999999.00'),('goods_receipts','MENGE','999999')]:
            bad=copy.deepcopy(t); bad[table][0][field]=value
            with self.subTest(table=table),self.assertRaises(ValueError):g.validate(bad)
    def test_duplicate_or_missing_history_rejected(self):
        t=g.snapshot(C,D);t['suppliers'].append(t['suppliers'][0])
        with self.assertRaises(ValueError):g.validate(t)
        t=g.snapshot(C,D);t['po_history'].pop()
        with self.assertRaises(ValueError):g.validate(t)
    def test_atomic_idempotent_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=g.write_batch(C,D,'bootstrap',tmp)
            self.assertEqual(p,g.write_batch(C,D,'bootstrap',tmp))
            (p/'payments.csv').write_text('corrupt')
            with self.assertRaises(ValueError):g.write_batch(C,D,'bootstrap',tmp)
    def test_manifest_checksums(self):
        files=g.build_files(C,D,'bootstrap');m=json.loads(files['manifest.json'])
        for f,meta in m['files'].items():self.assertEqual(meta['sha256'],hashlib.sha256(files[f]).hexdigest())
        self.assertEqual(files['_SUCCESS'].decode().strip(),hashlib.sha256(files['manifest.json']).hexdigest())
    def test_date_guards(self):
        for mode,day in [('bootstrap',D+timedelta(days=1)),('daily',D),('daily',D-timedelta(days=1))]:
            with self.subTest(mode=mode,day=day),self.assertRaises(ValueError):g.batch(C,day,mode)
    def test_source_config_selects_mode_from_its_own_epoch(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = dict(C, source='SAP_S4HANA', epoch='2026-10-25')
            Path(tmp, 'sap_s4hana.json').write_text(json.dumps(config))
            selected, mode = g.source_config('SAP_S4HANA', date(2026,10,25), tmp)
            self.assertEqual(selected, config)
            self.assertEqual(mode, 'bootstrap')
            self.assertEqual(g.source_config('SAP_S4HANA', date(2026,10,26), tmp)[1], 'daily')
            with self.assertRaises(ValueError):
                g.source_config('SAP_S4HANA', date(2026,10,24), tmp)

    def test_source_config_rejects_unknown_unsafe_and_mismatched_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ['UNKNOWN', '../SAP_S4HANA', 'SAP/S4HANA', 'sap_s4hana']:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    g.source_config(name, D, tmp)
            Path(tmp, 'sap_test.json').write_text(json.dumps(C))
            with self.assertRaises(ValueError):
                g.source_config('SAP_TEST', D, tmp)

if __name__=='__main__':unittest.main()
