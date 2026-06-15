#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _blocked_adapter import main as blocked_main

if __name__ == "__main__":
    sys.argv.insert(1, "--benchmark-id")
    sys.argv.insert(2, "skillsbench")
    raise SystemExit(blocked_main())
