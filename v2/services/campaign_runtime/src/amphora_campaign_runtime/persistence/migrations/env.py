"""Use only an explicitly supplied owner connection; history lives in runtime."""

from alembic import context

connection = context.config.attributes["connection"]
context.configure(connection=connection, version_table_schema="runtime")
with context.begin_transaction():
    context.run_migrations()
