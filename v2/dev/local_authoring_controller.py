"""Optional actual Registry alongside retained owners; no workers or tool activation."""

from local_records_controller import RecordsController


class AuthoringController(RecordsController):
    def __init__(self, *args, registry_token=None, **kwargs):
        self.registry_token = registry_token
        super().__init__(*args, **kwargs)

    def start(self):
        super().start()
        if 'registry' in self.control('/status')['owners']:
            assert self.registry_token, 'Registry read credential required'
            self.control('/owners/registry/start', 'POST')
            self.wait(lambda: self.request(self.routes.endpoint('registry'), '/v1/releases',
                token=self.registry_token)[0] == 200)

    def drain(self):
        if 'registry' in self.control('/status')['owners']:
            self.control('/owners/registry/drain', 'POST')
            self.wait(lambda: self.control('/status')['owners']['registry']['state'] == 'exited')
        return super().drain()
