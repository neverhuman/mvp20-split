#pragma once

#include "rust/cxx.h"

namespace amphora::rdkit {
rust::String rdkit_version();
rust::String canonical_smiles(rust::Str input);
rust::String molecule_facts_record(rust::Str input);
rust::String novelty_record(rust::Str input);
rust::String reaction_products(rust::Str reaction_smarts, rust::Str reactants);
}
