"""Controller-owned reporters; cached control status and nonblocking drain guard."""

from ..profile import require


class CatalogGroup:
    def __init__(self, reporters=None):
        self.reporters = {} if reporters is None else dict(reporters)

    def start(self):
        for reporter in self.reporters.values():
            reporter.start()

    def status(self):
        return {name: reporter.status() for name, reporter in self.reporters.items()}

    def resume(self):
        for reporter in self.reporters.values():
            reporter.resume()

    def quiesce(self):
        for reporter in self.reporters.values():
            reporter.quiesce()

    def require_stopped(self):
        for reporter in self.reporters.values():
            reporter.require_stopped()

    def close(self):
        self.quiesce()
        failed = False
        for reporter in self.reporters.values():
            try:
                reporter.close()
            except Exception:  # noqa: BLE001 - join all owned reporters before aggregate error.
                failed = True
        require(not failed, 'catalog_cleanup_incomplete')
