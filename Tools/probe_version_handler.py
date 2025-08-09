#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
main_c = ROOT/"Modules"/"main.c"
txt = main_c.read_text(encoding="utf-8", errors="ignore")
lines = txt.splitlines()

def ctx(i, k=10):
    s = max(0, i-k); e = min(len(lines), i+k+1)
    return "\n".join(f"{n+1:>6}: {lines[n]}" for n in range(s,e))

hits = []
# Look for the config flag used for -V (print_version) and the print call
for pat in [
    r'\bprint_version\b',
    r'\bprint_build_info\b',
    r'\b--version\b',
    r'[^A-Za-z]-V[^A-Za-z]',
    r'PySys_WriteStdout\([^)]*Py_GetVersion',
    r'fprintf\([^)]*"Python\s*%s\\n"[^)]*Py_GetVersion',
    r'printf\([^)]*"Python\s*%s\\n"[^)]*Py_GetVersion',
    r'"Python\s*%s\\n"\s*,\s*Py_GetVersion',
    r'"Python\s*%s\\r?\\n?"',
]:
    for m in re.finditer(pat, txt, flags=re.S):
        i = txt.count("\n", 0, m.start())
        hits.append((pat, i))

# De-dup by line
seen = set()
out = []
for pat, i in sorted(hits, key=lambda x: x[1]):
    if i in seen: 
        continue
    seen.add(i)
    out.append(f"[hit] {pat} @ line {i+1}\n{ctx(i)}\n")

out_path = ROOT/"build"/"probe_version_handler.txt"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text("\n".join(out), encoding="utf-8")
print(f"Wrote {out_path}")
