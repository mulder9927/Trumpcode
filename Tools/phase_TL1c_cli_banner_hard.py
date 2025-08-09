#!/usr/bin/env python3
# Make --version print "TrumpLang ..." across 3.12 variants.
from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parents[1]
sites = [ROOT/"Modules"/"main.c", ROOT/"Programs"/"python.c"]

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

changed = []
for p in sites:
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8", errors="ignore")
    o = s
    # printf("Python %s\n", Py_GetVersion());
    s = re.sub(r'printf\(\s*"Python\s*%s\\n"\s*,\s*Py_GetVersion\(\)\s*\)',
               r'printf("TrumpLang %s\n", Py_GetVersion())', s)
    # printf(L"Python %s\n", Py_GetVersion());
    s = re.sub(r'printf\(\s*L"Python\s*%s\\n"\s*,\s*Py_GetVersion\(\)\s*\)',
               r'printf(L"TrumpLang %s\n", Py_GetVersion())', s)
    # PySys_WriteStdout("Python %s\n", Py_GetVersion());
    s = re.sub(r'PySys_WriteStdout\(\s*"Python\s*%s\\n"\s*,\s*Py_GetVersion\(\)\s*\)',
               r'PySys_WriteStdout("TrumpLang %s\n", Py_GetVersion())', s)
    # PySys_WriteStdout(L"Python %s\n", ...)
    s = re.sub(r'PySys_WriteStdout\(\s*L"Python\s*%s\\n"\s*,\s*Py_GetVersion\(\)\s*\)',
               r'PySys_WriteStdout(L"TrumpLang %s\n", Py_GetVersion())', s)
    if s != o:
        backup(p); p.write_text(s, encoding="utf-8")
        changed.append(p.relative_to(ROOT).as_posix())

if changed:
    print("CLI banner patched in:", ", ".join(changed))
else:
    print("No banner call-sites matched (maybe already TrumpLang).")
