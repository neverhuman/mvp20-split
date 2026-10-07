import pytest

from run_tests import ownership_issues


def test_repository_test_ownership():
    assert ownership_issues() == []


@pytest.mark.parametrize('parent', ['services', 'deploy'])
def test_orphan_and_overlapping_test_owners_are_rejected(tmp_path, parent):
    tests = tmp_path / parent / "example/tests"
    tests.mkdir(parents=True)
    (tests / "test_behavior.py").write_text("def test_behavior(): pass")
    assert ownership_issues(tmp_path, {}) == [
        f"Expected one test owner: {parent}/example/tests/test_behavior.py"
    ]
    scopes = {"example": {"tests": f"{parent}/example/tests"}}
    assert ownership_issues(tmp_path, scopes) == []
    scopes["duplicate"] = {"tests": f"{parent}/example"}
    assert len(ownership_issues(tmp_path, scopes)) == 1


def test_node_suites_have_one_declared_owner_and_known_runner(tmp_path):
    tests = tmp_path / "studio/tests/transport"
    tests.mkdir(parents=True)
    (tests / "http.test.ts").write_text("// owned test")
    assert ownership_issues(tmp_path, {}) == ["Expected one test owner: studio/tests/transport/http.test.ts"]
    scopes = {"studio": {"tests": "studio/tests", "runner": "node"}}
    assert ownership_issues(tmp_path, scopes) == []
    scopes["overlap"] = {"tests": "studio/tests/transport", "runner": "node"}
    assert len(ownership_issues(tmp_path, scopes)) == 1
    scopes = {"bad": {"tests": "studio/tests", "runner": "invented"}}
    assert "Unknown test runner: bad" in ownership_issues(tmp_path, scopes)
