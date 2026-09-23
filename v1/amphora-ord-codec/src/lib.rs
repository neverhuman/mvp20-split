#![forbid(unsafe_code)]

use flate2::read::GzDecoder;
use prost::Message;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::{self, Read};
use thiserror::Error;

#[allow(clippy::doc_lazy_continuation)]
pub mod ord {
    include!(concat!(env!("OUT_DIR"), "/ord.rs"));
}

pub const ORD_SCHEMA_VERSION: &str = "0.6.3";
pub const ORD_SCHEMA_TAG_OBJECT: &str = "0a6c92558898156f06365220d3acbe2bea0a1e69";
pub const ORD_SCHEMA_SOURCE_COMMIT: &str = "7eb730963d7a47e1d6a6c5366806ad2133422df4";
pub const DATASET_PROTO_SHA256: &str =
    "60f44fbf7b01c0e0d219d7017254c64034eaee8d739a148f33d53c36ecc52b11";
pub const REACTION_PROTO_SHA256: &str =
    "f1546142d8b727f9c05aee7176287f1b0ff172966d125cd1f44b1a910530ceea";
pub const TEST_PROTO_SHA256: &str =
    "86cfe00045a1439463f33fc132f578e8eab942f7cc82bf6b7207e685f69c01e4";
pub const DESCRIPTOR_SET_BYTES: &[u8] =
    include_bytes!(concat!(env!("OUT_DIR"), "/ord-schema-v0.6.3.descriptor.pb"));

#[derive(Debug, Error)]
pub enum OrdCodecError {
    #[error("ORD gzip stream exceeds the configured decompression bound")]
    DecompressionLimit,
    #[error("ORD gzip stream: {0}")]
    Gzip(#[from] io::Error),
    #[error("ORD protobuf: {0}")]
    Protobuf(#[from] prost::DecodeError),
    #[error("ORD protobuf wire format is malformed")]
    WireFormat,
    #[error("ORD dataset contains reaction references instead of embedded reactions")]
    DatasetReferencesOnly,
    #[error("ORD dataset reaction scan does not match the decoded dataset")]
    ReactionScanMismatch,
    #[error("ORD dataset ID is empty")]
    MissingId,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RawReactionMessage {
    pub ordinal: usize,
    pub bytes: Vec<u8>,
    pub sha256: String,
}

#[derive(Debug, Clone)]
pub struct DecodedDataset {
    pub dataset: ord::Dataset,
    pub raw_reactions: Vec<RawReactionMessage>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct StructuredCompound {
    pub structure: String,
    pub structure_kind: String,
    pub reaction_role: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct StructuredReactionCandidate {
    pub dataset_id: String,
    pub reaction_id: String,
    pub reaction_ordinal: u64,
    pub raw_reaction_message_sha256: String,
    pub mapped_reaction_identifier: String,
    pub mapped_reaction_identifier_kind: String,
    pub input_compounds: Vec<StructuredCompound>,
    pub product: StructuredCompound,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum StructuralExclusionReason {
    MissingReactionId,
    MissingMappedReactionIdentifier,
    AmbiguousMappedReactionIdentifier,
    CrudeInputUnsupported,
    MissingInputStructure,
    MultiComponentInput,
    MissingProductStructure,
    MultiComponentProduct,
    AmbiguousProductOutcome,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct StructuralReactionExclusion {
    pub dataset_id: String,
    pub reaction_id: String,
    pub reaction_ordinal: u64,
    pub raw_reaction_message_sha256: String,
    pub reason: StructuralExclusionReason,
}

pub fn classify_dataset_reactions(
    decoded: &DecodedDataset,
) -> Vec<Result<StructuredReactionCandidate, StructuralReactionExclusion>> {
    decoded
        .dataset
        .reactions
        .iter()
        .zip(&decoded.raw_reactions)
        .map(|(reaction, raw)| classify_reaction(&decoded.dataset.dataset_id, reaction, raw))
        .collect()
}

fn classify_reaction(
    dataset_id: &str,
    reaction: &ord::Reaction,
    raw: &RawReactionMessage,
) -> Result<StructuredReactionCandidate, StructuralReactionExclusion> {
    let exclusion = |reason| StructuralReactionExclusion {
        dataset_id: dataset_id.to_owned(),
        reaction_id: reaction.reaction_id.clone(),
        reaction_ordinal: raw.ordinal as u64,
        raw_reaction_message_sha256: raw.sha256.clone(),
        reason,
    };
    if reaction.reaction_id.trim().is_empty() {
        return Err(exclusion(StructuralExclusionReason::MissingReactionId));
    }
    let mapped =
        reaction
            .identifiers
            .iter()
            .filter(|identifier| {
                identifier.is_mapped == Some(true)
                    && matches!(
                    ord::reaction_identifier::ReactionIdentifierType::try_from(identifier.r#type),
                    Ok(ord::reaction_identifier::ReactionIdentifierType::ReactionSmiles
                        | ord::reaction_identifier::ReactionIdentifierType::ReactionCxsmiles)
                ) && !identifier.value.trim().is_empty()
            })
            .collect::<Vec<_>>();
    if mapped.is_empty() {
        return Err(exclusion(
            StructuralExclusionReason::MissingMappedReactionIdentifier,
        ));
    }
    if mapped.len() != 1 {
        return Err(exclusion(
            StructuralExclusionReason::AmbiguousMappedReactionIdentifier,
        ));
    }
    let mut input_keys = reaction.inputs.keys().collect::<Vec<_>>();
    input_keys.sort();
    let mut inputs = Vec::new();
    for key in input_keys {
        let input = &reaction.inputs[key];
        if !input.crude_components.is_empty() {
            return Err(exclusion(StructuralExclusionReason::CrudeInputUnsupported));
        }
        for compound in &input.components {
            let structured = structured_compound(&compound.identifiers, compound.reaction_role)
                .ok_or_else(|| exclusion(StructuralExclusionReason::MissingInputStructure))?;
            if structured.structure.contains('.') {
                return Err(exclusion(StructuralExclusionReason::MultiComponentInput));
            }
            inputs.push(structured);
        }
    }
    if inputs.is_empty() {
        return Err(exclusion(StructuralExclusionReason::MissingInputStructure));
    }
    if reaction.outcomes.len() != 1 {
        return Err(exclusion(
            StructuralExclusionReason::AmbiguousProductOutcome,
        ));
    }
    let product_role = reaction.outcomes[0]
        .products
        .iter()
        .filter(|product| {
            ord::reaction_role::ReactionRoleType::try_from(product.reaction_role)
                .is_ok_and(|role| role == ord::reaction_role::ReactionRoleType::Product)
        })
        .collect::<Vec<_>>();
    let desired = product_role
        .iter()
        .copied()
        .filter(|product| product.is_desired_product == Some(true))
        .collect::<Vec<_>>();
    let product = match (desired.as_slice(), product_role.as_slice()) {
        ([product], _) => *product,
        ([], [product]) => *product,
        _ => {
            return Err(exclusion(
                StructuralExclusionReason::AmbiguousProductOutcome,
            ))
        }
    };
    if product_role.is_empty() {
        return Err(exclusion(
            StructuralExclusionReason::AmbiguousProductOutcome,
        ));
    }
    let product = structured_compound(&product.identifiers, product.reaction_role)
        .ok_or_else(|| exclusion(StructuralExclusionReason::MissingProductStructure))?;
    if product.structure.contains('.') {
        return Err(exclusion(StructuralExclusionReason::MultiComponentProduct));
    }
    let mapped_kind = ord::reaction_identifier::ReactionIdentifierType::try_from(mapped[0].r#type)
        .expect("mapped identifier kind was filtered")
        .as_str_name()
        .to_owned();
    Ok(StructuredReactionCandidate {
        dataset_id: dataset_id.to_owned(),
        reaction_id: reaction.reaction_id.clone(),
        reaction_ordinal: raw.ordinal as u64,
        raw_reaction_message_sha256: raw.sha256.clone(),
        mapped_reaction_identifier: mapped[0].value.clone(),
        mapped_reaction_identifier_kind: mapped_kind,
        input_compounds: inputs,
        product,
    })
}

fn structured_compound(
    identifiers: &[ord::CompoundIdentifier],
    reaction_role: i32,
) -> Option<StructuredCompound> {
    use ord::compound_identifier::CompoundIdentifierType::{Cxsmiles, Smiles};
    let select = |wanted| {
        let values = identifiers
            .iter()
            .filter(|identifier| {
                ord::compound_identifier::CompoundIdentifierType::try_from(identifier.r#type)
                    .is_ok_and(|kind| kind == wanted)
            })
            .map(|identifier| identifier.value.trim())
            .filter(|value| !value.is_empty())
            .collect::<std::collections::BTreeSet<_>>();
        (values.len() == 1).then(|| (wanted, *values.first().expect("one identifier")))
    };
    let supported = select(Smiles).or_else(|| select(Cxsmiles))?;
    let role = ord::reaction_role::ReactionRoleType::try_from(reaction_role)
        .map(|role| role.as_str_name().to_owned())
        .unwrap_or_else(|_| "UNSPECIFIED".into());
    Some(StructuredCompound {
        structure: supported.1.to_owned(),
        structure_kind: supported.0.as_str_name().to_owned(),
        reaction_role: role,
    })
}

/// Decompress and decode one gzip-compressed ORD Dataset while enforcing a
/// strict output bound. Reading to EOF makes the gzip decoder validate CRC and
/// stream completion before protobuf decoding starts.
pub fn decode_gzip_dataset(
    compressed: &[u8],
    maximum_decompressed_bytes: u64,
) -> Result<DecodedDataset, OrdCodecError> {
    let bytes = decompress_gzip_bounded(compressed, maximum_decompressed_bytes)?;
    decode_dataset(&bytes)
}

/// Validate gzip CRC/EOF and return the decompressed bytes only when the
/// configured output limit is respected.
pub fn decompress_gzip_bounded(
    compressed: &[u8],
    maximum_decompressed_bytes: u64,
) -> Result<Vec<u8>, OrdCodecError> {
    let decoder = GzDecoder::new(compressed);
    let mut bounded = decoder.take(maximum_decompressed_bytes.saturating_add(1));
    let mut bytes = Vec::new();
    bounded.read_to_end(&mut bytes)?;
    if bytes.len() as u64 > maximum_decompressed_bytes {
        return Err(OrdCodecError::DecompressionLimit);
    }
    Ok(bytes)
}

/// Decode an ORD Dataset and independently scan the raw wire message so every
/// embedded `Dataset.reactions` payload can retain its exact source hash.
pub fn decode_dataset(bytes: &[u8]) -> Result<DecodedDataset, OrdCodecError> {
    let raw_reactions = scan_raw_reactions(bytes)?;
    let dataset = ord::Dataset::decode(bytes)?;
    if dataset.dataset_id.trim().is_empty() {
        return Err(OrdCodecError::MissingId);
    }
    if dataset.reactions.is_empty() && !dataset.reaction_ids.is_empty() {
        return Err(OrdCodecError::DatasetReferencesOnly);
    }
    if raw_reactions.len() != dataset.reactions.len() {
        return Err(OrdCodecError::ReactionScanMismatch);
    }
    for (raw, decoded) in raw_reactions.iter().zip(&dataset.reactions) {
        let cross_decoded = ord::Reaction::decode(raw.bytes.as_slice())?;
        if cross_decoded.reaction_id != decoded.reaction_id {
            return Err(OrdCodecError::ReactionScanMismatch);
        }
    }
    Ok(DecodedDataset {
        dataset,
        raw_reactions,
    })
}

/// Scan the protobuf wire representation and copy the exact payload bytes for
/// every length-delimited field 3 (`Dataset.reactions`) in source order.
pub fn scan_raw_reactions(bytes: &[u8]) -> Result<Vec<RawReactionMessage>, OrdCodecError> {
    let mut cursor = 0_usize;
    let mut reactions = Vec::new();
    while cursor < bytes.len() {
        let key = read_varint(bytes, &mut cursor)?;
        let field = key >> 3;
        let wire_type = (key & 0x07) as u8;
        if field == 3 {
            if wire_type != 2 {
                return Err(OrdCodecError::WireFormat);
            }
            let length = read_varint(bytes, &mut cursor)? as usize;
            let end = cursor
                .checked_add(length)
                .filter(|end| *end <= bytes.len())
                .ok_or(OrdCodecError::WireFormat)?;
            let payload = bytes[cursor..end].to_vec();
            reactions.push(RawReactionMessage {
                ordinal: reactions.len(),
                sha256: sha256(&payload),
                bytes: payload,
            });
            cursor = end;
        } else {
            skip_field(bytes, &mut cursor, wire_type)?;
        }
    }
    Ok(reactions)
}

pub fn descriptor_set_sha256() -> String {
    sha256(DESCRIPTOR_SET_BYTES)
}

fn read_varint(bytes: &[u8], cursor: &mut usize) -> Result<u64, OrdCodecError> {
    let mut value = 0_u64;
    for shift in (0..=63).step_by(7) {
        let byte = *bytes.get(*cursor).ok_or(OrdCodecError::WireFormat)?;
        *cursor += 1;
        value |= u64::from(byte & 0x7f) << shift;
        if byte & 0x80 == 0 {
            return Ok(value);
        }
    }
    Err(OrdCodecError::WireFormat)
}

fn skip_field(bytes: &[u8], cursor: &mut usize, wire_type: u8) -> Result<(), OrdCodecError> {
    let length = match wire_type {
        0 => {
            read_varint(bytes, cursor)?;
            return Ok(());
        }
        1 => 8,
        2 => read_varint(bytes, cursor)? as usize,
        5 => 4,
        _ => return Err(OrdCodecError::WireFormat),
    };
    *cursor = cursor
        .checked_add(length)
        .filter(|end| *end <= bytes.len())
        .ok_or(OrdCodecError::WireFormat)?;
    Ok(())
}

fn sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn encoded_dataset() -> Vec<u8> {
        let dataset = ord::Dataset {
            name: "fixture".into(),
            description: String::new(),
            reactions: vec![ord::Reaction {
                reaction_id: "ord-fixture-1".into(),
                ..Default::default()
            }],
            reaction_ids: Vec::new(),
            dataset_id: "ord-fixture-dataset".into(),
        };
        dataset.encode_to_vec()
    }

    #[test]
    fn raw_scan_hashes_exact_embedded_reaction_bytes() {
        let bytes = encoded_dataset();
        let decoded = decode_dataset(&bytes).unwrap();
        assert_eq!(decoded.raw_reactions.len(), 1);
        assert_eq!(
            ord::Reaction::decode(decoded.raw_reactions[0].bytes.as_slice())
                .unwrap()
                .reaction_id,
            "ord-fixture-1"
        );
        assert_eq!(
            decoded.raw_reactions[0].sha256,
            sha256(&decoded.raw_reactions[0].bytes)
        );
    }

    #[test]
    fn reference_only_and_malformed_datasets_fail_closed() {
        let references = ord::Dataset {
            dataset_id: "ord-reference-set".into(),
            reaction_ids: vec!["ord-external-reaction".into()],
            ..Default::default()
        }
        .encode_to_vec();
        assert!(matches!(
            decode_dataset(&references),
            Err(OrdCodecError::DatasetReferencesOnly)
        ));
        assert!(scan_raw_reactions(&[0x1a, 0x80]).is_err());
    }

    #[test]
    fn structural_classification_accepts_or_excludes_every_reaction() {
        use ord::compound_identifier::CompoundIdentifierType;
        use ord::reaction_identifier::ReactionIdentifierType;
        use ord::reaction_role::ReactionRoleType;

        let identifier = |kind, value: &str| ord::CompoundIdentifier {
            r#type: kind as i32,
            value: value.into(),
            ..Default::default()
        };
        let accepted = ord::Reaction {
            reaction_id: "ord-reaction-accepted".into(),
            identifiers: vec![ord::ReactionIdentifier {
                r#type: ReactionIdentifierType::ReactionSmiles as i32,
                value: "[CH3:1][OH:2]>>[CH3:1][Cl:2]".into(),
                is_mapped: Some(true),
                ..Default::default()
            }],
            inputs: std::collections::HashMap::from([(
                "reactant".into(),
                ord::ReactionInput {
                    components: vec![ord::Compound {
                        identifiers: vec![
                            identifier(CompoundIdentifierType::Smiles, "CO"),
                            identifier(CompoundIdentifierType::Cxsmiles, "[CH3][OH]"),
                        ],
                        reaction_role: ReactionRoleType::Reactant as i32,
                        ..Default::default()
                    }],
                    ..Default::default()
                },
            )]),
            outcomes: vec![ord::ReactionOutcome {
                products: vec![ord::ProductCompound {
                    identifiers: vec![identifier(CompoundIdentifierType::Smiles, "CCl")],
                    is_desired_product: None,
                    reaction_role: ReactionRoleType::Product as i32,
                    ..Default::default()
                }],
                ..Default::default()
            }],
            ..Default::default()
        };
        let excluded = ord::Reaction {
            reaction_id: "ord-reaction-excluded".into(),
            ..Default::default()
        };
        let missing_id = ord::Reaction::default();
        let dataset = ord::Dataset {
            dataset_id: "ord-dataset".into(),
            reactions: vec![accepted, excluded, missing_id],
            ..Default::default()
        };
        let decoded = decode_dataset(&dataset.encode_to_vec()).unwrap();
        let classified = classify_dataset_reactions(&decoded);
        assert_eq!(classified.len(), 3);
        assert_eq!(
            classified[0].as_ref().unwrap().raw_reaction_message_sha256,
            decoded.raw_reactions[0].sha256
        );
        assert_eq!(
            classified[1].as_ref().unwrap_err().reason,
            StructuralExclusionReason::MissingMappedReactionIdentifier
        );
        assert_eq!(
            classified[2].as_ref().unwrap_err().reason,
            StructuralExclusionReason::MissingReactionId
        );
    }
}
