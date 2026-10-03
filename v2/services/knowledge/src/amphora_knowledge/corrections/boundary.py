"""Scoped correction/selection authority distinct from graph and publication grants."""


class CorrectionBoundary:
    def __init__(self, store):
        self.store = store

    def submit(self, principal, request):
        return self.store.append(request, principal).view

    def read(self, principal, request):
        principal.require("select_reasoning_receipt", request.chain.scope)
        result = self.store.select(request)
        return None if result is None else result.view
