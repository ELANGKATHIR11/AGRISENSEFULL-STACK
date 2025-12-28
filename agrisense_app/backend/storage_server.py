# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnusedFunction=false
from typing import Any, Dict, cast


def create_storage_app() -> Any:
    # Import Flask lazily so the module doesn't require it at import time
    from .core import data_store as ds

    try:
        from flask import Flask, jsonify, request  # type: ignore[reportMissingImports]
    except Exception as e:
        # Propagate so caller can decide whether to mount or ignore
        raise e

    app: Any = Flask(__name__)

    @app.get("/ping")
    def ping() -> Any:
        return jsonify({"status": "ok"})

    @app.post("/store")
    def store() -> Any:
        # Accept arbitrary JSON to store as a reading; extend as needed
        payload = cast(Dict[str, Any], (request.get_json(force=True, silent=True) or {}))
        # Route into existing insert_reading for simplicity
        ds.insert_reading(payload)  # type: ignore[arg-type]
        return jsonify({"ok": True})

    @app.post("/reset")
    def reset() -> Any:
        ds.reset_database()
        return jsonify({"ok": True})

    return app
