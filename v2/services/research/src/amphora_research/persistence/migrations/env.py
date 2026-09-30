"""Owner connection and migration history are explicitly research scoped."""

from alembic import context

context.configure(connection=context.config.attributes["connection"], version_table_schema="research")
with context.begin_transaction():
    context.run_migrations()
