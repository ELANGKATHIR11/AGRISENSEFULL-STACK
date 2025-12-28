import pytest

try:
    # Import FastAPI TestClient lazily so environments without fastapi/httpx don't fail
    from fastapi.testclient import TestClient
    from agrisense_app.backend.main import app as _app
except Exception:
    TestClient = None
    _app = None


@pytest.fixture(scope='session')
def test_client():
    """Provide a TestClient for running API tests in-process when available.

    If FastAPI or TestClient isn't available in the environment, this fixture
    will skip tests that require it.
    """
    if TestClient is None or _app is None:
        pytest.skip("FastAPI TestClient not available in this environment")

    client = TestClient(_app)
    yield client


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration")
