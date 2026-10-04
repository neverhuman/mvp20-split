"""Current grants and exact owner records precede scientific projections."""

from ..experiments.store import ExperimentStore
from ..observations.store import ObservationStore
from .experiment import ExperimentProjection
from .observation import ObservationProjection
from .query import ViewQuery
from .store import ObservationSelectionIndex


class ViewOwnerUnavailable(RuntimeError):
    pass


class ExplorationBoundary:
    def __init__(self, engine):
        self.experiments = ExperimentStore(engine)
        self.observations = ObservationStore(engine)
        self.index = ObservationSelectionIndex(engine)

    @staticmethod
    def _read(store, scope, reference, projection):
        try:
            record = store.read(scope, reference)
            if record is None:
                return None
            if record.reference != reference:
                raise ValueError("stored_reference_mismatch")
            return projection(record)
        except (ValueError, RecursionError) as error:
            raise ViewOwnerUnavailable("view_owner_unavailable") from error

    def catalog(self, principal, reference):
        principal.require("read_scientific_record", reference.scope)
        view = self._read(
            self.experiments, principal.scope, reference, ExperimentProjection
        )
        return None if view is None else view.catalog()

    def specimens(self, principal, request):
        principal.require("read_scientific_record", request.experiment.scope)
        query = ViewQuery.prepare(request)
        view = self._read(
            self.experiments,
            principal.scope,
            query.request.experiment,
            ExperimentProjection,
        )
        return None if view is None else view.specimens(query.request)

    def properties(self, principal, request):
        principal.require("read_scientific_record", request.experiment.scope)
        query = ViewQuery.prepare(request)
        request = query.request
        start, end = query.window(len(request.observations))
        view = self._read(
            self.experiments, principal.scope, request.experiment, ExperimentProjection
        )
        if view is None or not self.index.contains_all(
            principal.scope, request.observations
        ):
            return None
        rows = []
        for reference in request.observations[start:end]:
            observation = self._read(
                self.observations, principal.scope, reference, ObservationProjection
            )
            if observation is None:
                # Existence was established against immutable rows. Disappearance is an owner failure.
                raise ViewOwnerUnavailable("view_owner_unavailable")
            rows.append(observation.record)
        return view.properties(request, tuple(rows))

    def series(self, principal, request):
        principal.require("read_scientific_record", request.observation.scope)
        query = ViewQuery.prepare(request)
        view = self._read(
            self.observations,
            principal.scope,
            query.request.observation,
            ObservationProjection,
        )
        return None if view is None else view.series(query.request)
