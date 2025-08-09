#!/usr/bin/env python3
# Deep probe for TL1 anchors (contexts for exact patching)
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "probe_TL1_phase2.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

def read(p): 
    try: return p.read_text(encoding="utf-8", errors="ignore")
    except: return ""

def grep_ctx(path, pattern, flags=0, ctx=8):
    txt = read(path)
    if not txt: return []
    lines = txt.splitlines()
    out = []
    for m in re.finditer(pattern, txt, flags):
        ln = txt.count("\n", 0, m.start())
        s = max(0, ln-ctx); e = min(len(lines), ln+ctx+1)
        out.append((ln+1, "\n".join(f"{i+1:>6}: {lines[i]}" for i in range(s,e))))
    return out

def search_tree(globs, pattern, flags=0, ctx=3):
    hits = []
    for g in globs:
        for p in ROOT.glob(g):
            if p.is_file():
                for ln, block in grep_ctx(p, pattern, flags, ctx):
                    hits.append((p, ln, block))
    return hits

lines = []

# 1) Py_GetVersion body + any "Python " string literals anywhere (so we can rewrite banner)
getversion = ROOT / "Python" / "getversion.c"
lines.append(f"[getversion.c exists={getversion.exists()}]")
for ln, block in grep_ctx(getversion, r'\bPy_GetVersion\s*\(', re.S, ctx=20):
    lines.append(f"Py_GetVersion @ line {ln}\n{block}\n")
any_py_literals = search_tree(["Python/**/*.c", "Programs/**/*.c", "Include/**/*.h", "Modules/**/*.c"],
                              r'"Python[ ^%]"', 0, 1)
lines.append("[String literals matching \"Python \"]")
for p, ln, block in any_py_literals[:50]:
    lines.append(f"{p.relative_to(ROOT)}:{ln}\n{block}\n")
if len(any_py_literals) > 50:
    lines.append(f"... ({len(any_py_literals)} total, truncated)\n")

# 2) Program config anchors across Programs/
prog_hits = []
for pat in [r'PyConfig_Init\w*Config\s*\(\s*&config',
            r'Py_InitializeFromConfig\s*\(\s*&config',
            r'program_name']:
    h = search_tree(["Programs/**/*.c"], pat, 0, 8)
    lines.append(f"[Programs/* search: {pat}] hits={len(h)}")
    for p, ln, block in h:
        lines.append(f"{p.relative_to(ROOT)}:{ln}\n{block}\n")
    prog_hits.extend(h)

# 3) Env reads: PYTHONHOME/PYTHONPATH/TRUMPHOME/TRUMPPATH anywhere
for pat in [r'PYTHONHOME', r'PYTHONPATH', r'TRUMPHOME', r'TRUMPPATH', r'_Py_GetEnv\s*\(']:
    h = search_tree(["Python/**/*.c", "PC/**/*.c", "Modules/**/*.c"], pat, 0, 8)
    lines.append(f"[Env search: {pat}] hits={len(h)}")
    for p, ln, block in h:
        lines.append(f"{p.relative_to(ROOT)}:{ln}\n{block}\n")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT}")
