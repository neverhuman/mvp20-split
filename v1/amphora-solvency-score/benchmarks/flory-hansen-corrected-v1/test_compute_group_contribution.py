#!/usr/bin/env python3
"""Unit tests for flory-hansen-corrected-v1 compute_group_contribution.

R-B03 acceptance tests:
  T1  Hansen 2007 Table A.1 anchors (toluene, ethanol, acetone, water)
      within the tolerances documented in the instrument header.
  T2  Synthetic zero-volume pathology must ABSTAIN (volume floor), never
      divide, never return a value (the W7 denominator-collapse defect).
  T3  Uncovered fragment must be REJECTED (never silent zero volume).
  T4  Unparseable SMILES must be REJECTED.
  T5  Out-of-envelope values must be ABSTAINED, never returned (water VK).
  T6  Accounting identity: returned + abstained + rejected == batch size.
  T7  Determinism: two computations byte-identical.
"""
import sys
import unittest

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import compute_group_contribution as gc


class TestAnchors(unittest.TestCase):
    def test_t1_fedors_anchor_totals(self):
        for name, a in gc.ANCHORS.items():
            r = gc.compute(a["smiles"])
            self.assertEqual(r["fedors_status"], gc.RETURNED,
                             "%s fedors: %s" % (name, r["fedors_reason"]))
            got = r["values"]["fedors_delta_total"]
            ref = a["delta_total"]
            rel = abs(got - ref) / ref
            self.assertLessEqual(
                rel, a["fedors_rel_tol"],
                "%s fedors delta_total %.3f vs ref %.3f rel err %.3f > tol %.2f"
                % (name, got, ref, rel, a["fedors_rel_tol"]))
            # returned value must itself be in-envelope
            self.assertGreaterEqual(got, gc.ENVELOPE_MIN)
            self.assertLessEqual(got, gc.ENVELOPE_MAX)

    def test_t1_vk_anchor_components(self):
        for name in ("toluene", "ethanol", "acetone"):
            a = gc.ANCHORS[name]
            r = gc.compute(a["smiles"])
            self.assertEqual(r["hansen_status"], gc.RETURNED,
                             "%s hansen: %s" % (name, r["hansen_reason"]))
            for comp in ("delta_d", "delta_p", "delta_h"):
                got = r["values"]["hansen_" + comp]
                ref = a[comp]
                if ref >= gc.VK_COMPONENT_ABS_SWITCH:
                    rel = abs(got - ref) / ref
                    self.assertLessEqual(
                        rel, gc.VK_COMPONENT_REL_TOL,
                        "%s %s %.3f vs %.3f rel %.3f" % (name, comp, got, ref, rel))
                else:
                    self.assertLessEqual(
                        abs(got - ref), gc.VK_COMPONENT_ABS_TOL,
                        "%s %s %.3f vs %.3f abs" % (name, comp, got, ref))
                self.assertLessEqual(got, gc.ENVELOPE_MAX)
                self.assertGreaterEqual(got, 0.0)

    def test_t5_water_vk_abstains_out_of_envelope(self):
        a = gc.ANCHORS["water"]
        r = gc.compute(a["smiles"])
        self.assertEqual(r["hansen_status"], a["hansen_expected_status"])
        # no hansen value may be returned
        for k in r["values"]:
            self.assertFalse(k.startswith("hansen_"),
                             "out-of-envelope hansen value leaked: %s" % k)
        self.assertIn("out_of_envelope", r["hansen_reason"])


class TestPathologies(unittest.TestCase):
    def test_t2_synthetic_zero_volume_abstains(self):
        # 10 quaternary carbons: sum dV = 10 * (-19.2) = -192 cm3/mol.
        # This is exactly the W7 denominator-collapse pathology, injected
        # synthetically at the group level.
        r = gc.compute_from_groups({"C_quaternary": 10})
        self.assertEqual(r["fedors_status"], gc.ABSTAINED_VOLUME_FLOOR)
        self.assertEqual(r["hansen_status"], gc.ABSTAINED_VOLUME_FLOOR)
        self.assertEqual(r["values"], {}, "value must never be computed")
        self.assertIn("volume_floor", r["fedors_reason"])

    def test_t2_near_zero_positive_volume_abstains(self):
        # sum dV = 33.5 - 19.2 - 19.2 + 4.9... build: CH3 + 2x quaternary
        # + CH -> 33.5 - 38.4 - 1.0 = -5.9; and a sub-epsilon positive case:
        # CH3 + quaternary + CH2*? use groups summing to 0.5 cm3/mol:
        # ether_O (3.8) + CH (-1.0)*3 = 0.8 -> below 1.0 floor.
        r = gc.compute_from_groups({"ether_O": 1, "CH": 3})
        self.assertEqual(r["fedors_status"], gc.ABSTAINED_VOLUME_FLOOR)
        self.assertEqual(r["values"], {})

    def test_t3_uncovered_fragment_rejected(self):
        r = gc.compute("CP(C)C")  # phosphine: P not in the group table
        self.assertEqual(r["fedors_status"], gc.REJECTED_UNCOVERED_FRAGMENT)
        self.assertEqual(r["hansen_status"], gc.REJECTED_UNCOVERED_FRAGMENT)
        self.assertIn("uncovered_fragment", r["fedors_reason"])
        self.assertIn("P", r["fedors_reason"])
        self.assertEqual(r["values"], {})

    def test_t4_parse_error_rejected(self):
        r = gc.compute("not_a_smiles((")
        self.assertEqual(r["fedors_status"], gc.REJECTED_PARSE_ERROR)
        self.assertEqual(r["values"], {})

    def test_full_coverage_no_silent_zero(self):
        # every heavy atom of a normal molecule is claimed exactly once:
        # groups' Fedors volumes must reconstruct sum_V (no silent zeros).
        r = gc.compute("CCOC(=O)c1ccccc1Cl")  # ethyl chlorobenzoate
        self.assertEqual(r["fedors_status"], gc.RETURNED)
        table = {name: fed for name, _s, fed, _v in gc.GROUP_TABLE}
        table[gc.RING_NONAROMATIC_5PLUS[0]] = gc.RING_NONAROMATIC_5PLUS[1]
        table[gc.RING_NONAROMATIC_3_4[0]] = gc.RING_NONAROMATIC_3_4[1]
        v = sum(table[g][1] * n for g, n in r["groups"].items())
        v += sum(table[g][1] * n for g, n in r["ring_corrections"].items())
        self.assertAlmostEqual(v, r["sum_V_cm3_mol"], places=6)


class TestAccountingAndDeterminism(unittest.TestCase):
    BATCH = ["Cc1ccccc1", "CCO", "CC(C)=O", "O", "CP(C)C", "xx((",
             "CCOC(=O)C1CCC1", "COc1cc(OC(=O)C2COCC2C(C)=O)cc(C(C)=O)c1Cl"]

    def test_t6_accounting_identity(self):
        for method in ("fedors_status", "hansen_status"):
            returned = abstained = rejected = 0
            for smi in self.BATCH:
                s = gc.compute(smi)[method]
                if s == gc.RETURNED:
                    returned += 1
                elif s.startswith("ABSTAINED"):
                    abstained += 1
                elif s.startswith("REJECTED"):
                    rejected += 1
                else:
                    self.fail("unknown status " + s)
            self.assertEqual(returned + abstained + rejected, len(self.BATCH))

    def test_t7_determinism_two_replay(self):
        a = gc.canonical_json([gc.compute(s) for s in self.BATCH])
        b = gc.canonical_json([gc.compute(s) for s in self.BATCH])
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
