"""Explicit configured local server; no migration or automatic model dispatch."""

import argparse
import os

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from ..supervision_intake import SupervisionIntake
from .app import create_app
from .credentials import Credentials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8007)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    try:
        credentials = Credentials.from_json(os.environ['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'])
        engine = create_engine(os.environ['AMPHORA_PLANNING_DATABASE_URL'],
                               connect_args={'options': '-c statement_timeout=5000'})
    except (KeyError, TypeError, ValueError, SQLAlchemyError):
        raise SystemExit('Valid Planning database and supervisor credentials configuration required') from None
    try:
        uvicorn.run(create_app(SupervisionIntake(engine), credentials), host=args.host, port=args.port)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
