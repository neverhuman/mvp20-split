import pytest
from check_boundaries import check, source_violations


@pytest.mark.parametrize(
    "source,expected",
    [
        ("from amphora_contracts_core.models import Scope", "private_contract_import"),
        ("from amphora_knowledge.repository import Store", "undeclared_or_private_dependency"),
        ("import sqlalchemy", "undeclared_or_private_dependency"),
        ("__import__('other_service')", "dynamic_import"),
        ("import importlib; importlib.import_module('other')", "dynamic_import"),
        ("import sys; sys.path.append('../other')", "path_injection"),
    ],
)
def test_forbidden_imports_are_detected(source, expected):
    assert expected in source_violations(
        source,
        "amphora_campaign_runtime",
        {"amphora_contracts_core"},
        {"amphora-contracts-core"},
        {"amphora-contracts-core"},
    )


def test_declared_public_contract_and_owner_internal_imports_allowed():
    source = "from amphora_contracts_core import Scope\nfrom .graph import Graph\nimport json"
    assert not source_violations(
        source,
        "amphora_campaign_runtime",
        {"amphora_contracts_core"},
        {"amphora-contracts-core"},
        {"amphora-contracts-core"},
    )


def test_current_production_dependencies():
    assert check() == []


def test_public_client_root_is_explicit_and_private_modules_remain_forbidden():
    public = {"amphora_tool_protocol"}
    deps = {"amphora-tool-protocol"}
    assert not source_violations("from amphora_tool_protocol import RuntimeClient", "amphora_numeric_affine", public, deps, deps)
    assert source_violations("from amphora_tool_protocol.clients import RuntimeClient", "amphora_numeric_affine", public, deps, deps) == ["private_contract_import"]
    assert source_violations("from amphora_tool_protocol import RuntimeClient", "amphora_numeric_affine", public, deps, set()) == ["undeclared_contract_dependency"]
