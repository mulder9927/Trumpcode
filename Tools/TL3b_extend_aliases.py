#!/usr/bin/env python3
#!/usr/bin/env python3
from pathlib import Path
import re
import shutil


root = Path(__file__).resolve().parents[1]
p = root / "Lib" / "trumplang_syntax.py"
text = p.read_text(encoding="utf-8")

# 1) Add more aliases (merge-friendly: append to existing ALIASES dict)
more = r"""
    # --- TL3b additions ---
    ("LOOK","FOLKS"): "print",
    ("YOU","WONT","BELIEVE","THIS"): "print",
    ("SO","TRUE","SO","TRUE"): "return",
    ("TOTAL","SUCCESS"): "return",
    ("THIS","I","CAN","TELL","YOU"): "if",
    ("PEOPLE","ARE","SAYING"): "else",
    ("KEEP","WINNING"): "continue",
    ("MAKE","IT","STOP"): "break",
    ("IN",): "in",
"""
text = re.sub(
    r"(ALIASES\s*=\s*{\s*)([^}]*)(\})",
    lambda m: m.group(1) + m.group(2).rstrip() + more + "\n}", text, count=1
)

# 2) Also forbid `continue` in strict mode (like we already do for break)
text = text.replace(
    "        if strict and t.type == tokenize.NAME and t.string == \"break\":\n"
    "            raise TrumpSyntaxError(\"Use 'CONTRADICT THE NARRATIVE' instead of 'break' in TrumpLang strict mode\")\n",
    "        if strict and t.type == tokenize.NAME and t.string == \"break\":\n"
    "            raise TrumpSyntaxError(\"Use 'CONTRADICT THE NARRATIVE' instead of 'break' in TrumpLang strict mode\")\n"
    "        if strict and t.type == tokenize.NAME and t.string == \"continue\":\n"
    "            raise TrumpSyntaxError(\"Use 'MOVE ALONG' instead of 'continue' in TrumpLang strict mode\")\n"
)

bak = p.with_suffix(p.suffix + ".bak_TL3b")
if not bak.exists():
    shutil.copy2(p, bak)
p.write_text(text, encoding="utf-8")
print("TL3b: extended aliases + strict continue rule applied.")
