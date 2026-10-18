"""Reproduce consequential V1 failures and require V2 to reject them."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'v2/dev'))
from diligence import cli
from diligence.core import (Rejected, canonical, pointer, sha, strict_json,
                            validate_claims, validate_ledger)
from diligence.capsule import MissingEnvironment, run_checker, verify_capsule
from diligence.decisions import check_decisions
from diligence.publication import INTEGRATION, QUALIFIER, scientific_card, check_document
import test_integrity as legacy_tests


class RedTeamCapsule(unittest.TestCase):
    setUp = legacy_tests.CapsuleIntegration.setUp
    repin_payload_for_structural_test = legacy_tests.CapsuleIntegration.repin_payload_for_structural_test

    def test_coordinated_fake_checker_and_rehashed_policy_rejects(self):
        p=self.capsule/'checker/acceptance/__main__.py'
        raw=b'import json\nprint(json.dumps({"status":"verified","gates":[{"gate":"fake"}]*12}))\n';p.write_bytes(raw)
        mapping=self.capsule/'byte_reconstruction.v1.json';value=strict_json(mapping.read_bytes())
        for row in value['checker_sources']:
            if row['capsule_path']=='checker/acceptance/__main__.py':row['source'].update(sha256=sha(raw),bytes=len(raw))
        mapping.write_bytes(canonical(value));self.repin_payload_for_structural_test('checker/acceptance/__main__.py');self.repin_payload_for_structural_test('byte_reconstruction.v1.json')
        with self.assertRaisesRegex(Rejected,'reviewed_policy_mismatch'):verify_capsule(self.capsule)

    def test_extra_member_cannot_be_laundered_with_manifest_rehash(self):
        p=self.capsule/'unexpected.py';p.write_text('raise RuntimeError("unreviewed")\n')
        manifest=self.capsule/'MANIFEST.json';value=strict_json(manifest.read_bytes());value['files'].append({'path':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size});manifest.write_bytes(canonical(value));(self.capsule/'MANIFEST.sha256').write_text(sha(manifest.read_bytes())+'\n')
        with self.assertRaisesRegex(Rejected,'reviewed_allowlist_mismatch'):verify_capsule(self.capsule)

    def test_external_manifest_anchor_and_isolated_entrypoint(self):
        digest=sha((self.capsule/'MANIFEST.json').read_bytes())
        r=subprocess.run([sys.executable,'-I','-B',str(self.capsule/'verify.py'),'--expected-manifest-sha256',digest],capture_output=True,text=True,cwd=self.root)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertTrue(json.loads(r.stdout)['external_manifest_pin_checked'])
        with self.assertRaisesRegex(Rejected,'external_manifest_pin_mismatch'):verify_capsule(self.capsule,expected_manifest='0'*64)

    def test_source_profile_runs_capsule_once_and_reports_scope(self):
        with patch('diligence.cli.verify_capsule',wraps=verify_capsule) as verify,redirect_stdout(io.StringIO()) as output:
            code=cli.main(['verify-source'])
        self.assertEqual(code,0,output.getvalue());self.assertEqual(verify.call_count,1)
        report=json.loads(output.getvalue());self.assertIn('source_static_dependency_guard',report['checks_executed'])
        self.assertIn('current installed-owner recovery',report['not_executed'])

    def test_source_output_ancestor_alias_into_checkout_rejects(self):
        alias=self.root/'alias';alias.symlink_to(ROOT,target_is_directory=True)
        with self.assertRaisesRegex(Rejected,'external_output_required'):cli.build_capsule(alias/'new-output')

    def test_requested_missing_dependency_returns_exit_three(self):
        with patch('diligence.cli.verify_capsule',side_effect=MissingEnvironment('requested_numpy_unavailable')),redirect_stdout(io.StringIO()) as output:
            code=cli.main(['verify-source','--bootstrap'])
        self.assertEqual(code,3);self.assertEqual(json.loads(output.getvalue())['status'],'environment_unavailable')


class RedTeamValidation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='amphora-v2-validation-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def test_checker_output_flood_is_bounded(self):
        with self.assertRaisesRegex(Rejected,'checker_output_limit'):
            run_checker([sys.executable,'-I','-c','import sys;sys.stdout.write("x"*200000)'],cwd=self.root)

    def test_checker_timeout_is_rejection(self):
        with self.assertRaisesRegex(Rejected,'checker_timeout'):
            run_checker([sys.executable,'-I','-c','import time;time.sleep(3)'],cwd=self.root,timeout=.05)

    def test_leading_garbage_is_not_ignored(self):
        with self.assertRaises(Rejected):run_checker([sys.executable,'-I','-c','print("garbage");print(\'{"status":"verified"}\')'],cwd=self.root)

    def test_pointer_negative_index_and_bad_escape_reject(self):
        for selector in ['/-1','/+0','/00','/~2']:
            with self.subTest(selector=selector),self.assertRaises(Rejected):pointer([1],selector)

    def test_claim_null_shape_rejects_cleanly(self):
        value=json.loads((cli.DOCS/'claims.json').read_text());value['claims']=None
        with self.assertRaises(Rejected):validate_claims(value,cli.git_source)

    def test_role_approval_cannot_be_backed_by_readme(self):
        value=json.loads((cli.DOCS/'task_ledger.json').read_text());task=next(t for t in value['tasks'] if t['id']=='DD-010');task.update(status='verified',evidence=['README.md'])
        with self.assertRaisesRegex(Rejected,'role_approval_not_established'):validate_ledger(value,ROOT)

    def test_qualified_preparation_still_requires_verified_dependency(self):
        value=json.loads((cli.DOCS/'task_ledger.json').read_text());value['tasks'][0]['status']='planned'
        with self.assertRaisesRegex(Rejected,'unmet_verified_dependency'):validate_ledger(value,ROOT)

    def test_any_existing_file_is_not_task_acceptance(self):
        value=json.loads((cli.DOCS/'task_ledger.json').read_text());value['tasks'][1]['evidence']=['README.md']
        with self.assertRaisesRegex(Rejected,'task_evidence_not_qualified'):validate_ledger(value,ROOT)

    def evidence_fixture(self):
        value=json.loads((cli.DOCS/'task_ledger.json').read_text())
        registry=json.loads((ROOT/value['evidence_registry']).read_text())
        for record in registry['records']:
            p=self.root/record['pin']['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/record['pin']['path'],p)
            for binding in record['code_bindings']:
                p=self.root/binding['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/binding['path'],p)
        return value,registry

    def test_failed_or_boolean_exit_receipt_cannot_qualify_task(self):
        for result,exit_code in [('FAIL',0),('PASS',False)]:
            value,registry=self.evidence_fixture();record=next(r for r in registry['records'] if 'DD-002' in r['supports'])
            p=self.root/record['pin']['path'];raw=canonical({'status':result,'exit_code':exit_code});p.write_bytes(raw);record['pin'].update(bytes=len(raw),sha256=sha(raw));record.update(kind='mechanical_check',result={'selector':'/status','expected':'PASS','exit_selector':'/exit_code'})
            registry_path=self.root/value['evidence_registry'];registry_path.parent.mkdir(parents=True,exist_ok=True);registry_path.write_bytes(canonical(registry))
            with self.subTest(result=result,exit_code=exit_code),self.assertRaisesRegex(Rejected,'task_receipt_failed'):validate_ledger(value,self.root)

    def test_stale_code_binding_rejects_a_passing_receipt(self):
        value,registry=self.evidence_fixture();record=next(r for r in registry['records'] if 'DD-002' in r['supports']);p=self.root/record['pin']['path'];raw=canonical({'status':'PASS','exit_code':0});p.write_bytes(raw);record['pin'].update(bytes=len(raw),sha256=sha(raw))
        code=self.root/'verifier.py';code.write_bytes(b'pass\n');record.update(kind='mechanical_check',result={'selector':'/status','expected':'PASS','exit_selector':'/exit_code'},code_bindings=[{'path':'verifier.py','bytes':5,'sha256':'0'*64}])
        p=self.root/value['evidence_registry'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical(registry))
        with self.assertRaisesRegex(Rejected,'source_hash_mismatch'):validate_ledger(value,self.root)

    def test_phase_membership_and_source_range_reject(self):
        for kind in ['membership','range','shape']:
            value=json.loads((cli.DOCS/'task_ledger.json').read_text())
            if kind=='membership':value['phases'][0]['tasks'].pop()
            if kind=='range':value['tasks'][0]['source_refs'][0]['end_line']=99999
            if kind=='shape':value['tasks']=None
            with self.subTest(kind=kind),self.assertRaises(Rejected):validate_ledger(value,ROOT)

    def test_decision_gate_cannot_be_declared_met(self):
        value=json.loads((cli.DOCS/'V2/investment_gates.json').read_text());value['gates'][0]['state']='met';p=self.root/'gates.json';p.write_bytes(canonical(value))
        with self.assertRaisesRegex(Rejected,'unqualified_gate_promotion'):check_decisions(p)

    def test_scientific_card_keeps_inference_and_integration_adjacent(self):
        source=json.loads((ROOT/'docs/review/plga/evidence/evidence_summary.json').read_text());card=scientific_card(source)
        self.assertIn(INTEGRATION,card);self.assertEqual(card.count(QUALIFIER),2)
        for learner in ['rf','lightgbm']:
            for value in source['stage2']['all_model_mae_pp'][learner].values():self.assertIn(f'{value:.3f}',card)
        self.assertIn('not a fixed-day assay schedule',card)

    def test_scientific_missing_cell_or_false_interpretation_rejects(self):
        for kind in ['cell','contrast','interpretation']:
            source=json.loads((ROOT/'docs/review/plga/evidence/evidence_summary.json').read_text())
            if kind=='cell':source['stage2']['all_model_mae_pp']['rf'].pop('raw')
            if kind=='contrast':source['stage2']['paired_contrasts'].pop()
            if kind=='interpretation':source['stage2']['paired_contrasts'][0]['conditional_ci95_pp']=[1,2]
            with self.subTest(kind=kind),self.assertRaises(Rejected):scientific_card(source)

    def test_document_freshness_checks_inputs_and_renderer(self):
        pdf=self.root/'review.pdf';pdf.write_bytes(b'%PDF-fixture');renderer=self.root/'renderer.py';renderer.write_bytes(b'pass\n');source=self.root/'source.json';source.write_bytes(b'{}')
        receipt=self.root/'render.json';record={'pdf_sha256':sha(pdf.read_bytes()),'renderer_sha256':sha(renderer.read_bytes()),'source_sha256':{'source.json':sha(source.read_bytes())}};receipt.write_bytes(canonical(record))
        self.assertEqual(check_document(self.root,pdf,receipt,renderer)['status'],'fresh')
        source.write_bytes(b'{"changed":true}')
        with self.assertRaisesRegex(Rejected,'stale_document_input'):check_document(self.root,pdf,receipt,renderer)
        source.write_bytes(b'{}');renderer.write_bytes(b'# changed\n')
        with self.assertRaisesRegex(Rejected,'stale_renderer'):check_document(self.root,pdf,receipt,renderer)


if __name__=='__main__':unittest.main()
