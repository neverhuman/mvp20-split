"""Generate readable task/progress projections from the one canonical ledger."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'v2/docs/Diligence/2026-10-18'


def generate():
    ledger=json.loads((D/'task_ledger.json').read_text())
    tasks=ledger['tasks'];lines=['# Amphora | Detailed task register','',
      'Generated from `task_ledger.json`. Edit the ledger, then rerun this projection. Inspecting a task contract is not an acceptance pass. Future investor work and follow-on execution remain subject to their stated scope.','']
    progress=['# Amphora | Task completion projection','',
      'Version 2 retains this backlog for traceability. Task counts are preparation bookkeeping and do not measure scientific, commercial or investment readiness. Five decision tracks in V2/investment_gates.json remain unmet. Verified task evidence is byte-bound, explicitly supported and scoped to preparer checks; role approval is separate.','',
      '| Phase | Tasks | Implemented or verified | Verified preparation |',
      '|---|---:|---:|---:|']
    for phase in ledger['phases']:
        group=[t for t in tasks if t['phase']==phase['id']]
        done=sum(t['status'] in {'implemented','verified'} for t in group);verified=sum(t['status']=='verified' for t in group)
        progress.append(f"| {phase['id']} - {phase['name']} | {len(group)} | {done} | {verified} |")
        lines.extend(['',f"## {phase['id']} - {phase['name']}",''])
        for t in group:
            lines.extend([f"### {t['id']} - {t['title']}",'',
              f"- Status: **{t['status']}**; priority: {t['priority']}.",
              f"- Owner: {t['owner_role']}; reviewer: {t['reviewer_role']}.",
              f"- Dependencies: {', '.join(t['dependencies']) or 'none'}.",
              f"- Execution scope: {t['execution_authority']}.",
              '- Planning estimate: unestimated; assign a person and calibrate the bounded scope before scheduling.',
              f"- Boundary: {t['scope']}",
              '- Deliverables: '+', '.join('`'+p+'`' for p in t['deliverables'])+'.','',
              '**Acceptance**',''])
            for a in t['acceptance']:
                lines.append(f"- {a['check_id']} ({a['availability']}): {a['criteria']}")
                if a['command']:lines.extend(['','```sh',' '.join(a['command']),'```',''])
            lines.extend(['','**Evidence:** '+(', '.join('`'+e+'`' for e in t['evidence']) if t['evidence'] else 'Not yet retained; no acceptance pass is implied.'),'',
              '**Requirement sources:** '+ '; '.join(f"{x['document']} lines {x['start_line']}-{x['end_line']}" for x in t['source_refs'])+'.','',
              '**Failure rule:** '+t['failure_disposition'],''])
    done=sum(t['status'] in {'implemented','verified'} for t in tasks);verified=sum(t['status']=='verified' for t in tasks)
    progress.extend([f"| **Backlog only** | **{len(tasks)}** | **{done}** | **{verified}** |",'',
      'The current request delivers the comprehensive plan and qualified scaffolding. These percentages describe the larger future investor-delivery register; they are not a percentage of the usefulness or completeness of the current planning assignment.','',
      'Current assessment: 0 of 5 investment decision tracks met. This is not a scalar estimate of company value. Next investor decision: select the audience/claims and accountable owner/budget, then pursue the appropriate evidence track. Exact runtime return point: POP-01 E2.2a; preserve the existing POP/RG/ML sequence.'])
    (D/'TASK_REGISTER.md').write_text('\n'.join(lines).rstrip()+'\n');(D/'PROGRESS.md').write_text('\n'.join(progress).rstrip()+'\n')
    review=D/'V2/findings.json'
    if review.exists():
        findings=json.loads(review.read_text());report=['# Amphora | Candid red-team findings - version 2','',findings['review_scope'],'',
          'Confirmed defects, evidence gaps and unknowns have different meanings. Missing evidence is unverified, not declared false. Severity concerns diligence or the stated trusted-tooling profile, not a remotely exposed production service.','']
        for finding in findings['findings']:
            report += [f"## {finding['id']} - {finding['title']}",'',f"**Severity:** {finding['severity']}. **Basis:** {finding['basis']}. **Disposition:** {finding['disposition']}.",'',
              '**Investor impact:** '+finding['investor_impact'],'','**Concrete fix:** '+finding['fix'],'','**Verification / remaining evidence:** '+finding['verification'],'']
            for src in finding['sources']:
                url='https://github.com/neverhuman/mvp20-split/blob/'+src['revision']+'/'+src['path'].replace(' ','%20')+'#L'+str(src['lines'][0])
                report += [f"Source: [{src['path']} at {src['revision'][:8]}, lines {src['lines'][0]}-{src['lines'][1]}]({url}). SHA-256 `{src['sha256']}`.",'']
        (D/'V2/RED_TEAM_FINDINGS.md').write_text('\n'.join(report).rstrip()+'\n')
        state=['# Amphora | One-page current-state ledger - version 2','',
          '| Evidence object | Current state | What it does not establish |','|---|---|---|',
          '| Implemented scaffold | Reviewed source pins, fixed historical transport, strict task/claim checks and current V2 hardening; exact checks in V2/evidence | Product, scientific or commercial derisking |',
          '| Investor prose | Full brief/systems note and qualified investor capsule remain planned; a complete scientific proof card is generated | An approved investor release |',
          '| Scientific study | Retrospective isolated PLGA adapter; all ten planned intervals include zero; original paper/results unchanged | Pareto-specific superiority, equivalence, new-panel transfer or deployed-engine integration |',
          '| Commercial/defensibility | Explicit hypotheses and contribution/rights matrix | Buyer demand, pricing, ROI, exclusivity or a proven moat |',
          '| Ownership/budget | Roles are unassigned and future budgets unapproved | Staffing capacity or a six-hour delivery promise |',
          '| Review | Actual V1 artifacts/code inspected by local preparer; additional worker reviewed reconciliation only | Independent full-artifact audit or independent science |',
          '| Decision tracks | 0 of 5 met; partial/unverified/not-met states recorded | An investment recommendation |','',
          'Current publication scope: user-authorized revision pushed as a review branch with a draft PR. No merge, experiments or production operations are implied. The 93 stable IDs remain an implementation backlog; percentages are not readiness measures.']
        (D/'V2/CURRENT_STATE.md').write_text('\n'.join(state)+'\n')
    return {'tasks':len(tasks),'implemented_or_verified':done,'verified':verified}


if __name__=='__main__':print(json.dumps(generate(),sort_keys=True))
