import yaml, os

def load_config(path: str = "config.yaml"):
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "..", "config.example.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)
