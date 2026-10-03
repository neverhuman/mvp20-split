"""Independently rebuild Research for immutable-history cutover acceptance."""
import argparse
from pathlib import Path

from install_owner_peer import install

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    install(parser.parse_args().output, "amphora-research",
            ("amphora_data_artifacts", "amphora_campaign_runtime", "amphora_knowledge"))
