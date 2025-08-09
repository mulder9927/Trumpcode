from pathlib import Path
import shutil

p = Path("Modules/main.c")
s = p.read_text(encoding="utf-8")

old = 'fprintf(stderr, "Python %s on %s\\n", Py_GetVersion(), Py_GetPlatform());'
new = 'fprintf(stderr, "TrumpLang %s on %s\\n", Py_GetVersion(), Py_GetPlatform());'

if old in s:
    bak = p.with_suffix(p.suffix + ".bak2")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_text(s.replace(old, new), encoding="utf-8")
    print("OK: banner patched")
else:
    print("Note: exact banner line not found; nothing changed")
