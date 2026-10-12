#!/usr/bin/env python3
"""
Project Chronos — Backend Entrypoint
Allows launching the backend server directly from within the backend directory.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
for p in (str(PROJECT_ROOT), str(BACKEND_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n⚡ [Project Chronos] Starting Backend Server on http://{host}:{port} ...\n")
    uvicorn.run(app, host=host, port=port)
