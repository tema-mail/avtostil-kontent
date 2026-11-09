#!/usr/bin/env python3
"""Генерирует обложки по plan.csv через gen/cover.sh, по 3 параллельно."""
import csv, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R = Path(__file__).resolve().parent.parent
rows = [r for r in csv.DictReader(open(R / "docs/plan.csv"), delimiter=";") if r["oblozhka"] and (len(sys.argv) < 2 or r["id"] in sys.argv[1:])]
def one(r):
    out = subprocess.run([str(R / "gen/cover.sh"), r["id"], r["oblozhka"]], capture_output=True, text=True).stdout.strip()
    print(out, flush=True); return out
with ThreadPoolExecutor(1) as ex: list(ex.map(one, rows))
