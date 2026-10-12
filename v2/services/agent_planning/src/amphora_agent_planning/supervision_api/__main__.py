"""Explicit configured local server; no migration or automatic model dispatch."""

import argparse
import os

import uvicorn
from sqlalchemy.exc import SQLAlchemyError

from ..supervision_intake import SupervisionIntake
from .app import create_app
from .credentials import Credentials
from .hosting import serving_engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8007)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    try:
        credentials = Credentials.from_json(os.environ['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'])
        engine = serving_engine(os.environ['AMPHORA_PLANNING_DATABASE_URL'])
    except (KeyError, TypeError, ValueError, SQLAlchemyError):
        raise SystemExit('Valid Planning database and supervisor credentials configuration required') from None
    try:
        try:
            topology=None
            path=os.environ.get('AMPHORA_PLANNING_TOPOLOGY_CONFIG')
            if path is not None:
                from ..topology.hosting import ConfiguredTopology
                topology=ConfiguredTopology.load(path).operations(engine)
            curations = None
            curation_config = os.environ.get('AMPHORA_PLANNING_CURATION_POLICIES')
            if curation_config is not None:
                from ..curation_intake.configuration import policy_ids
                from ..curation_intake.journal import CurationJournal
                curations = CurationJournal(engine, policy_ids(curation_config))
            app=create_app(SupervisionIntake(engine), credentials,topology=topology,curations=curations)
        except (OSError,KeyError,TypeError,ValueError,RecursionError):
            raise SystemExit('Valid Planning topology/curation configuration required') from None
        uvicorn.run(app, host=args.host, port=args.port)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
