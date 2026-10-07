"""Reconcile one original container turn; never retry an ambiguous start."""

from ..profile import require


class ContainerTurn:
    def __init__(self, journal, engine, profile, environment):
        self.journal, self.engine, self.profile = journal, engine, profile
        self._environment = dict(environment)

    def launch(self):
        self.profile.verify()
        record = self.journal.read()
        if record is None or record['phase'] == 'released':
            record = self.journal.intent()
        if record['phase'] == 'intent':
            observed = self.engine.observe(record, self.profile)
            if observed is None:
                container_id = self.engine.create(record, self.profile, self._environment)
                observed = self.engine.observe(record, self.profile)
                require(observed is not None and observed.container_id == container_id, 'container_create_unconfirmed')
            require(observed.status == 'created' and not observed.started, 'container_unexpected_start')
            record = self.journal.created(observed.container_id)
        if record['phase'] == 'created':
            observed = self.engine.observe(record, self.profile)
            require(observed is not None and observed.status == 'created' and not observed.started,
                    'container_start_requires_original_created')
            self.journal.starting()
            self.engine.start(record['container_id'])
            self.journal.started()
        # Starting/started/exited replays do not send Docker start again.
        return self

    def poll(self):
        record = self.journal.read()
        require(record is not None and record['phase'] in {'starting', 'started', 'exited'}, 'container_turn_not_started')
        if record['phase'] == 'exited':
            return record['exit_code']
        observed = self.engine.observe(record, self.profile)
        require(observed is not None, 'container_original_missing')
        if observed.status == 'exited':
            self.journal.exited(observed.exit_code)
            return observed.exit_code
        if observed.status == 'created':
            # Start may still be queued at the daemon. Absence of StartedAt does
            # not prove the original request cannot execute later.
            require(record['phase'] == 'starting', 'container_start_state_regressed')
        return None

    def release(self):
        record = self.journal.read()
        require(record is not None and record['phase'] in {'exited', 'released'}, 'container_release_requires_exit')
        if record['phase'] == 'exited':
            self.engine.remove_exited(record, self.profile)
            self.journal.released()
