"""Install an isolated Runtime receipt peer; integration acceptance is separate."""
import argparse
from pathlib import Path

from install_owner_peer import install


def verify(output):
    return install(output, "amphora-campaign-runtime",
                   ("amphora_data_artifacts", "amphora_research", "amphora_knowledge"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output)
