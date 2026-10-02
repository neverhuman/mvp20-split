"""Migration history belongs only to the Knowledge schema."""

from alembic import context

context.configure(connection=context.config.attributes["connection"], version_table_schema="knowledge")
with context.begin_transaction():
    context.run_migrations()
