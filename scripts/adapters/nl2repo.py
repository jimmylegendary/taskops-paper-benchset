#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _reported_qwen_adapter import main as reported_qwen_main

if __name__ == "__main__":
    sys.argv.insert(1, "--benchmark-id")
    sys.argv.insert(2, "nl2repo")
    raise SystemExit(reported_qwen_main())
