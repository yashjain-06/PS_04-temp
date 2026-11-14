"""Start the web UI:  python scripts/run_server.py   (owner: M4)

Local:   http://127.0.0.1:5000
On a hosting platform the PORT environment variable is honoured and the server listens on all interfaces.
Set HOST=0.0.0.0 to let other devices on your Wi-Fi open it.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import load_config  # noqa: E402
from web.app import create_app  # noqa: E402

if __name__ == "__main__":
    cfg = load_config()["web"]
    host = os.environ.get("HOST") or ("0.0.0.0" if os.environ.get("PORT") else cfg["host"])
    port = int(os.environ.get("PORT") or cfg["port"])
    print(f"Open http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}")
    create_app().run(host=host, port=port, threaded=True, debug=False)
