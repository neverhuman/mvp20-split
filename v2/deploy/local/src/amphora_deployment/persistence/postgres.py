"""Bootstrap only deployment-owned schemas/identities; service migrations stay owner-owned."""

from ..installation import OWNERS
from ..profile import require


DATABASE = "amphora_local"


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def sql(docker, container, statement):
    # SQL may contain newly generated passwords. Never log input or raw diagnostics.
    return docker.run("exec", "-i", container, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres",
                      "-d", DATABASE, "-At", payload=statement)


def bootstrap(docker, container, identity, bundle):
    marker = sql(docker, container, "SELECT to_regclass('deployment.bootstrap') IS NOT NULL;")
    if marker == "t":
        require(sql(docker, container, "SELECT deployment_id FROM deployment.bootstrap;") == identity, "deployment_database_owner_mismatch")
        return
    roles = [role for recipe in OWNERS.values() for role in (recipe.migration_role, recipe.service_role)]
    lines = ["BEGIN;", "CREATE SCHEMA deployment AUTHORIZATION postgres;",
             "CREATE TABLE deployment.bootstrap (deployment_id text PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT clock_timestamp());",
             "REVOKE ALL ON SCHEMA deployment FROM PUBLIC;", "REVOKE ALL ON DATABASE amphora_local FROM PUBLIC;",
             "REVOKE CREATE ON SCHEMA public FROM PUBLIC;"]
    for role in roles:
        password = bundle.environment(["PG_" + role.upper() + "_PASSWORD"])["PG_" + role.upper() + "_PASSWORD"]
        lines.append("CREATE ROLE " + role + " LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD " + literal(password) + ";")
    lines.append("GRANT CONNECT ON DATABASE amphora_local TO " + ",".join(roles) + ";")
    for recipe in OWNERS.values():
        lines += ["CREATE SCHEMA " + recipe.schema + " AUTHORIZATION " + recipe.migration_role + ";",
                  "GRANT USAGE ON SCHEMA " + recipe.schema + " TO " + recipe.service_role + ";"]
    lines += ["INSERT INTO deployment.bootstrap(deployment_id) VALUES (" + literal(identity) + ");", "COMMIT;"]
    sql(docker, container, "\n".join(lines))
    require(sql(docker, container, "SELECT deployment_id FROM deployment.bootstrap;") == identity, "deployment_bootstrap_receipt")
