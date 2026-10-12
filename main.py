#!/usr/bin/env python3
"""
Project Chronos — Root Application Entrypoint
Allows instant server launch via `python main.py` or `python3 main.py`
directly after cloning the repository.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from run import main

if __name__ == "__main__":
    main()
