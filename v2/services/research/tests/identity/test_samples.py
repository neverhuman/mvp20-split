import json

import pytest
from amphora_contracts_research import CandidateRevision, SampleIdentity
from amphora_research.identity.questions import ResearchIdentityError
from amphora_research.identity.samples import CandidateDefinition, IdentityMatch, SampleDefinition


def records():
    scope = {"tenant_id": "test", "project_id": "samples"}
    artifact = {"artifact_id": "synthetic", "scope": scope, "sha256": "b" * 64,
                "media_type": "application/json", "size_bytes": 2,
                "schema_ref": {"schema_id": "synthetic", "version": "1", "sha256": "a" * 64}}
    ref = {"scope": scope, "candidate_id": "candidate", "revision": 1}
    candidate = {"wire_version": "1", "reference": ref, "representation": artifact, "supersedes": None}
    sample = {"wire_version": "1", "reference": {"scope": scope, "sample_id": "specimen", "revision": 1},
              "candidate": ref, "material_state": None, "identity_evidence": artifact, "supersedes": None}
    return json.loads(json.dumps([candidate, sample]))


def definitions(c=None, s=None):
    if c is None:
        c, s = records()
    return (CandidateDefinition(CandidateRevision.model_validate_json(json.dumps(c))),
            SampleDefinition(SampleIdentity.model_validate_json(json.dumps(s))))


def test_match_does_not_invent_material_state_or_scientific_acceptance():
    c, s = definitions()
    result = IdentityMatch.reconcile(c.record.reference, s.record.reference, c, s)
    assert (result.disposition, result.reason) == ("matched", "exact_identity_only")
    assert s.record.material_state is None


@pytest.mark.parametrize(("missing", "reason"), [("candidate", "unknown_candidate"), ("sample", "unknown_sample")])
def test_unknown_identity_quarantines_without_fabricating_entity(missing, reason):
    c, s = definitions()
    result = IdentityMatch.reconcile(c.record.reference, s.record.reference,
                                    None if missing == "candidate" else c, None if missing == "sample" else s)
    assert (result.disposition, result.reason) == ("quarantined", reason)


@pytest.mark.parametrize(("changed", "reason"), [
    ("scope", "scope_mismatch"), ("candidate", "candidate_revision_mismatch"),
    ("sample", "sample_revision_mismatch"), ("binding", "sample_candidate_mismatch"),
])
def test_exact_revision_and_scope_are_required(changed, reason):
    c, s = definitions()
    cref, sref = c.record.reference, s.record.reference
    if changed == "scope":
        sref = sref.model_copy(update={"scope": sref.scope.model_copy(update={"project_id": "foreign"})})
    elif changed == "candidate":
        cref = cref.model_copy(update={"revision": 2})
    elif changed == "sample":
        sref = sref.model_copy(update={"revision": 2})
    else:
        s = SampleDefinition(s.record.model_copy(update={"candidate": cref.model_copy(update={"revision": 2})}))
    result = IdentityMatch.reconcile(cref, sref, c, s)
    assert result.disposition == "quarantined"
    assert result.reason == reason


@pytest.mark.parametrize(("owner", "field", "reason"), [
    (0, "representation", "representation_scope_mismatch"),
    (1, "identity_evidence", "sample_scope_mismatch"),
    (1, "candidate", "sample_scope_mismatch"),
])
def test_cross_scope_record_is_invalid(owner, field, reason):
    data = records()
    data[owner][field]["scope"]["project_id"] = "foreign"
    with pytest.raises(ResearchIdentityError, match=reason):
        definitions(*data)


@pytest.mark.parametrize("owner", [0, 1])
def test_corrections_require_exact_predecessor(owner):
    data = records()
    data[owner]["reference"]["revision"] = 2
    with pytest.raises(ResearchIdentityError, match="missing_predecessor"):
        definitions(*data)
    data[owner]["supersedes"] = dict(data[owner]["reference"])
    with pytest.raises(ResearchIdentityError, match="invalid_predecessor"):
        definitions(*data)
    data[owner]["supersedes"]["revision"] = 1
    definitions(*data)


def test_foreign_material_state_never_becomes_sample_context():
    c, s = records()
    s["material_state"] = {"scope": {"tenant_id": "test", "project_id": "foreign"},
                           "material_state_id": "prepared", "revision": 1}
    with pytest.raises(ResearchIdentityError, match="material_state_scope_mismatch"):
        definitions(c, s)
