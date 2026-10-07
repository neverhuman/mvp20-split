"""Serving-role boundary for the configured supervisor host; no DDL."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def serving_engine(database_url):
    url = make_url(database_url)
    if url.drivername != 'postgresql+psycopg' or url.username != 'planning_service':
        raise ValueError('planning_service_role_required')
    engine = create_engine(url, pool_pre_ping=True,
                           connect_args={'connect_timeout': 5, 'options': '-c statement_timeout=5000'})
    try:
        with engine.connect() as connection:
            if connection.execute(text('SELECT current_user')).scalar_one() != 'planning_service':
                raise ValueError('planning_service_role_required')
    except Exception:
        engine.dispose()
        raise
    return engine
