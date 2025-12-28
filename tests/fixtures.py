import subprocess
import time
import requests
import os
import signal
import pytest
from pathlib import Path


@pytest.fixture(scope='session')
def live_server(tmp_path_factory):
    """Start uvicorn in a subprocess for integration tests and stop it at teardown.

    Uses the .venv/Scripts/python.exe in the project root. If you need to run
    with a different python, set the VENV_PYTHON env var.
    """
    project_root = Path(__file__).resolve().parents[1]
    python = os.environ.get('VENV_PYTHON') or str(project_root / '.venv' / 'Scripts' / 'python.exe')

    proc = subprocess.Popen([
        python, '-m', 'uvicorn', 'agrisense_app.backend.main:app', '--port', '8004'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for /health
    base = 'http://127.0.0.1:8004'
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            r = requests.get(f'{base}/health', timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.3)

    yield base

    # Teardown
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
