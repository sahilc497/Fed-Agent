import os
import sys
import time
import subprocess
import requests

# Ensure backend path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def verify_server():
    print("Starting Uvicorn server in background...")
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "venv", "Scripts", "python.exe"))
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    cmd = [venv_python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    proc = subprocess.Popen(cmd, cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        # Wait for server to bind
        time.sleep(3)

        # 1. Test /health
        print("Checking GET http://127.0.0.1:8000/health...")
        r1 = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print(f"Liveness Status Code: {r1.status_code}, Body: {r1.json()}")

        # 2. Test /health/ready
        print("Checking GET http://127.0.0.1:8000/health/ready...")
        r2 = requests.get("http://127.0.0.1:8000/health/ready", timeout=5)
        print(f"Readiness Status Code: {r2.status_code}, Body: {r2.json()}")

        # 3. Test /docs
        print("Checking GET http://127.0.0.1:8000/docs...")
        r3 = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        print(f"OpenAPI Swagger Status Code: {r3.status_code}")

        print("\nAll live HTTP server checks passed successfully!")
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    verify_server()
