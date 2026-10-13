import subprocess
import os
import psycopg2

def verify_alembic_migration():
    test_db_url = "postgresql+psycopg2://postgres@127.0.0.1:5432/federated_mesh_test"
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    venv_alembic = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "Scripts", "alembic.exe"))

    print("Step 1: Dropping any existing tables in federated_mesh_test...")
    conn = psycopg2.connect(dbname="federated_mesh_test", user="postgres", host="127.0.0.1", port=5432)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    cur.close()
    conn.close()

    print("Step 2: Running 'alembic upgrade head' on federated_mesh_test...")
    env = os.environ.copy()
    env["SYNC_DATABASE_URL"] = test_db_url
    res_up = subprocess.run([venv_alembic, "-x", f"db_url={test_db_url}", "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True, env=env)
    print("Alembic upgrade stdout:\n", res_up.stdout)
    if res_up.returncode != 0:
        print("Alembic upgrade stderr:\n", res_up.stderr)
        raise RuntimeError("Alembic upgrade failed!")

    conn = psycopg2.connect(dbname="federated_mesh_test", user="postgres", host="127.0.0.1", port=5432)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables created by Alembic upgrade:", len(tables), tables)
    assert "users" in tables
    assert "departments" in tables
    assert "sales_opportunities" in tables
    assert "audit_logs" in tables
    assert "alembic_version" in tables

    print("Step 3: Testing 'alembic downgrade base' on federated_mesh_test...")
    res_down = subprocess.run([venv_alembic, "-x", f"db_url={test_db_url}", "downgrade", "base"], cwd=backend_dir, capture_output=True, text=True, env=env)
    print("Alembic downgrade stdout:\n", res_down.stdout)
    if res_down.returncode != 0:
        print("Alembic downgrade stderr:\n", res_down.stderr)
        raise RuntimeError("Alembic downgrade failed!")

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    remaining_tables = [r[0] for r in cur.fetchall()]
    print("Remaining tables after downgrade base:", remaining_tables)
    assert "users" not in remaining_tables
    assert "departments" not in remaining_tables
    cur.close()
    conn.close()

    print("Step 4: Running 'alembic upgrade head' again to ensure full idempotency...")
    res_up2 = subprocess.run([venv_alembic, "-x", f"db_url={test_db_url}", "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True, env=env)
    assert res_up2.returncode == 0
    print("Alembic migration verification succeeded completely without any stamp bypass!")

if __name__ == "__main__":
    verify_alembic_migration()
