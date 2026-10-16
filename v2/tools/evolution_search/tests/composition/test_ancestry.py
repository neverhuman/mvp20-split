"""Retained closure bounds remain independent of direct-parent grouping."""
import pytest

from amphora_evolution_search.composition.ancestry import Publication,PublicationLedger


def test_shared_ancestry_and_input_carrier_count_once():
    ledger=PublicationLedger()
    for item in (Publication("source",10),Publication("carrier",20,("source",)),
        Publication("left",30,("source","carrier")),Publication("right",40,("carrier",)),
        Publication("result",50,("left","right","carrier"))):ledger.include(item)
    footprint=ledger.retained(("result","left","result"))
    assert (footprint.artifacts,footprint.bytes,footprint.largest_ancestor_count)==(5,150,4)


def test_unknown_parent_is_not_assumed_to_be_a_leaf():
    ledger=PublicationLedger()
    with pytest.raises(ValueError,match="ancestry_incomplete"):
        ledger.include(Publication("result",1,("external",)))
    ledger.include(Publication("external",2))
    ledger.include(Publication("result",1,("external",)))
    assert ledger.retained(("result",)).bytes==3


def test_idempotent_identity_rejects_changed_content_or_ancestry():
    ledger=PublicationLedger();leaf=Publication("leaf",1)
    ledger.include(leaf);ledger.include(leaf)
    with pytest.raises(ValueError,match="publication_conflict"):ledger.include(Publication("leaf",2))
    assert ledger.retained(("leaf",)).artifacts==1


def test_grouping_cannot_hide_4096_ancestors():
    ledger=PublicationLedger()
    # 4,062 leaves + 34 grouping artifacts + the result exceed 4,096 identities.
    leaves=tuple("leaf/"+str(i) for i in range(4062))
    for leaf in leaves:ledger.include(Publication(leaf,1))
    groups=[]
    for offset in range(0,len(leaves),120):
        name="group/"+str(offset);groups.append(name)
        ledger.include(Publication(name,1,leaves[offset:offset+120]))
    with pytest.raises(ValueError,match="retained_ancestry"):
        ledger.include(Publication("result",1,tuple(groups)))
    # Failed addition does not contaminate a later valid assessment.
    ledger.include(Publication("valid",1,tuple(groups[:-1])))
    assert ledger.retained(("valid",)).largest_ancestor_count==3993


def test_exact_4096_identity_boundary():
    ledger=PublicationLedger()
    leaves=tuple(str(i) for i in range(4061))
    for leaf in leaves:ledger.include(Publication(leaf,0))
    groups=[]
    for offset in range(0,len(leaves),120):
        name="group/"+str(offset);groups.append(name)
        ledger.include(Publication(name,0,leaves[offset:offset+120]))
    ledger.include(Publication("result",262144,tuple(groups)))
    assert ledger.retained(("result",)).largest_ancestor_count==4095


@pytest.mark.parametrize("arguments",[("x",True,()),("x",262145,()),("x",1,("x",)),
    ("x",1,("p","p")),("x",1,tuple(str(i) for i in range(129)))])
def test_invalid_publication(arguments):
    with pytest.raises(ValueError):Publication(*arguments)


def test_retained_roots_require_explicit_known_identity():
    with pytest.raises(ValueError,match="retained_roots"):PublicationLedger().retained(("missing",))
