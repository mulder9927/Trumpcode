from pathlib import Path
import re, shutil

root = Path(__file__).resolve().parents[1]
p = root / "Lib" / "importlib" / "_bootstrap_external.py"
s = p.read_text(encoding="utf-8", errors="ignore")

bak = p.with_suffix(p.suffix + ".bak_TL1c")
if not bak.exists():
    shutil.copy2(p, bak)

changed = False

def inject_suffix_list(tag, text):
    # match e.g. SOURCE_SUFFIXES = ['.py', ...]
    pat = rf"^{tag}\s*=\s*\[([^\]]*)\]"
    m = re.search(pat, text, flags=re.M)
    if not m:
        return text, False
    inside = m.group(1)
    if ".trump" in inside:
        return text, False
    # place right after '.py'
    inside_new = inside.replace("'.py'", "'.py', '.trump'")
    if inside_new == inside:
        # fallback: append at end
        inside_new = (inside.strip() + (", " if inside.strip() else "") + "'.trump'")
    new = re.sub(pat, f"{tag} = [{inside_new}]", text, flags=re.M)
    return new, True

for tag in ("SOURCE_SUFFIXES", "ALL_SOURCE_SUFFIXES"):
    s, did = inject_suffix_list(tag, s)
    changed |= did

if changed:
    p.write_text(s, encoding="utf-8")
    print("OK: added '.trump' to importlib source suffixes")
else:
    print("No change (already had '.trump'?)")
