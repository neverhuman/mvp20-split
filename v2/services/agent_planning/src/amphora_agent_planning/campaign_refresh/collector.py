"""Fresh owner calls outside SQL; unchanged historical bytes never renew permission."""

import hashlib
from datetime import UTC, datetime

from pydantic import ValidationError

from ..campaign_context.records import canonical
from ..campaign_data_access import ArtifactSelection
from ..campaign_proposals.observations import ObservationKey
from ..campaign_proposals.research import ConsumedResearch
from ..context.policy import require
from ..metadata_reads import MetadataWindow
from ..registry_access import ObservedRelease
from ..runtime_metadata import ReviewedUniverse
from ..runtime_metadata.reader import PEER_CODES
from ..source_access.budget import ReadBudget
from .result import RefreshChange, RefreshFinding, RefreshResult

UNIVERSE_CODES = frozenset({'runtime_metadata_type', 'runtime_metadata_scope', 'runtime_metadata_duplicate_tool',
    'runtime_metadata_duplicate_schema', 'runtime_metadata_duplicate_port', 'runtime_metadata_universe', 'runtime_metadata_size'})


class ExactReleaseWindow(MetadataWindow):
    """64 selected exact reads, distinct from the unchanged eight-page scan window."""

    def __init__(self):
        super().__init__('registry', seconds=20)
        self.max_calls = 64


class RefreshCollector:
    def __init__(self, *, artifacts, research, registry, runtime):
        self.artifacts, self.research, self.registry, self.runtime = artifacts, research, registry, runtime

    def collect(self, plan):
        plan.verify()
        processing, failures, changes, gaps = [], [], [], []
        budget = ReadBudget()
        for offset in range(0, len(plan.artifacts), 128):
            selection = ArtifactSelection.bind(plan.request, plan.artifacts[offset:offset + 128])
            report = self.artifacts.read(selection, budget)
            require(report.selection == selection, 'refresh_artifact_selection')
            expected = set(selection.references())
            returned = [row.reference for row in (*report.records, *report.failures)]
            require(len(returned) == len(set(returned)) and set(returned) == expected, 'refresh_artifact_coverage')
            for row in report.records:
                require(type(row.body) is bytes and len(row.body) == row.reference.size_bytes and
                        hashlib.sha256(row.body).hexdigest() == row.reference.sha256, 'refresh_artifact_content')
                processing.append(row.reference)
            failures.extend(RefreshFinding('data', canonical(row.reference.model_dump(mode='json')), row.code)
                            for row in report.failures)
        self._research(plan, changes, gaps)
        self._releases(plan, changes, failures)
        self._runtime(plan, changes, failures)
        return RefreshResult(plan, datetime.now(UTC), tuple(processing), tuple(changes), tuple(failures), tuple(gaps))

    def _research(self, plan, changes, gaps):
        if plan.research is None:
            return
        report = self.research.review(plan.research)
        current = report.context
        require(current.selection == plan.research, 'refresh_research_selection')
        # ResearchRecordReader owns reconstruction and exact identity validation.
        # Reconstruct the returned context too, rather than trusting derived lists.
        from ..campaign_context import ResearchContext
        groups = {kind: tuple(row.document() for row in current.records if row.identity.kind == kind)
                  for kind in ('question', 'need', 'assessment')}
        verified = ResearchContext.bind(plan.research, questions=groups['question'], needs=groups['need'],
            assessments=groups['assessment'], unavailable=current.gaps)
        require(verified == current, 'refresh_research_context')
        original = plan.review.composition.evidence.research.context
        before = {ConsumedResearch.key(row.identity): row.sha256 for row in original.records}
        after = {ConsumedResearch.key(row.identity): row.sha256 for row in current.records}
        for key in plan.review.read_set.keys:
            if key.lane == 'research' and before.get(key) != after.get(key):
                changes.append(RefreshChange(key, before.get(key), after.get(key)))
        gaps.extend(RefreshFinding('research', canonical(row.identity.document()), row.reason) for row in current.gaps)

    def _releases(self, plan, changes, failures):
        window = ExactReleaseWindow()
        keys = {use.release.record.document().lock: use.release.key for use in plan.review.composition.uses}
        for original in plan.releases:
            selected = original.document()
            identity = canonical(selected.lock.model_dump(mode='json'))
            try:
                current = self.registry.exact(plan.request, selected.lock, window)
                require(ObservedRelease.bind(current.document(), selected.scope, selected.lock) == current,
                        'refresh_registry_binding')
            except ValueError as error:
                if isinstance(error, ValidationError):
                    code = 'registry_record_invalid'
                elif str(error) in PEER_CODES | {'registry_scope', 'registry_lock', 'registry_record_type',
                                                'registry_descriptor_size', 'registry_duplicate_port'}:
                    code = str(error)
                else:
                    raise
                failures.append(RefreshFinding('registry', identity, code))
            else:
                if current.sha256 != original.sha256:
                    changes.append(RefreshChange(keys[selected.lock], original.sha256, current.sha256))

    def _runtime(self, plan, changes, failures):
        selected = plan.review.composition.runtime
        if selected is None:
            return
        try:
            current = self.runtime.universe(plan.request, window=MetadataWindow('runtime', seconds=20))
            require(ReviewedUniverse.bind(current.document(), plan.request) == current, 'refresh_runtime_binding')
        except ValueError as error:
            if isinstance(error, ValidationError):
                code = 'runtime_record_invalid'
            elif str(error) in PEER_CODES | UNIVERSE_CODES:
                code = str(error)
            else:
                raise
            failures.append(RefreshFinding('runtime', canonical(plan.request.document().reference.scope.model_dump(mode='json')), code))
        else:
            for tool in selected.changes(current):
                changes.append(RefreshChange(ObservationKey('runtime', 'selected_tool', canonical(tool.model_dump(mode='json'))),
                                              None, None))
