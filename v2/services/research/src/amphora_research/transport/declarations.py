"""Exact declaration reads; neither artifact access nor scientific adjudication."""

from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef


class DeclarationReader:
    def __init__(self, ledger):
        self.ledger = ledger

    def read(self, principal, reference: ResearchQuestionRef | EvidenceNeedRef):
        principal.require("read_declarations", reference.scope)
        if isinstance(reference, ResearchQuestionRef):
            kind, identity = "question", reference.question_id
        else:
            kind, identity = "need", reference.need_id
        return self.ledger.read(reference.scope, kind, identity, reference.revision)
