"""
Unified launcher for LunaScope 3.0 using official NASA inputs.
Starts the FastAPI server which serves both the REST API and the built React frontend.
"""

import sys
import os
from pathlib import Path
import uvicorn

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"==================================================")
    print(f"  LunaScope 3.0 — Lunar South Pole Navigator")
    print(f"  Serving on: http://{host}:{port}")
    print(f"  API Docs:   http://{host}:{port}/docs")
    print(f"==================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
