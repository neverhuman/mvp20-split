"""Explicit owner migration entrypoint; service startup never applies DDL."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine


def upgrade(url):
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
    finally:
        engine.dispose()


if __name__ == "__main__":
    upgrade(os.environ["AMPHORA_RESEARCH_MIGRATION_URL"])
