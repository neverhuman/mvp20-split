"""Deterministic monotonic closure; no variable expansion or executable expressions."""

from .model import Closure, Limits, Program, Proof, ReasoningError, Seed


class Evaluator:
    def __init__(self, limits=None):
        limits = Limits() if limits is None else limits
        if type(limits) is not Limits:
            raise ReasoningError("invalid_reasoning_limit")
        self.limits = limits

    def evaluate(self, program, seeds):
        if (type(program) is not Program or type(seeds) is not tuple or len(seeds) > 8192
                or any(type(seed) is not Seed for seed in seeds)):
            raise ReasoningError("invalid_reasoning_input")
        grouped, origins = {}, {}
        for seed in sorted(seeds):
            if seed.origin in origins and origins[seed.origin] != seed.fact:
                raise ReasoningError("conflicting_origin_identity")
            origins[seed.origin] = seed.fact
            grouped.setdefault(seed.fact, set()).add(seed.origin)
        if len(grouped) > self.limits.facts:
            raise ReasoningError("initial_fact_limit")
        proofs = {fact: Proof(fact, 0, None, (), tuple(sorted(refs))) for fact, refs in grouped.items()}
        work = 0

        def finish(code=None):
            return Closure(program, tuple(proofs[fact] for fact in sorted(proofs)), code is None, code, work)

        # All candidates in a round consume only the preceding complete round.
        # An interrupted round publishes none of its candidates, avoiding order bias.
        while True:
            pending = {}
            for rule in program.rules:
                if work >= self.limits.work:
                    return finish("reasoning_work_limit")
                work += 1
                if rule.conclusion in proofs:
                    continue
                matched = True
                for premise in rule.premises:
                    if work >= self.limits.work:
                        return finish("reasoning_work_limit")
                    work += 1
                    if premise not in proofs:
                        matched = False
                        break
                if matched:
                    depth = max(proofs[premise].depth for premise in rule.premises) + 1
                    candidate = Proof(rule.conclusion, depth, rule.rule_id, rule.premises, ())
                    prior = pending.get(rule.conclusion)
                    if prior is None or (depth, rule.rule_id) < (prior.depth, prior.rule_id):
                        pending[rule.conclusion] = candidate
            if not pending:
                return finish()
            if any(proof.depth > self.limits.depth for proof in pending.values()):
                return finish("reasoning_depth_limit")
            if len(proofs) + len(pending) > self.limits.facts:
                return finish("reasoning_fact_limit")
            proofs.update(pending)
