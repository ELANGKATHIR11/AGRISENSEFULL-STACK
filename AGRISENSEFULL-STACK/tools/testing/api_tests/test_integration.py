#!/usr/bin/env python3
"""Integration test for AgriSense backend-frontend pipeline.

This file is an integration test and will be marked with the pytest
`integration` marker. It is intentionally excluded from fast unit test runs
and should be executed explicitly (e.g. pytest -m integration).
"""

import json
import time
import subprocess
from contextlib import contextmanager

import pytest
import requests


@pytest.mark.integration
@contextmanager
def backend_server():
    """Start backend server in background for integration testing.

    Note: this uses the project's virtualenv python in `.venv` relative to the
    project root. CI integration stage should ensure the environment is prepared
    and the working directory is set appropriately.
    """
    proc = subprocess.Popen([
        '.venv/Scripts/python.exe', '-m', 'uvicorn',
        'agrisense_app.backend.main:app', '--port', '8004'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start (simple backoff)
    time.sleep(8)

    try:
        yield proc
    finally:
        proc.terminate()
        proc.wait()


@pytest.mark.integration
def test_backend_frontend_integration():
    """A simple integration scenario that exercises key endpoints.

    This test is resource- and time-heavy and should only run when explicitly
    requested (pytest -m integration).
    """
    print('🚀 Starting AgriSense backend for integration test...')

    with backend_server():
        base_url = 'http://127.0.0.1:8004'

        # Health
        r = requests.get(f'{base_url}/health', timeout=15)
        assert r.status_code == 200

        # Plants list (may be empty but should return JSON)
        r = requests.get(f'{base_url}/plants', timeout=15)
        assert r.status_code in (200, 204)

        # Recommendation endpoint smoke
        payload = {
            'moisture': 45.0,
            'temp': 25.0,
            'ph': 6.5,
            'ec': 1.2,
            'plant': 'wheat'
        }
        r = requests.post(f'{base_url}/recommend', json=payload, timeout=15)
        assert r.status_code == 200
        reco = r.json()
        assert 'water_liters' in reco

        # UI serving (optional)
        r = requests.get(f'{base_url}/ui', timeout=15)
        assert r.status_code in (200, 404)

    print('✅ Integration test completed!')


if __name__ == '__main__':
    # Allow manual execution for debugging
    test_backend_frontend_integration()