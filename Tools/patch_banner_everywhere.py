from pathlib import Path
import re, shutil

p = Path("Modules/main.c")
s0 = p.read_text(encoding="utf-8", errors="ignore")

# backup once
bak = p.with_suffix(p.suffix + ".bak_all")
if not bak.exists():
    shutil.copy2(p, bak)

s = s0
# fprintf/printf narrow & wide
s = re.sub(r'(")Python(\s*%s)', r'\1TrumpLang\2', s)

# PySys_WriteStdout variants (narrow & wide)
s = re.sub(r'(PySys_WriteStdout\(\s*L?)"Python(\s*%s)', r'\1"TrumpLang\2', s)

if s != s0:
    p.write_text(s, encoding="utf-8")
    print("OK: replaced 'Python %s' -> 'TrumpLang %s' in Modules/main.c")
else:
    print("No changes (patterns not found or already patched)")
