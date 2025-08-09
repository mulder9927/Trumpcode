#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "probe_dashV_sites.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

def slurp(p): 
    try: return p.read_text(encoding="utf-8", errors="ignore")
    except: return ""

targets = [ROOT/"Modules"/"main.c", ROOT/"Programs"/"python.c"]
patterns = [
    r'--version', r'[^A-Za-z]-V[^A-Za-z]',  # option parsing
    r'Py_GetVersion\s*\(',                  # version call
    r'Python\s*%s',                         # literal prefix
    r'PySys_WriteStdout\([^)]*Py_GetVersion', r'fprintf\([^)]*Py_GetVersion', r'printf\([^)]*Py_GetVersion',
]

lines = []
for t in targets:
    lines.append(f"[FILE] {t.relative_to(ROOT)} exists={t.exists()}")
    if not t.exists(): continue
    txt = slurp(t)
    arr = txt.splitlines()
    joined = "\n".join(arr)
    for pat in patterns:
        for m in re.finditer(pat, joined, flags=re.S):
            ln = joined.count("\n", 0, m.start()) + 1
            s = max(1, ln-10); e = min(len(arr), ln+10)
            ctx = "\n".join(f"{i:>6}: {arr[i-1]}" for i in range(s, e+1))
            lines.append(f"\n[hit] {t.name}:{ln} {pat}\n{ctx}\n")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT}")
