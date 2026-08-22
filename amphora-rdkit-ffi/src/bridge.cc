#include "bridge.h"

#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/SmilesParse/SmilesWrite.h>
#include <GraphMol/Descriptors/MolDescriptors.h>
#include <GraphMol/ChemTransforms/ChemTransforms.h>
#include <GraphMol/Fingerprints/MorganFingerprints.h>
#include <GraphMol/MolOps.h>
#include <GraphMol/RWMol.h>
#include <GraphMol/ChemReactions/ReactionParser.h>
#include <GraphMol/ChemReactions/ReactionRunner.h>
#include <RDGeneral/versions.h>
#include <DataStructs/ExplicitBitVect.h>

#include <algorithm>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace amphora::rdkit {
rust::String rdkit_version() { return std::string(RDKit::rdkitVersion); }

rust::String canonical_smiles(rust::Str input) {
  const std::string smiles(input.data(), input.size());
  std::unique_ptr<RDKit::ROMol> molecule(RDKit::SmilesToMol(smiles));
  if (!molecule) {
    throw std::invalid_argument("RDKit rejected the SMILES input");
  }
  return RDKit::MolToSmiles(*molecule, true);
}

namespace {
bool is_carbonyl_carbon(const RDKit::Atom &atom) {
  if (atom.getAtomicNum() != 6) {
    return false;
  }
  for (const auto bond : atom.getOwningMol().atomBonds(&atom)) {
    if (bond->getBondType() != RDKit::Bond::DOUBLE) {
      continue;
    }
    const auto *other = bond->getOtherAtom(&atom);
    if (other->getAtomicNum() == 8 || other->getAtomicNum() == 16) {
      return true;
    }
  }
  return false;
}

bool is_sulfonyl_sulfur(const RDKit::Atom &atom) {
  if (atom.getAtomicNum() != 16) {
    return false;
  }
  unsigned double_bonded_oxygen_count = 0;
  for (const auto bond : atom.getOwningMol().atomBonds(&atom)) {
    const auto *other = bond->getOtherAtom(&atom);
    if (bond->getBondType() == RDKit::Bond::DOUBLE &&
        other->getAtomicNum() == 8) {
      ++double_bonded_oxygen_count;
    }
  }
  return double_bonded_oxygen_count >= 2;
}

// R-N02: an amidine/guanidine carbon (C=N) delocalizes an attached nitrogen's
// lone pair exactly like the carbonyl/thiocarbonyl carbons above (C=O/C=S), so
// its N-H must not be counted as reactive amine hydrogen. Categorical
// classification only; whether guanidine N-H is exactly zero in a quantitative
// AHEW sense is explicitly left open (see the R-N02 repair receipts).
bool is_amidine_or_guanidine_carbon(const RDKit::Atom &atom) {
  if (atom.getAtomicNum() != 6) {
    return false;
  }
  for (const auto bond : atom.getOwningMol().atomBonds(&atom)) {
    if (bond->getBondType() != RDKit::Bond::DOUBLE) {
      continue;
    }
    if (bond->getOtherAtom(&atom)->getAtomicNum() == 7) {
      return true;
    }
  }
  return false;
}

bool is_nitrile_carbon(const RDKit::Atom &atom) {
  if (atom.getAtomicNum() != 6) {
    return false;
  }
  for (const auto bond : atom.getOwningMol().atomBonds(&atom)) {
    if (bond->getBondType() == RDKit::Bond::TRIPLE &&
        bond->getOtherAtom(&atom)->getAtomicNum() == 7) {
      return true;
    }
  }
  return false;
}

// W-FFI2: dicyandiamide (cyanoguanidine, CAS 461-58-5) is an amidine/guanidine
// carbon whose imine (C=N) nitrogen itself bears a cyanamide (nitrile)
// substituent -- N#C-N=C(NH2)(NH2). That electron-withdrawing nitrile
// competes for the guanidine carbon's pi system and collapses the symmetric,
// three-nitrogen "Y-delocalized" resonance that R-N02 relies on to zero
// ordinary guanidine/amidine N-H: guanidine's conjugate-acid pKaH is 13.6
// (delocalization-stabilized superbase), while cyanoguanidine's is only
// ~0.7 (predicted; chembk.com CAS 461-58-5 pKa listing) -- a >12 log-unit
// collapse in the exact resonance effect the exclusion is premised on.
// Mechanistically, Fedtke, Domaratius & Walter, "Curing of epoxy resins with
// dicyandiamide," Polymer Bulletin 31:429-435 (1993), DOI 10.1007/BF00329879,
// show dicyandiamide's terminal amino nitrogens nucleophilically ring-open a
// glycidyl-ether epoxide model compound to form N-alkyl adducts -- i.e. those
// N-H's ARE reactive amine hydrogens, not resonance-inert ones. Patent
// WO1993010168A1 (1993) states dicyandiamide has a defined functionality of
// four. This predicate is intentionally narrow: it fires ONLY on the specific
// cyanamide-on-imine-nitrogen motif that defines dicyandiamide, not on any
// amidine/guanidine carbon with a nitrile anywhere else in the molecule.
// Pure alkyl/aryl/H-substituted guanidines -- guanidine itself, DPG (CAS
// 102-06-7), DOTG (CAS 97-39-2), biguanide -- carry no such substituent and
// remain fully excluded (R-N02/V-N02c unchanged).
//
// W-FFI2 fire 2 (2026-08-06): the original predicate only inspected the
// DOUBLE-bonded (formal-imine) nitrogen for the nitrile substituent. Because
// dicyandiamide's three guanidine nitrogens are resonance-equivalent (that is
// the entire premise of Y-delocalization cited above), which one carries the
// formal C=N in a given SMILES/kekulization is a drawing convention, not a
// chemical fact -- RDKit does not tautomer-canonicalize on parse, so an
// equally valid tautomer SMILES for the identical molecule (e.g.
// "N=C(N)NC#N", double bond on a terminal nitrogen instead of the cyanamide
// nitrogen) left the cyanamide substituent on a SINGLY-bonded nitrogen and
// the old double-bond-only scan missed it, silently reproducing the original
// zeroed-DICY defect on chemically-identical input. The predicate now scans
// EVERY nitrogen directly bonded to the guanidine/amidine carbon (regardless
// of that bond's order), so detection is invariant to which nitrogen a
// particular kekulization happens to double-bond. Narrowness is unchanged:
// the nitrile must still be bonded to a nitrogen that is itself directly
// bonded to the guanidine carbon (see the n-methylguanidine and
// remote-nitrile-guanidine adversarial regression probes).
bool is_cyanamide_substituted_guanidine_carbon(const RDKit::Atom &atom) {
  if (atom.getAtomicNum() != 6) {
    return false;
  }
  const RDKit::ROMol &owning_mol = atom.getOwningMol();
  for (const auto guanidine_nitrogen : owning_mol.atomNeighbors(&atom)) {
    if (guanidine_nitrogen->getAtomicNum() != 7) {
      continue;
    }
    for (const auto substituent :
         owning_mol.atomNeighbors(guanidine_nitrogen)) {
      if (substituent->getIdx() == atom.getIdx()) {
        continue;
      }
      if (is_nitrile_carbon(*substituent)) {
        return true;
      }
    }
  }
  return false;
}

unsigned count_reactive_amine_hydrogens(const RDKit::ROMol &molecule) {
  unsigned count = 0;
  for (const auto atom : molecule.atoms()) {
    if (atom->getAtomicNum() != 7 || atom->getIsAromatic() ||
        atom->getFormalCharge() != 0) {
      continue;
    }
    const unsigned hydrogen_count = atom->getTotalNumHs();
    if (hydrogen_count == 0) {
      continue;
    }
    bool excluded = false;
    for (const auto neighbor : molecule.atomNeighbors(atom)) {
      if (is_carbonyl_carbon(*neighbor) || is_sulfonyl_sulfur(*neighbor)) {
        excluded = true;
        break;
      }
      if (is_amidine_or_guanidine_carbon(*neighbor) &&
          !is_cyanamide_substituted_guanidine_carbon(*neighbor)) {
        excluded = true;
        break;
      }
    }
    if (!excluded) {
      count += hydrogen_count;
    }
  }
  return count;
}

unsigned count_oxirane_rings(const RDKit::ROMol &molecule) {
  unsigned count = 0;
  for (const auto oxygen : molecule.atoms()) {
    if (oxygen->getAtomicNum() != 8 || oxygen->getDegree() != 2 ||
        oxygen->getFormalCharge() != 0) {
      continue;
    }
    auto neighbors = molecule.atomNeighbors(oxygen);
    auto first = neighbors.begin();
    const auto *carbon_a = *first;
    ++first;
    const auto *carbon_b = *first;
    if (carbon_a->getAtomicNum() != 6 || carbon_b->getAtomicNum() != 6) {
      continue;
    }
    const auto *carbon_bond =
        molecule.getBondBetweenAtoms(carbon_a->getIdx(), carbon_b->getIdx());
    const auto *oxygen_bond_a =
        molecule.getBondBetweenAtoms(oxygen->getIdx(), carbon_a->getIdx());
    const auto *oxygen_bond_b =
        molecule.getBondBetweenAtoms(oxygen->getIdx(), carbon_b->getIdx());
    if (carbon_bond && oxygen_bond_a && oxygen_bond_b &&
        carbon_bond->getBondType() == RDKit::Bond::SINGLE &&
        oxygen_bond_a->getBondType() == RDKit::Bond::SINGLE &&
        oxygen_bond_b->getBondType() == RDKit::Bond::SINGLE) {
      ++count;
    }
  }
  return count;
}

std::string serialize_bits(const ExplicitBitVect &fingerprint) {
  IntVect bits;
  fingerprint.getOnBits(bits);
  std::ostringstream output;
  for (std::size_t index = 0; index < bits.size(); ++index) {
    if (index > 0) {
      output << ',';
    }
    output << bits[index];
  }
  return output.str();
}
} // namespace

rust::String molecule_facts_record(rust::Str input) {
  const std::string smiles(input.data(), input.size());
  std::unique_ptr<RDKit::ROMol> molecule(RDKit::SmilesToMol(smiles));
  if (!molecule) {
    throw std::invalid_argument("RDKit rejected the SMILES input");
  }
  for (const auto atom : molecule->atoms()) {
    if (atom->getAtomicNum() == 0 || atom->hasQuery()) {
      throw std::invalid_argument("wildcard and query atoms are unsupported");
    }
  }
  std::ostringstream record;
  record << RDKit::MolToSmiles(*molecule, true) << '\t'
         << RDKit::Descriptors::calcMolFormula(*molecule, true, true) << '\t'
         << std::setprecision(15) << RDKit::Descriptors::calcAMW(*molecule)
         << '\t' << count_oxirane_rings(*molecule) << '\t'
         << count_reactive_amine_hydrogens(*molecule);
  return record.str();
}

rust::String novelty_record(rust::Str input) {
  const std::string smiles(input.data(), input.size());
  std::unique_ptr<RDKit::ROMol> molecule(RDKit::SmilesToMol(smiles));
  if (!molecule) {
    throw std::invalid_argument("RDKit rejected the SMILES input");
  }
  for (const auto atom : molecule->atoms()) {
    if (atom->getAtomicNum() == 0 || atom->hasQuery()) {
      throw std::invalid_argument("wildcard and query atoms are unsupported");
    }
  }
  std::unique_ptr<ExplicitBitVect> fingerprint(
      RDKit::MorganFingerprints::getFingerprintAsBitVect(
          *molecule, 2, 2048, nullptr, nullptr, true));
  std::unique_ptr<RDKit::ROMol> scaffold(RDKit::MurckoDecompose(*molecule));
  std::string scaffold_smiles;
  std::string scaffold_bits;
  if (scaffold && scaffold->getNumAtoms() > 0) {
    RDKit::MolOps::fastFindRings(*scaffold);
    scaffold_smiles = RDKit::MolToSmiles(*scaffold, true);
    std::unique_ptr<ExplicitBitVect> scaffold_fingerprint(
        RDKit::MorganFingerprints::getFingerprintAsBitVect(
            *scaffold, 2, 2048, nullptr, nullptr, true));
    scaffold_bits = serialize_bits(*scaffold_fingerprint);
  }
  std::ostringstream record;
  record << RDKit::MolToSmiles(*molecule, true) << '\t' << scaffold_smiles
         << '\t' << serialize_bits(*fingerprint) << '\t' << scaffold_bits;
  return record.str();
}

rust::String reaction_products(rust::Str reaction_smarts_input,
                               rust::Str reactants_input) {
  const std::string reaction_smarts(reaction_smarts_input.data(),
                                    reaction_smarts_input.size());
  const std::string encoded_reactants(reactants_input.data(),
                                      reactants_input.size());
  std::unique_ptr<RDKit::ChemicalReaction> reaction(
      RDKit::RxnSmartsToChemicalReaction(reaction_smarts));
  if (!reaction) {
    throw std::invalid_argument("RDKit rejected the reaction SMARTS");
  }
  reaction->initReactantMatchers();

  RDKit::MOL_SPTR_VECT reactants;
  std::size_t start = 0;
  while (start <= encoded_reactants.size()) {
    const auto end = encoded_reactants.find('\x1e', start);
    const auto token = encoded_reactants.substr(
        start, end == std::string::npos ? std::string::npos : end - start);
    if (token.empty()) {
      throw std::invalid_argument("reaction reactant is empty");
    }
    std::unique_ptr<RDKit::ROMol> molecule(RDKit::SmilesToMol(token));
    if (!molecule) {
      throw std::invalid_argument("RDKit rejected a reaction reactant");
    }
    reactants.push_back(RDKit::ROMOL_SPTR(molecule.release()));
    if (end == std::string::npos) {
      break;
    }
    start = end + 1;
  }
  if (reactants.size() != reaction->getNumReactantTemplates()) {
    throw std::invalid_argument("reactant count does not match reaction SMARTS");
  }

  std::vector<std::string> canonical_products;
  for (auto &product_set : reaction->runReactants(reactants)) {
    if (product_set.size() != 1 || !product_set.front()) {
      continue;
    }
    try {
      RDKit::RWMol product(*product_set.front());
      RDKit::MolOps::sanitizeMol(product);
      const auto smiles = RDKit::MolToSmiles(product, true);
      if (!smiles.empty() && smiles.find('.') == std::string::npos) {
        canonical_products.push_back(smiles);
      }
    } catch (const std::exception &) {
      // Invalid products are explicit rejections at the Rust boundary.
    }
  }
  std::sort(canonical_products.begin(), canonical_products.end());
  canonical_products.erase(
      std::unique(canonical_products.begin(), canonical_products.end()),
      canonical_products.end());
  std::ostringstream output;
  for (std::size_t index = 0; index < canonical_products.size(); ++index) {
    if (index > 0) {
      output << '\n';
    }
    output << canonical_products[index];
  }
  return output.str();
}
} // namespace amphora::rdkit
