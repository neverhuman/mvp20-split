"""Migration history belongs only to the Planning schema."""

from alembic import context

context.configure(connection=context.config.attributes["connection"], version_table_schema="planning")
with context.begin_transaction():
    context.run_migrations()
