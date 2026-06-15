#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _blocked_adapter import main as blocked_main

if __name__ == "__main__":
    benchmark_id = "agents_last_exam"
    if "--subset" in sys.argv:
        idx = sys.argv.index("--subset")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1] == "free_easy":
            benchmark_id = "agents_last_exam_free_easy_subset"
    sys.argv.insert(1, "--benchmark-id")
    sys.argv.insert(2, benchmark_id)
    raise SystemExit(blocked_main())
