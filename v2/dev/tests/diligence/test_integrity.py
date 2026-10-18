"""Behavioral integrity tests; no providers, services, datasets or training."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'v2/dev'))
from diligence.core import (MAX_DOCUMENT, SOURCE_REVISION, EvidencePin, HistoricalExport,
                           Rejected, bounded_read, canonical, local_file, pointer,
                           relative_name, sha, strict_json, validate_claims,
                           validate_ledger, verify_manifest)
from diligence import cli
from diligence.capsule import MissingEnvironment, verify_capsule


class ParserAndPins(unittest.TestCase):
    def test_strict_json_rejects_corrupt_forms(self):
        cases = [b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":Infinity}',
                 b'{"x":1e999}', b'{', b'\xff', b' ' * (MAX_DOCUMENT + 1)]
        for raw in cases:
            with self.subTest(raw_length=len(raw)), self.assertRaises(Rejected):
                strict_json(raw)

    def test_canonical_json_finite_and_stable(self):
        self.assertEqual(canonical({'b':2,'a':1}), canonical({'a':1,'b':2}))
        with self.assertRaises(ValueError): canonical({'x':float('nan')})

    def test_paths_are_fixed_relative_files(self):
        for path in ['../x','a/../x','/absolute','a\\b','a//b','a/./b','x:y','']:
            with self.subTest(path=path), self.assertRaises(Rejected): relative_name(path)
        self.assertEqual(relative_name('evidence/result.json'),'evidence/result.json')

    def test_linked_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'file').write_text('x'); (root/'linked').symlink_to(root/'file')
            with self.assertRaises(Rejected): local_file(root,'linked')
            with self.assertRaises(Rejected): local_file(root,'../outside')

    def test_bounded_read_missing_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x'
            with self.assertRaises(Rejected): bounded_read(p)
            p.write_bytes(b'x'*(MAX_DOCUMENT+1))
            with self.assertRaises(Rejected): bounded_read(p)

    def test_pin_closed_fields_and_digest_types(self):
        for obj in [{'path':'a','sha256':'bad','bytes':1},
                    {'path':'a','sha256':'0'*64,'bytes':True},
                    {'path':'a','sha256':'0'*64,'bytes':-1},
                    {'path':'a','sha256':'0'*64,'bytes':1,'extra':0}]:
            with self.subTest(obj=obj), self.assertRaises(Rejected):EvidencePin.parse(obj)

    def test_declared_identity_and_crlf_export(self):
        raw=b'{"ok":true}\n';pin=EvidencePin('a.json',sha(raw),len(raw))
        self.assertEqual(HistoricalExport(pin,'identity',sha(raw)).reconstruct(raw),raw)
        expected=raw.replace(b'\n',b'\r\n')
        self.assertEqual(HistoricalExport(pin,'lf-to-crlf-v1',sha(expected)).reconstruct(raw),expected)

    def test_corrupt_source_and_historical_hash_reject(self):
        raw=b'{"ok":true}\n';pin=EvidencePin('a.json',sha(raw),len(raw))
        for value in [b'{"ok":false}',raw+b' ',raw.replace(b'true',b'fail')]:
            with self.assertRaises(Rejected):HistoricalExport(pin,'identity',sha(raw)).reconstruct(value)
        with self.assertRaises(Rejected):HistoricalExport(pin,'identity','0'*64).reconstruct(raw)
        with self.assertRaises(Rejected):HistoricalExport(pin,'normalize-json',sha(raw)).reconstruct(raw)

    def test_mixed_or_already_crlf_cannot_be_transformed(self):
        for raw in [b'first\r\nsecond\n',b'one\rtwo\n',b'one\r\n',b'no newline',b'\xff\n']:
            pin=EvidencePin('a',sha(raw),len(raw))
            with self.subTest(raw=raw), self.assertRaises(Rejected):
                HistoricalExport(pin,'lf-to-crlf-v1',sha(raw.replace(b'\n',b'\r\n'))).reconstruct(raw)

    def test_pointer_missing_escaped_keys_and_lists(self):
        self.assertEqual(pointer({'a/b':{'~':[3]}},'/a~1b/~0/0'),3)
        self.assertEqual(pointer({'a':1},''),{'a':1})
        for value,key in [({},'/missing'),({'a':[]},'/a/1'),({},'wrong')]:
            with self.assertRaises(Rejected):pointer(value,key)


class ClaimsAndTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=strict_json((cli.DOCS/'claims.json').read_bytes())
        cls.ledger=strict_json((cli.DOCS/'task_ledger.json').read_bytes())

    def source(self,name):return cli.git_source(name)

    def test_exact_claims_and_full_matrix(self):
        self.assertEqual(validate_claims(self.registry,self.source),26)

    def test_duplicate_unknown_or_omitted_claim_rejects(self):
        for kind in ['duplicate','missing','unknown']:
            r=copy.deepcopy(self.registry)
            if kind=='duplicate':r['claims'].append(copy.deepcopy(r['claims'][0]))
            if kind=='missing':r['claims'].pop()
            if kind=='unknown':r['claims'][0]['id']='invented'
            with self.subTest(kind=kind),self.assertRaises(Rejected):validate_claims(r,self.source)

    def test_rounded_value_cannot_replace_source_precision(self):
        r=copy.deepcopy(self.registry);c=next(c for c in r['claims'] if c['id']=='METRIC-RF-RAW')
        c['metrics'][0]['value']=round(c['metrics'][0]['value'],3)
        with self.assertRaises(Rejected):validate_claims(r,self.source)

    def test_bad_selector_unit_or_metric_source_rejects(self):
        for kind in ['selector','unit','source']:
            r=copy.deepcopy(self.registry);m=next(c for c in r['claims'] if c['metrics'])['metrics'][0]
            if kind=='selector':m['selector']='/not_present'
            if kind=='unit':m['unit']=''
            if kind=='source':m['source_path']='unbound.json'
            with self.subTest(kind=kind),self.assertRaises(Rejected):validate_claims(r,self.source)

    def test_qualitative_or_future_cannot_be_promoted(self):
        for kind in ['numeric','fresh','approved','future']:
            r=copy.deepcopy(self.registry)
            if kind=='numeric':r['claims'][0]['metrics']=copy.deepcopy(next(c for c in r['claims'] if c['metrics'])['metrics'])
            if kind=='fresh':r['claims'][2]['verification_status']='fresh_execution'
            if kind=='approved':r['claims'][0]['editorial_status']='approved'
            if kind=='future':r['claims'][-1]['verification_status']='inspected'
            with self.subTest(kind=kind),self.assertRaises(Rejected):validate_claims(r,self.source)

    def test_mandatory_qualifier_cannot_be_dropped(self):
        r=copy.deepcopy(self.registry);r['claims'][0]['mandatory_qualifiers']=[]
        with self.assertRaises(Rejected):validate_claims(r,self.source)

    def test_task_dag_valid(self):
        self.assertEqual(validate_ledger(self.ledger,ROOT)['tasks'],93)

    def test_task_cycle_unknown_dependency_duplicate_rejects(self):
        for kind in ['cycle','unknown','duplicate','no_evidence','unmet']:
            r=copy.deepcopy(self.ledger)
            if kind=='cycle':r['tasks'][0]['dependencies']=[r['tasks'][1]['id']]
            if kind=='unknown':r['tasks'][0]['dependencies']=['DD-999']
            if kind=='duplicate':r['tasks'].append(copy.deepcopy(r['tasks'][0]))
            if kind=='no_evidence':r['tasks'][0]['status']='verified';r['tasks'][0]['evidence']=[]
            if kind=='unmet':
                r['tasks'][9]['status']='verified';r['tasks'][9]['evidence']=['README.md']
                r['tasks'][8]['status']='planned'
            with self.subTest(kind=kind),self.assertRaises(Rejected):validate_ledger(r,ROOT)


class CapsuleIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='amphora-integrity-test-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.capsule=self.root/'capsule';cli.build_capsule(self.capsule)

    def test_original_twelve_gates_and_science_offline(self):
        r=verify_capsule(self.capsule)
        self.assertEqual(len(r['historical_evidence']['gates']),12)
        self.assertEqual(r['plga']['stage2_result_cells'],12)
        self.assertFalse(r['services_started']);self.assertEqual(r['provider_calls'],0)
        self.assertFalse(r['investor_release_qualified'])
        self.assertEqual(r['source_boundary_check'],'not_rerun_in_capsule')

    def test_standalone_checkout_free_command(self):
        result=subprocess.run([sys.executable,'-B',str(self.capsule/'verify.py')],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertEqual(json.loads(result.stdout)['status'],'verified')

    def test_mutated_source_and_delivered_extra_file_reject(self):
        p=self.capsule/'claims.json';original=p.read_bytes();p.write_bytes(original+b' ')
        with self.assertRaises(Rejected):verify_capsule(self.capsule)
        p.write_bytes(original);(self.capsule/'unreviewed.txt').write_text('extra')
        with self.assertRaises(Rejected):verify_capsule(self.capsule)

    def test_manifest_self_hash_and_duplicate_members_reject(self):
        p=self.capsule/'MANIFEST.json';m=strict_json(p.read_bytes());m['files'].append(copy.deepcopy(m['files'][0]));p.write_bytes(canonical(m))
        with self.assertRaises(Rejected):verify_manifest(self.capsule)

    def test_requested_missing_numpy_is_explicit(self):
        with patch('diligence.capsule.importlib.util.find_spec',return_value=None):
            with self.assertRaises(MissingEnvironment):verify_capsule(self.capsule,True)

    def test_changed_mapping_gate_set_rejects_even_with_new_payload_hash(self):
        p=self.capsule/'byte_reconstruction.v1.json';m=strict_json(p.read_bytes());m['entries'].pop();p.write_bytes(canonical(m))
        self.repin_payload_for_structural_test('byte_reconstruction.v1.json')
        with self.assertRaisesRegex(Rejected,'required_gate_set_mismatch'):verify_capsule(self.capsule)

    def test_changed_frozen_scope_rejected_by_unchanged_original_checker(self):
        # Test original semantic assertions separately from the wrapper's hash gate.
        sys.path.insert(0,str(ROOT/'v2/deploy/local/src'))
        from amphora_deployment.acceptance.ledger import AcceptanceLedger
        mapping=strict_json((cli.DOCS/'byte_reconstruction.v1.json').read_bytes())
        directory=self.root/'semantic';directory.mkdir();ledger_raw=cli.git_source(mapping['ledger']['path']);ledger=strict_json(ledger_raw)
        for row in mapping['entries']:
            pin=EvidencePin.parse(row['source']);b=HistoricalExport(pin,row['transform'],row['historical_sha256']).reconstruct(cli.git_source(pin.path))
            if row['gate']=='live_context':
                obj=strict_json(b);obj['restart']['additional_model_calls']=1;b=canonical(obj);ledger['evidence'][row['gate']]=sha(b)
            (directory/row['output_name']).write_bytes(b)
        result=AcceptanceLedger.from_bytes(canonical(ledger)).verify(directory)
        self.assertEqual(result['status'],'rejected')
        self.assertTrue(any(r.get('reason')=='required_assertion_failed' for r in result['gates']))

    def test_two_deterministic_archives_match(self):
        other=self.root/'other';cli.build_capsule(other)
        a=self.root/'a.zip';b=self.root/'b.zip'
        self.assertEqual(cli.archive_capsule(self.capsule,a)['archive_sha256'],cli.archive_capsule(other,b)['archive_sha256'])

    def test_existing_or_internal_output_rejected(self):
        with self.assertRaises(Rejected):cli.build_capsule(self.capsule)
        with self.assertRaises(Rejected):cli.build_capsule(ROOT/'new-capsule')

    def test_capsule_linked_file_rejected(self):
        (self.capsule/'bad').symlink_to(self.capsule/'claims.json')
        with self.assertRaises(Rejected):verify_capsule(self.capsule)

    def repin_payload_for_structural_test(self,name):
        # A deliberate test oracle for downstream schema failures, never release behavior.
        p=self.capsule/'MANIFEST.json';m=strict_json(p.read_bytes())
        for row in m['files']:
            if row['path']==name:b=(self.capsule/name).read_bytes();row.update(bytes=len(b),sha256=sha(b))
        p.write_bytes(canonical(m));(self.capsule/'MANIFEST.sha256').write_text(sha(p.read_bytes())+'\n')


if __name__=='__main__':unittest.main()
