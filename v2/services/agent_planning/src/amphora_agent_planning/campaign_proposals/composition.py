"""Link authored producers and selected tool releases without execution authority."""

from dataclasses import dataclass

from amphora_contracts_planning import CampaignNodeAddress, FutureCampaignDraft

from ..context.policy import require
from .authored import AuthoredCampaign
from .evidence import EvidenceFinding, EvidencePurposeReview
from .observations import RelevantReadSet
from .tools import (
    ConsumedRelease,
    ConsumedTools,
    RuntimeToolSelection,
    literal_dependencies,
    validate_invocation,
)


@dataclass(frozen=True)
class ToolUse:
    address: CampaignNodeAddress
    release: ConsumedRelease


@dataclass(frozen=True)
class CompositionReview:
    evidence: EvidencePurposeReview
    authored: AuthoredCampaign | None
    uses: tuple[ToolUse, ...]
    runtime: RuntimeToolSelection | None
    read_set: RelevantReadSet
    findings: tuple[EvidenceFinding, ...]

    @classmethod
    def bind(cls, prepared):
        evidence = EvidencePurposeReview.bind(prepared)
        prepared = evidence.proposal
        candidate = prepared.review_document().candidate
        authored = AuthoredCampaign.bind(candidate) if isinstance(candidate, FutureCampaignDraft) else None
        tools = ConsumedTools.from_proposal(prepared)
        uses, findings = [], []
        keys = set(evidence.read_set.keys)
        if authored is not None:
            for node in authored.nodes:
                if node.node.kind == 'invoke':
                    release = tools.release(node.node.tool)
                    validate_invocation(node.node, release)
                    keys.update(literal_dependencies(node.node, prepared))
                    uses.append(ToolUse(node.address, release))
        runtime = None
        if uses:
            require(tools.universe is not None, 'campaign_tool_runtime_unavailable')
            runtime = RuntimeToolSelection.bind(tools.universe, tuple(dict.fromkeys(use.release.record.document().lock.tool for use in uses)))
            locks = {lock.tool: lock for lock in runtime.locks}
            require(all(locks[use.release.record.document().lock.tool] == use.release.record.document().lock for use in uses),
                    'campaign_tool_reviewed_lock')
        draft = prepared.review_document()
        groups = [('/evidence_requests', draft.evidence_requests)]
        if candidate is not None:
            groups.append(('/candidate/expected_evidence', candidate.expected_evidence))
        for path, intents in groups:
            for index, intent in enumerate(intents):
                if intent.producer is not None:
                    if authored is not None:
                        authored.resolve(intent.producer)
                    else:
                        findings.append(EvidenceFinding(path + '/' + str(index) + '/producer', 'runtime_producer_resolution_required'))
        findings.extend(finding for finding in evidence.findings if finding.code != 'producer_resolution_required')
        if candidate is not None and authored is None:
            findings.append(EvidenceFinding('/candidate', 'runtime_adjustment_acceptance_required'))
        keys.update(use.release.key for use in uses)
        return cls(evidence, authored, tuple(uses), runtime, prepared.inputs.select(keys), tuple(findings))
