"""One bounded compiler step using its existing independent lease and commands."""
from dataclasses import replace
from .rejection import ProposalRejected


class CurationCompiler:
    def __init__(self, journal, progression):
        if progression.journal is not journal.compiler:
            raise ValueError('curation_compiler_progression')
        self.journal, self.progression = journal, progression

    def advance(self, principal, lease):
        current = self.journal.current(principal, lease.curation_id)
        if current is not None and current.terminal:
            return current
        try:
            selected = self.journal.prepare(principal, lease)
        except ProposalRejected as error:
            return self.journal._project(principal, lease, 'failed', str(error), None)
        lease = replace(lease, progress=selected.progress)
        # Job selection is delegated to the existing independently fenced compiler;
        # expired job ownership cannot erase a command already issued by that owner.
        with self.journal.engine.begin() as conn:
            self.journal._guard(principal, lease, conn)
        step = self.progression.advance(principal, selected.selection.effect_id)
        return self.journal.observe(principal, lease, selected.selection, step)
