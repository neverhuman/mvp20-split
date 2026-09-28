"""Bounded semantic failures; no partial plan or state mutation on rejection."""

from amphora_contracts_core import Finding


class CompilationError(ValueError):
    def __init__(self, code, location):
        self.findings = (Finding(code=code, location=location[:256], message=code.replace("_", " ")),)
        super().__init__(code)


def require(condition, code, location):
    if not condition:
        raise CompilationError(code, location)
