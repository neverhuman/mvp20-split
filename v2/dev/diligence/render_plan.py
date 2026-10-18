"""Render the Amphora engineering workplan. Renderer dependencies stay optional."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import textwrap
import importlib.util

ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'v2/docs/Diligence/2026-10-18'


def render(output):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import (BaseDocTemplate,Frame,PageTemplate,Paragraph,Spacer,
      Table,TableStyle,PageBreak,KeepTogether,Flowable)
    sys.path.insert(0, str(ROOT / 'v2/dev'))
    from diligence.cli import check_plan
    check_plan()

    if output.exists():raise ValueError('Choose a new PDF output path')
    brand=json.loads((D/'brand_tokens.json').read_text());ledger=json.loads((D/'task_ledger.json').read_text())
    palette={k:colors.HexColor('#'+v) for k,v in brand['palette'].items()}
    fontdir=Path(importlib.util.find_spec('matplotlib').origin).parent/'mpl-data/fonts/ttf';fontfiles={
      'AmphoraSans':'DejaVuSans.ttf','AmphoraBold':'DejaVuSans-Bold.ttf',
      'AmphoraMono':'DejaVuSansMono.ttf','AmphoraItalic':'DejaVuSans-Oblique.ttf'}
    for name,file in fontfiles.items():pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
    pdfmetrics.registerFontFamily('AmphoraSans',normal='AmphoraSans',bold='AmphoraBold',italic='AmphoraItalic',boldItalic='AmphoraBold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('Body',fontName='AmphoraSans',fontSize=10.5,leading=15,spaceAfter=7,textColor=palette['ink'],allowWidows=0,allowOrphans=0))
    styles.add(ParagraphStyle('TitleA',fontName='AmphoraBold',fontSize=31,leading=38,textColor=palette['ink'],spaceAfter=14))
    styles.add(ParagraphStyle('Deck',fontName='AmphoraSans',fontSize=14,leading=21,textColor=palette['muted'],spaceAfter=16))
    styles.add(ParagraphStyle('SectionA',fontName='AmphoraBold',fontSize=18,leading=23,spaceBefore=18,spaceAfter=10,textColor=palette['ink'],keepWithNext=True))
    styles.add(ParagraphStyle('SectionB',fontName='AmphoraBold',fontSize=12,leading=17,spaceBefore=12,spaceAfter=6,textColor=palette['teal'],keepWithNext=True))
    styles.add(ParagraphStyle('CellA',fontName='AmphoraSans',fontSize=9.1,leading=12.5,textColor=palette['ink']))
    styles.add(ParagraphStyle('CellHead',fontName='AmphoraBold',fontSize=9.1,leading=12.5,textColor=colors.white))
    styles.add(ParagraphStyle('CodeA',fontName='AmphoraMono',fontSize=9,leading=12,spaceAfter=5,textColor=palette['ink'],backColor=palette['wash'],borderPadding=7))
    width=612-2*.7*inch

    def inline(s):
        # Links retain readable labels. Source-linked documents are delivered alongside this PDF.
        s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:m.group(1),s)
        s=html.escape(s)
        s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
        s=re.sub(r'`([^`]+)`',r'<font name="AmphoraMono" size="9">\1</font>',s)
        return s

    def paragraph(s,style='Body'):return Paragraph(inline(s),styles[style])

    def table(rows,weights=None):
        cols=len(rows[0]);weights=weights or [1]*cols;colwidths=[width*w/sum(weights) for w in weights]
        body=[[paragraph(c,'CellHead' if i==0 else 'CellA') for c in row] for i,row in enumerate(rows)]
        t=Table(body,colWidths=colwidths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'AmphoraSans'),('BACKGROUND',(0,0),(-1,0),palette['ink']),('VALIGN',(0,0),(-1,-1),'TOP'),
          ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,palette['wash']]),('LINEBELOW',(0,0),(-1,0),.7,palette['teal']),('LINEBELOW',(0,1),(-1,-1),.3,palette['rule'])]))
        return t

    class Route(Flowable):
        def __init__(self):super().__init__();self.width=width;self.height=112
        def draw(self):
            c=self.canv;w=(width-30)/4;labels=[('PIN','Source and claims'),('CHECK','Exact evidence'),('BUILD','Readable documents'),('QUALIFY','Private review')]
            for i,(small,label) in enumerate(labels):
                x=i*(w+10);c.setFillColor(palette['wash']);c.setStrokeColor(palette['rule']);c.roundRect(x,23,w,65,7,fill=1,stroke=1)
                c.setFillColor(palette['teal']);c.setFont('AmphoraBold',9);c.drawString(x+10,67,small)
                c.setFillColor(palette['ink']);c.setFont('AmphoraSans',9.1)
                for j,line in enumerate(textwrap.wrap(label,18)):c.drawString(x+10,49-j*12,line)
                if i<3:c.setStrokeColor(palette['teal']);c.line(x+w+1,55,x+w+9,55)

    def page(canvas,doc):
        canvas.saveState();canvas.setFillColor(palette['ink']);canvas.setFont('AmphoraBold',11);canvas.drawString(.7*inch,752,'AMPHORA')
        canvas.setFont('AmphoraSans',9);canvas.setFillColor(palette['muted']);canvas.drawRightString(612-.7*inch,752,'VERSION 2 | INVESTOR REVIEW')
        canvas.setStrokeColor(palette['rule']);canvas.line(.7*inch,742,612-.7*inch,742)
        canvas.line(.7*inch,44,612-.7*inch,44);canvas.setFont('AmphoraSans',8.5);canvas.drawString(.7*inch,29,'18 October 2026 | Local review draft')
        canvas.drawRightString(612-.7*inch,29,str(doc.page));canvas.restoreState()

    output.parent.mkdir(parents=True,exist_ok=True)
    doc=BaseDocTemplate(str(output),pagesize=(612,792),leftMargin=.7*inch,rightMargin=.7*inch,topMargin=64,bottomMargin=58,
       title='Amphora | Critical investor review and workplan - version 2',author='Amphora',subject='Candid findings, decision gates and bounded code fixes',creator='Amphora diligence plan renderer v2')
    doc.addPageTemplates(PageTemplate(id='Amphora',frames=[Frame(.7*inch,58,width,676,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page))
    story=[Spacer(1,20),paragraph('Investor challenge.\nEvidence-led version 2.','TitleA'),paragraph('A candid decision brief and source-grounded delivery plan','Deck'),
       paragraph('5 decision tracks | 14 findings | 93 backlog IDs retained','SectionB'),
       table([['Investor question','Current evidence','Unresolved decision'],
         ['Inspectable engineering?','Source mechanisms and bounded historical demonstrations.','Current installed behavior and the selected integrated workflow.'],
         ['Scientific advantage?','Complete retrospective PLGA matrix; all ten planned intervals include zero.','New-panel benefit/transfer; no established Pareto-specific superiority.'],
         ['Product integration?','PLGA is a separate adapter; no LLM calls.','No end-to-end PLGA campaign-engine qualification supplied.'],
         ['Commercial value?','Workflow composition/reuse is a hypothesis.','Buyer pain, current alternative, adoption, pricing and matched value evidence.'],
         ['Defensible assets?','Versioned source and data provenance.','Chain of rights, accountable owners/budgets and incremental advantage.']],[1.1,1.8,1.8]),
       Spacer(1,15),paragraph('Decision: deeper technical diligence and a bounded next proof are supportable. None of the five investment tracks is closed. Preparation task counts are not scientific or commercial derisking.'),
       paragraph('Two reproduced V1 defects are addressed in this revision: mutable hashes could bless a fake historical checker, and a README could qualify an owner-approval task. The original PLGA paper and results remain unchanged.'),PageBreak()]
    lines=(D/'V2/WORKPLAN_V2.md').read_text().splitlines();i=0;buffer=[]
    def flush():
        if buffer:story.append(paragraph(' '.join(buffer)));buffer.clear()
    while i<len(lines):
        line=lines[i]
        if line.startswith('# '):i+=1;continue
        if line.startswith('## '):
            flush();story.append(paragraph(line[3:],'SectionA'));i+=1;continue
        if line.startswith('### '):
            flush();story.append(paragraph(line[4:],'SectionB'));i+=1;continue
        if line.startswith('|'):
            flush();rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[x.strip() for x in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',x) for x in cells):rows.append(cells)
                i+=1
            story.append(table(rows));story.append(Spacer(1,9));continue
        if line.startswith('```'):
            flush();code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):code.extend(textwrap.wrap(lines[i],88,replace_whitespace=False,drop_whitespace=False) or ['']);i+=1
            story.append(Paragraph('<br/>'.join(html.escape(x).replace(' ','&nbsp;') for x in code),styles['CodeA']));i+=1;continue
        if re.match(r'^\d+\. ',line) or line.startswith('- '):
            flush();story.append(paragraph(line));i+=1;continue
        if not line.strip():flush()
        else:buffer.append(line)
        i+=1
    flush();story.append(PageBreak());story.append(paragraph('Candid findings and disposition','SectionA'))
    findings=json.loads((D/'V2/findings.json').read_text())
    for finding in findings['findings']:
        story.append(paragraph(finding['id']+' | '+finding['severity'].upper()+' | '+finding['title'],'SectionB'))
        story.append(paragraph('Impact: '+finding['investor_impact']))
        story.append(paragraph('Fix / disposition: '+finding['fix']+' ['+finding['disposition']+']'))
        story.append(paragraph('Verification / remaining proof: '+finding['verification']))
        src=finding['sources'][0]
        url='https://github.com/neverhuman/mvp20-split/blob/'+src['revision']+'/'+src['path'].replace(' ','%20')+'#L'+str(src['lines'][0])
        story.append(Paragraph('Source: <link href="'+html.escape(url,quote=True)+'" color="#087F8C">'+html.escape(src['revision'][:8]+' / '+Path(src['path']).name+' / lines '+str(src['lines'][0])+'-'+str(src['lines'][1]))+'</link>',styles['CellA']))
        story.append(Spacer(1,8))
    story.append(PageBreak());story.append(paragraph('Actual version 2 checks','SectionA'))
    receipt=json.loads((D/'V2/evidence/test_report.json').read_text())
    story.append(paragraph(str(receipt['tests_run'])+' focused tests: '+receipt['result']+'. This qualifies the named tooling boundary; it is not a count of scientific or commercial risks retired.'))
    verified=json.loads((D/'V2/evidence/final_source_profile.json').read_text())
    story.append(paragraph('Source/capsule report: '+verified['report']['status']+'. The original twelve historical assertions and PLGA aggregate check executed as stated in the receipt. Historical fitting/process behavior was not rerun.'))
    story.append(paragraph('Full commands, code hashes, environment, stdout digest, coverage and requested arithmetic outcome are in V2/evidence. The additional review worker did not inspect the inaccessible Library artifacts; local artifact and code review was performed by the preparer.'))
    rows=[['Decision track','State','New evidence required']]
    for gate in json.loads((D/'V2/investment_gates.json').read_text())['gates']:
        rows.append([gate['id']+' - '+gate['name'],gate['state'],gate['evidence_needed']])
    story.append(table(rows,[1.5,.7,3]));story.append(Spacer(1,10))
    story.append(paragraph('The 93 task IDs remain in TASK_REGISTER.md and task_ledger.json. No task percentage is presented as investment readiness. Missing owners, budgets and decision margins are deliberately unresolved.'))
    story.append(PageBreak());story.append(paragraph('Source and artifact identity','SectionA'))
    story.append(paragraph('The complete source lock and specification register accompany this document. Their hashes bind inspected inputs; they do not establish publisher authenticity or scientific validation.'))
    for spec in json.loads((D/'specification_register.json').read_text())['documents']:
        story.append(paragraph(spec['id']+' | '+str(spec['lines'])+' lines | '+str(spec['bytes'])+' bytes','SectionB'))
        story.append(paragraph(spec['filename']));story.append(paragraph('SHA-256: `'+spec['sha256']+'`'))
    story.append(paragraph('Repository basis: `9c3018dcdd17f40be27fc3c6dc7057d2d7cb05bc`. Original PLGA PDF: `f228757745d9d4836f6d048120867348ef6718e9763ca48ea0710f60b11dd33a`.'))
    story.append(paragraph('Fresh evidence reports and final branch/commit are in the handoff. An earlier review receipt cannot approve a changed PDF. No raw attachment, private correspondence or new scientific experiment is created by this workplan.'))
    def canvas_factory(*args, **kwargs):
        kwargs['initialFontName'] = 'AmphoraSans'
        return Canvas(*args, **kwargs)
    doc.build(story,canvasmaker=canvas_factory)
    receipt={'format':'amphora-plan-render.v1','output_name':output.name,'pdf_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
      'source_sha256':{str((D/name).relative_to(ROOT)):hashlib.sha256((D/name).read_bytes()).hexdigest() for name in ['V2/WORKPLAN_V2.md','task_ledger.json','brand_tokens.json','claims.json','source_lock.json','specification_register.json','V2/findings.json','V2/investment_gates.json','V2/evidence/test_report.json','V2/evidence/final_source_profile.json','V2/SCIENTIFIC_CARD.md','V2/CONTRIBUTION_PROVENANCE.md','V2/commercial_hypotheses.json']},
      'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'font_sha256':{name:hashlib.sha256((fontdir/file).read_bytes()).hexdigest() for name,file in fontfiles.items()},
      'renderer':'ReportLab','visual_qa':'pending_after_render','metadata_policy':'Record final PDF hash; no byte determinism claimed before testing fixed toolchain.'}
    for p in (ROOT/'v2/dev/diligence/templates').glob('*.tex'):
        receipt['source_sha256'][p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    output.with_suffix('.render.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();render(args.output)
