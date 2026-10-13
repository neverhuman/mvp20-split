"""Installed schema identity reuse must never broaden accepted provider output."""
import pytest
from amphora_agent_planning.providers import profiles
from amphora_contracts_planning import ProviderObservation, TaskProviderObservation
from .test_provider import attempt


FACTORIES = ('reference_proposal_schema', 'extraction_draft_schema', 'extraction_edit_schema',
             'campaign_draft_schema', 'checkpoint_draft_schema', 'checkpoint_followup_draft_schema',
             'campaign_curation_draft_schema')


@pytest.fixture(autouse=True)
def catalog_lifetime():
    profiles._profile_catalog.cache_clear()
    yield
    profiles._profile_catalog.cache_clear()


@pytest.mark.parametrize('name', FACTORIES)
def test_exact_identity_selects_only_its_existing_observation_family(name):
    profile = getattr(profiles, name)()
    binding = attempt(lambda value: value['context'].update(output_schema=profile.model_dump(mode='json')))
    assert profiles.OutputProfiles.supported(binding)
    expected = ProviderObservation if name == 'reference_proposal_schema' else TaskProviderObservation
    assert profiles.OutputProfiles.observation_model(binding) is expected
    for field, replacement in [('sha256', 'f' * 64), ('schema_id', 'unregistered.output')]:
        changed = profile.model_dump(mode='json') | {field: replacement}
        forged = attempt(lambda value: value['context'].update(output_schema=changed))
        assert not profiles.OutputProfiles.supported(forged)
        assert profiles.OutputProfiles.observation_model(forged) is ProviderObservation
        with pytest.raises(ValueError, match='unsupported_output_profile'):
            profiles.OutputProfiles.parse(b'{}', forged)
    assert profiles.OutputProfiles.supported(binding)


def test_repeated_checks_do_not_regenerate_static_schemas_or_retain_dtos(monkeypatch):
    binding = attempt()
    counts = dict.fromkeys(FACTORIES, 0)
    for name in FACTORIES:
        original = getattr(profiles, name)
        def counted(name=name, original=original):
            counts[name] += 1
            return original()
        monkeypatch.setattr(profiles, name, counted)
    for _ in range(20):
        assert profiles.OutputProfiles.supported(binding)
        assert profiles.OutputProfiles.observation_model(binding) is ProviderObservation
    assert all(count == 1 for count in counts.values())
    catalog = profiles._profile_catalog()
    assert type(catalog) is tuple and len(catalog) == 7
    assert all(type(name) is str and type(identity) is tuple and
               all(type(part) is str for part in identity) for name, identity in catalog)
    profiles._profile_catalog.cache_clear()
    assert profiles.OutputProfiles.supported(binding)
    assert all(count == 2 for count in counts.values())
