import requests
class BackendClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base = base_url.rstrip("/")
    def ingest(self, reading):
        r = requests.post(f"{self.base}/ingest", json=reading)
        return r.json()
    def recommend(self, reading):
        r = requests.post(f"{self.base}/recommend", json=reading)
        return r.json()
class MqttCaptureTrigger:
    def __init__(self, *a, **k):
        pass
