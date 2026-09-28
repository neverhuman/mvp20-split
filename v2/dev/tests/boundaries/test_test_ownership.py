from run_tests import ownership_issues


def test_repository_test_ownership():
    assert ownership_issues() == []


def test_orphan_and_overlapping_test_owners_are_rejected(tmp_path):
    tests = tmp_path / "services/example/tests"
    tests.mkdir(parents=True)
    (tests / "test_behavior.py").write_text("def test_behavior(): pass")
    assert ownership_issues(tmp_path, {}) == [
        "Expected one test owner: services/example/tests/test_behavior.py"
    ]
    scopes = {"example": {"tests": "services/example/tests"}}
    assert ownership_issues(tmp_path, scopes) == []
    scopes["duplicate"] = {"tests": "services/example"}
    assert len(ownership_issues(tmp_path, scopes)) == 1
