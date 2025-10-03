import os
from pathlib import Path

def pytest_ignore_collect(path, config):
    # Ignore hardware or long-running integration scripts that are not unit tests
    p = Path(path)
    # Ignore Arduino firmware tests and scripts that make network calls at import time
    if 'AGRISENSE_IoT' in str(p):
        return True
    if p.match('scripts/test_weed_quick.py'):
        return True
    if p.match('tools/testing/api_tests/test_integration.py'):
        return True
    # Ignore any test files that are in directories named 'arduino' or 'edge'
    if any(part.lower().startswith('arduino') for part in p.parts):
        return True
    return False
