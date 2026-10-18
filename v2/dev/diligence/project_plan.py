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
      'One task is one equal delivery unit. Verified status requires evidence and verified dependencies. Implemented status does not imply review/acceptance. These are DD-01 units, not engine implementation percentages.','',
      '| Phase | Tasks | Implemented or verified | Verified | Implementation % | Verification % |',
      '|---|---:|---:|---:|---:|---:|']
    for phase in ledger['phases']:
        group=[t for t in tasks if t['phase']==phase['id']]
        done=sum(t['status'] in {'implemented','verified'} for t in group);verified=sum(t['status']=='verified' for t in group)
        progress.append(f"| {phase['id']} - {phase['name']} | {len(group)} | {done} | {verified} | {100*done/len(group):.2f}% | {100*verified/len(group):.2f}% |")
        lines.extend(['',f"## {phase['id']} - {phase['name']}",''])
        for t in group:
            lines.extend([f"### {t['id']} - {t['title']}",'',
              f"- Status: **{t['status']}**; priority: {t['priority']}.",
              f"- Owner: {t['owner_role']}; reviewer: {t['reviewer_role']}.",
              f"- Dependencies: {', '.join(t['dependencies']) or 'none'}.",
              f"- Execution scope: {t['execution_authority']}.",
              f"- Planning estimate: {t['estimate_minutes'][0]}-{t['estimate_minutes'][1]} minutes; unmeasured.",
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
    progress.extend([f"| **Overall** | **{len(tasks)}** | **{done}** | **{verified}** | **{100*done/len(tasks):.2f}%** | **{100*verified/len(tasks):.2f}%** |",'',
      'The current request delivers the comprehensive plan and qualified scaffolding. These percentages describe the larger future investor-delivery register; they are not a percentage of the usefulness or completeness of the current planning assignment.','',
      'Next investor decision: DD-010. Exact runtime return point: POP-01 E2.2a, reconcile owning Data qualification before Runtime binding; preserve existing POP/RG/ML sequence.'])
    (D/'TASK_REGISTER.md').write_text('\n'.join(lines).rstrip()+'\n');(D/'PROGRESS.md').write_text('\n'.join(progress).rstrip()+'\n')
    return {'tasks':len(tasks),'implemented_or_verified':done,'verified':verified}


if __name__=='__main__':print(json.dumps(generate(),sort_keys=True))
