#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _local_score_adapter import main as local_score_main

if __name__ == "__main__":
    sys.argv.insert(1, "--benchmark-id")
    sys.argv.insert(2, "swe_bench_multilingual")
    raise SystemExit(local_score_main())
