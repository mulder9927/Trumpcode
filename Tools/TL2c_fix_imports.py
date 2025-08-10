#!/usr/bin/env python3
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
p = root / "Lib" / "trumplang_bootstrap.py"

text = p.read_text(encoding="utf-8", errors="ignore")
bak = p.with_suffix(p.suffix + ".bak_importfix")
if not bak.exists():
    shutil.copy2(p, bak)

fixed = text
fixed = fixed.replace("from .trumplang_rhetoric import pick_rants, PRESS as PRESS_MONOLOGUES",
                      "import trumplang_rhetoric as _rhet")
fixed = fixed.replace("pick_rants(", "_rhet.pick_rants(").replace("PRESS_MONOLOGUES", "_rhet.PRESS")

p.write_text(fixed, encoding="utf-8")
print("Fixed imports in Lib/trumplang_bootstrap.py")
