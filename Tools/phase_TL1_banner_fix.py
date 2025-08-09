#!/usr/bin/env python3
from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "Modules" / "main.c"

def backup(x):
    b = x.with_suffix(x.suffix + ".bak")
    if not b.exists():
        shutil.copy2(x, b)

if not p.exists():
    print("Modules/main.c missing")
    raise SystemExit(1)

s0 = p.read_text(encoding="utf-8", errors="ignore")
s = s0
# fprintf(stderr, "Python %s on %s\n", Py_GetVersion(), Py_GetPlatform());
s = re.sub(r'fprintf\s*\(\s*stderr\s*,\s*"Python\s*%s\s*on\s*%s\\n"\s*,',
           'fprintf(stderr, "TrumpLang %s on %s\\n",', s)
# printf("Python %s\n", Py_GetVersion());
s = re.sub(r'printf\s*\(\s*"Python\s*%s\\n"\s*,\s*Py_GetVersion\(\)\s*\)',
           'printf("TrumpLang %s\\n", Py_GetVersion())', s)

if s != s0:
    backup(p)
    p.write_text(s, encoding="utf-8")
    print("Modules/main.c: CHANGED (CLI banner -> TrumpLang)")
else:
    print("Modules/main.c: OK/NOOP (no matching banner literals)")
