#!/usr/bin/env python3
"""
Find all CPython version-print call sites (where 'Python %s' or Py_GetVersion()
is printed) with context, so we patch the right one for --version.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "probe_version_sites.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def grep_ctx(path, pats, ctx=8):
    txt = read(path)
    if not txt:
        return []
    lines = txt.splitlines()
    joined = "\n".join(lines)
    hits = []
    for pat in pats:
        for m in re.finditer(pat, joined, re.S):
            ln = joined.count("\n", 0, m.start())
            s = max(0, ln-ctx); e = min(len(lines), ln+ctx+1)
            block = "\n".join(f"{i+1:>6}: {lines[i]}" for i in range(s,e))
            hits.append((pat, ln+1, block))
    return hits

files = [
    "Modules/main.c",
    "Programs/python.c",
    "Modules/getversion.c",
    "Python/getversion.c",
]

patterns = [
    r'Python\s*%s',                       # "Python %s" literals
    r'PySys_WriteStdout\([^;]*Py_GetVersion',  # PySys_WriteStdout(... Py_GetVersion())
    r'printf\([^;]*Py_GetVersion',        # printf(... Py_GetVersion())
    r'fprintf\([^;]*Py_GetVersion',       # fprintf(... Py_GetVersion())
    r'--version',                         # any explicit long option handling
    r'[^A-Za-z](-V)[^A-Za-z]',            # -V handling (non-word bounded)
]

lines = []
for rel in files:
    p = ROOT / rel
    lines.append(f"[FILE] {rel} exists={p.exists()}")
    if not p.exists():
        continue
    for pat, ln, block in grep_ctx(p, patterns, ctx=10):
        lines.append(f"  [hit] {pat} @ line {ln}\n{block}\n")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT}")
