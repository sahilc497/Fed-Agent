import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_databases():
    conn = psycopg2.connect(dbname="postgres", user="postgres", host="127.0.0.1", port=5432)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    for db_name in ["federated_mesh_dev", "federated_mesh_test"]:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database: {db_name}")
        else:
            print(f"Database already exists: {db_name}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    init_databases()
