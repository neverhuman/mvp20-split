"""Reconstruct the exact primary/late capture from owned immutable SQL history."""

from ..campaign_preparations.journal import CampaignPreparationJournal
from ..context import AttemptBinding
from ..context.policy import require
from ..persistence.dispatch import DispatchJournal
from ..persistence.journal import PlanningJournal
from ..persistence.settlement import SettlementJournal
from ..supervision_intake.snapshot import CheckpointIntakeSnapshot
from ..supervision_intake.storage import SupervisionIntake
from .capture import CaptureOrigin


def load_origin(engine, connection, principal, engagement_id, ordinal, kind):
    require(kind in {'primary', 'late'}, 'capture_observation_kind')
    key = {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
        'engagement': engagement_id, 'ordinal': ordinal}
    intake = SupervisionIntake._wrapper(connection, key, principal)
    require(isinstance(intake, CheckpointIntakeSnapshot), 'capture_intake_missing')
    binding = AttemptBinding(intake.planning, ordinal)
    stored = CampaignPreparationJournal(engine)._read(connection,
        {name: key[name] for name in ('tenant', 'project', 'engagement')}, intake.planning)
    require(stored is not None, 'capture_preparation_missing')
    current = PlanningJournal(engine)._attempt(connection, key, intake.planning)
    require(current is not None and current.observation is not None, 'capture_observation_missing')
    settlement = SettlementJournal(engine)
    charge = settlement._charge(connection, key, binding)
    require(settlement._read(connection, key, charge) is not None, 'capture_settlement_missing')
    observation = current.observation
    if kind == 'late':
        dispatch = DispatchJournal(engine)
        bound, reservation = dispatch._bound(connection, key, principal, binding)
        observation = dispatch._late(connection, key, bound, reservation)
        require(observation is not None, 'capture_late_missing')
    return CaptureOrigin.bind(intake, principal, stored.record, observation, kind=kind)
