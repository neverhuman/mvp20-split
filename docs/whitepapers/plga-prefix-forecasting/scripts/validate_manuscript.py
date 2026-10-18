#!/usr/bin/env python3
"""Validate the manuscript/build/aggregate evidence without fitting models."""
import argparse,ast,hashlib,json,re,subprocess
from pathlib import Path

def validate(root):
    ledger=json.loads((root/'claim_ledger.json').read_text());tex=(root/'paper.tex').read_text();tables=(root/'tables.tex').read_text();bib=(root/'references.bib').read_text()
    assert ledger['eligible_formulations']==320 and ledger['eligible_observations']==4870 and ledger['suffix_targets']==3910
    assert ledger['eligible_publication_dois']==113 and ledger['largest_joint_component']==59
    assert ledger['stage2_outer_fold_sizes']==[43,83,93,48,53]
    assert ledger['stage2_fit_budget']['total_fits_including_replay']==1560
    assert ledger['model_fits_in_this_script']==0
    assert all(x['conditional_ci95_pp'][0]<=0<=x['conditional_ci95_pp'][1] and x['holm_adjusted_p']>=.05 for x in ledger['stage2_contrasts'])
    for learner,arms in ledger['stage2_metrics'].items():
        for arm,v in arms.items():assert f'{v:.3f}' in tables,(learner,arm)
    for x in ledger['stage2_contrasts']:
        assert all(f'{v:+.3f}' in tables for v in [x['difference_mae_pp'],*x['conditional_ci95_pp']])
    citations={k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',tex) for k in group.split(',')};entries=set(re.findall(r'@\w+\{([^,]+),',bib));assert citations==entries,(citations-entries,entries-citations)
    log=(root/'paper.log').read_text(errors='replace');bad=[x for x in log.splitlines() if 'Overfull' in x or ('undefined' in x.lower() and 'warning' in x.lower()) or 'Rerun to get cross-references' in x];assert not bad,bad
    blg=(root/'paper.blg').read_text(errors='replace');assert 'Warning--' not in blg and 'error message' not in blg.lower()
    info=subprocess.run(['pdfinfo',str(root/'paper.pdf')],capture_output=True,text=True,check=True).stdout;pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1));assert 6<=pages<=9 and re.search(r'^Author:\s+Jepson Taylor\s*$',info,re.M)
    pdftext=subprocess.run(['pdftotext','-layout',str(root/'paper.pdf'),'-'],capture_output=True,text=True,check=True).stdout
    rawtext=subprocess.run(['pdftotext','-raw',str(root/'paper.pdf'),'-'],capture_output=True,text=True,check=True).stdout
    assert all(h in re.sub(r'\s+','',rawtext) for h in ['a3c45e945518cf64c84608df76b5b4c0f551201ef8f24f298692a4e94c1d7a38','71b1b2892c591c085529d5da41b97af208320513b7f25edff47836365ef57034','bc3b78f76a4c24b1643f49384f5546c5f4dd8ee894cf449c33b4f229dc85892d','fb963e6001ddfeb8c3cfc7715312dfec5188d982dcbc9f3d84a79f76cf8ba7cc','712e33f6fd33e9010ce615ef227f24e8af37c6b051e94d86ebc8ce3d6f4fa55a']);assert not re.search(r'\[\?\]|\?\?',pdftext);assert all(s.lower() in ' '.join(pdftext.split()).lower() for s in ['13.077','13.798','13.139','13.592','1,560','include zero','Jepson Taylor','draft'])
    forbidden=''.join(('ve','ox'));secret=re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY|https?://[^\s/@:]+:[^\s/@]+@|drive\.google\.com/file/d/')
    for p in root.rglob('*'):
        if not p.is_file() or 'qa' in p.relative_to(root).parts:continue
        assert p.suffix not in ['.xlsx','.xls','.csv','.pkl','.pickle','.tar','.gz'],p
        if p.suffix in ['.tex','.bib','.md','.json','.py','.bbl'] or p.name in ['Makefile','.gitignore']:
            t=p.read_text();assert forbidden not in t.lower(),p;assert not secret.search(t),p
        if p.suffix=='.py':ast.parse(p.read_text())
    assert forbidden not in (pdftext+info).lower()
    report={'status':'PASS','pages':pages,'bibliography_entries':len(entries),'numeric_result_cells':12,'planned_contrasts':10,'unresolved_references':0,'overfull_boxes':0,'new_model_fits':0,'raw_data_or_private_reports_in_tree':False,'prohibited_branding_found':False,'pdf_sha256':hashlib.sha256((root/'paper.pdf').read_bytes()).hexdigest(),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'paper.tex',root/'references.bib',root/'tables.tex',root/'claim_ledger.json']}}
    (root/'build_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));args=ap.parse_args();validate(args.root)
