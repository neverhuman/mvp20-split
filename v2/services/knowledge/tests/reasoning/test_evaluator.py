from dataclasses import replace
from itertools import permutations

import pytest
from amphora_knowledge.reasoning.evaluator import Evaluator
from amphora_knowledge.reasoning.model import Atom, Fact, Limits, Program, ReasoningError, Rule, Seed

A, B, C, D = (Fact(Atom("sample", p, "target")) for p in ("a", "b", "c", "d"))


def program(*rules):
    return Program("synthetic-v1", tuple(rules))


def test_conjunction_and_transitive_proof_preserve_original_evidence():
    result = Evaluator().evaluate(program(Rule("ab", (A,), B), Rule("bc", (A, B), C)),
        (Seed(A, "observation-1"), Seed(A, "observation-2")))
    assert result.complete and result.assess(C).status == "supported"
    assert result.origins(C) == ("observation-1", "observation-2")
    assert result.proofs[-1].depth == 2
    assert result.assess(D).status == "unknown" and result.origins(D) == ()


def test_missing_conjunct_is_not_inferred_from_absence():
    result = Evaluator().evaluate(program(Rule("abc", (A, B), C)), (Seed(A, "a"),))
    assert result.complete and result.assess(C).status == "unknown"


def test_explicit_negative_is_not_negation_as_failure():
    rules = program(Rule("negative", (A.opposite(),), B))
    assert Evaluator().evaluate(rules, ()).assess(B).status == "unknown"
    result = Evaluator().evaluate(rules, (Seed(A.opposite(), "negative-observation"),))
    assert result.assess(A).status == "contradicted" and result.assess(B).status == "supported"


def test_conflict_does_not_explode_or_disappear():
    result = Evaluator().evaluate(program(), (Seed(A, "yes"), Seed(A.opposite(), "no")))
    finding = result.assess(A)
    assert finding.status == "unknown" and finding.positive and finding.negative and finding.conflict
    assert result.assess(B).status == "unknown" and not result.assess(B).conflict


@pytest.mark.parametrize("seeded", [False, True])
def test_cycles_terminate_and_require_actual_seeds(seeded):
    rules = program(Rule("ab", (A,), B), Rule("ba", (B,), A))
    result = Evaluator().evaluate(rules, (Seed(A, "root"),) if seeded else ())
    assert result.complete and result.assess(B).status == ("supported" if seeded else "unknown")
    assert result.origins(B) == (("root",) if seeded else ())


def test_rule_and_input_order_preserve_exact_closure_and_proof_choice():
    rules = (Rule("z", (A,), C), Rule("a", (B,), C), Rule("next", (C,), D))
    inputs = (Seed(A, "a"), Seed(B, "b"))
    outputs = [Evaluator().evaluate(program(*ordered), tuple(seeds))
        for ordered in permutations(rules) for seeds in permutations(inputs)]
    assert all(output == outputs[0] for output in outputs)
    assert outputs[0].origins(D) == ("b",)


@pytest.mark.parametrize("limits,code", [(Limits(depth=1), "reasoning_depth_limit"),
    (Limits(facts=2), "reasoning_fact_limit"), (Limits(work=2), "reasoning_work_limit")])
def test_exhaustion_never_reports_complete_support(limits, code):
    result = Evaluator(limits).evaluate(program(Rule("ab", (A,), B), Rule("bc", (B,), C)), (Seed(A, "root"),))
    assert not result.complete and result.stop_code == code
    assert result.assess(A).status == "unknown" and result.assess(C).status == "unknown"
    assert result.work <= limits.work


def test_exact_depth_bound_is_complete_if_no_further_productive_rule():
    result = Evaluator(Limits(depth=1)).evaluate(program(Rule("ab", (A,), B)), (Seed(A, "a"),))
    assert result.complete and result.assess(B).status == "supported"


def test_interrupted_round_does_not_publish_first_rule_only():
    result = Evaluator(Limits(work=2)).evaluate(program(Rule("ab", (A,), B), Rule("ac", (A,), C)),
        (Seed(A, "a"),))
    assert not result.complete and [proof.fact for proof in result.proofs] == [A]


def test_duplicate_seed_is_one_evidence_origin_not_replication():
    seed = Seed(A, "same")
    result = Evaluator().evaluate(program(), (seed, seed))
    assert result.origins(A) == ("same",) and len(result.proofs) == 1


def test_one_origin_cannot_silently_change_its_fact():
    with pytest.raises(ReasoningError, match="conflicting_origin_identity"):
        Evaluator().evaluate(program(), (Seed(A, "same"), Seed(B, "same")))


@pytest.mark.parametrize("factory", [lambda: Rule("empty", (), A), lambda: Rule("repeat", (A, A), B),
    lambda: Rule("list", [A], B), lambda: program(Rule("same", (A,), B), Rule("same", (B,), C)),
    lambda: Limits(depth=True), lambda: Limits(work=0), lambda: Limits(facts=8193),
    lambda: Fact(A.atom, "unknown"), lambda: Atom("", "b", "c"),
    lambda: Program("v", [Rule("r", (A,), B)]), lambda: Seed("not-a-fact", "s")])
def test_invalid_shapes_cannot_enter_kernel(factory):
    with pytest.raises(ReasoningError):
        factory()


def test_configured_input_bounds_fail_before_evaluation():
    with pytest.raises(ReasoningError, match="initial_fact_limit"):
        Evaluator(Limits(facts=1)).evaluate(program(), (Seed(A, "a"), Seed(B, "b")))
    with pytest.raises(ReasoningError, match="invalid_reasoning_input"):
        Evaluator().evaluate(program(), [Seed(A, "a")])
    with pytest.raises(ReasoningError, match="invalid_program"):
        Program("v", tuple(Rule(str(i), (A,), B) for i in range(257)))
    with pytest.raises(ReasoningError, match="invalid_ground_rule"):
        replace(Rule("r", (A,), B), premises=tuple(Fact(Atom("s", str(i), "o")) for i in range(17)))
