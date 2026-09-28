"""Owner connection and migration history are explicitly registry scoped."""

from alembic import context

context.configure(connection=context.config.attributes["connection"], version_table_schema="registry")
with context.begin_transaction():
    context.run_migrations()
