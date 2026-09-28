"""Use only an explicitly supplied owner connection; history lives in artifact."""

from alembic import context

connection = context.config.attributes["connection"]
context.configure(connection=connection, version_table_schema="artifacts")
with context.begin_transaction():
    context.run_migrations()
