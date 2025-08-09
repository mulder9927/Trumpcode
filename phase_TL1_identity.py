#!/usr/bin/env python3
"""
TL1 Identity Split automation for TrumpLang (CPython 3.12 baseline)

What it does:
- PCbuild/python.vcxproj: TargetName -> trump (x64 Debug/Release)
- PCbuild/pythonw.vcxproj: TargetName -> trumpw (x64 Debug/Release)
- Python/getversion.c: "Python %s" -> "TrumpLang %s"
- Programs/python.c: set PyConfig.program_name = L"trump" after init
- Python/sysmodule.c: implementation name "cpython" -> "trumplang"
                     cache_tag "cpython-" -> "trumplang-"
- PC/getpathp.c: Prefer TRUMPHOME/TRUMPPATH, fallback to PYTHONHOME/PYTHONPATH

Usage:
  python tools/phase_TL1_identity.py --check   # dry run
  python tools/phase_TL1_identity.py --apply   # make changes (with .bak backups)
"""

import argparse
import re
import shutil
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class Change:
    def __init__(self, path: Path, description: str):
        self.path = path
        self.description = description
        self.changed = False
        self.note = ""

    def backup(self):
        bak = self.path.with_suffix(self.path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(self.path, bak)

def edit_vcxproj_target(path: Path, new_target: str):
    ch = Change(path, f"Set <TargetName> to {new_target} (x64 Debug/Release)")
    if not path.exists():
        ch.note = "file missing"
        return ch
    ET.register_namespace('', "http://schemas.microsoft.com/developer/msbuild/2003")
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'msb': root.tag.split('}')[0].strip('{')}

    def ensure_target(cfg, platform):
        xpath = (f".//msb:PropertyGroup[@Condition=\"'$(Configuration)|$(Platform)'=='{cfg}|{platform}'\"]",)
        groups = root.findall(xpath[0], ns)
        if not groups:
            # Create a new PropertyGroup with that Condition (rare, but safe)
            grp = ET.SubElement(root, f"{{{ns['msb']}}}PropertyGroup")
            grp.set('Condition', f"'$(Configuration)|$(Platform)'=='{cfg}|{platform}'")
            groups = [grp]
        for grp in groups:
            tn = grp.find("msb:TargetName", ns)
            if tn is None:
                tn = ET.SubElement(grp, f"{{{ns['msb']}}}TargetName")
                tn.text = new_target
                return True
            if tn.text != new_target:
                tn.text = new_target
                return True
        return False

    changed = False
    for cfg in ("Debug", "Release"):
        if ensure_target(cfg, "x64"):
            changed = True

    if changed:
        ch.changed = True
        if args.apply:
            tree.write(path, encoding="utf-8", xml_declaration=True)
    return ch

def replace_once_text(path: Path, pattern: str, repl: str, desc: str, flags=0):
    ch = Change(path, desc)
    if not path.exists():
        ch.note = "file missing"
        return ch
    text = path.read_text(encoding="utf-8", errors="ignore")
    new_text, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n > 0:
        ch.changed = True
        if args.apply:
            path.write_text(new_text, encoding="utf-8")
    else:
        ch.note = "already set or pattern not found"
    return ch

def insert_after_pattern(path: Path, anchor_pat: str, insertion: str, guard_pat: str, desc: str, flags=0):
    ch = Change(path, desc)
    if not path.exists():
        ch.note = "file missing"
        return ch
    text = path.read_text(encoding="utf-8", errors="ignore")
    if re.search(guard_pat, text, flags):
        ch.note = "guard pattern found (already inserted)"
        return ch
    m = re.search(anchor_pat, text, flags)
    if not m:
        ch.note = "anchor not found"
        return ch
    idx = m.end()
    new_text = text[:idx] + insertion + text[idx:]
    ch.changed = True
    if args.apply:
        path.write_text(new_text, encoding="utf-8")
    return ch

def multi_replace(path: Path, replacements, desc: str):
    """replacements: list[(pattern, repl, flags)], applies all; marks changed if any applied"""
    ch = Change(path, desc)
    if not path.exists():
        ch.note = "file missing"
        return ch
    text = path.read_text(encoding="utf-8", errors="ignore")
    changed = False
    for pat, repl, flags in replacements:
        new_text, n = re.subn(pat, repl, text, flags=flags)
        if n:
            text = new_text
            changed = True
    if changed:
        ch.changed = True
        if args.apply:
            path.write_text(text, encoding="utf-8")
    else:
        ch.note = "already set or patterns not found"
    return ch

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true", help="apply changes")
parser.add_argument("--check", action="store_true", help="dry-run only")
args = parser.parse_args()
if not (args.apply or args.check):
    print("Use --check for dry-run or --apply to modify files.")
    sys.exit(2)

changes = []

# 1) PCbuild targets
pyproj = ROOT / "PCbuild" / "python.vcxproj"
wproj  = ROOT / "PCbuild" / "pythonw.vcxproj"
for p in (pyproj, wproj):
    if p.exists() and args.apply:
        Change(p, "backup").backup()

changes.append(edit_vcxproj_target(pyproj, "trump"))
changes.append(edit_vcxproj_target(wproj,  "trumpw"))

# 2) Python/getversion.c: banner
gv = ROOT / "Python" / "getversion.c"
if gv.exists() and args.apply: Change(gv, "backup").backup()
changes.append(
    replace_once_text(
        gv,
        r'Python %s \(%s\)',
        r'TrumpLang %s (%s)',
        desc='Replace banner "Python %s (%s)" -> "TrumpLang %s (%s)"'
    )
)

# 3) Programs/python.c: program_name = L"trump" after PyConfig_InitPythonConfig
pc = ROOT / "Programs" / "python.c"
if pc.exists() and args.apply: Change(pc, "backup").backup()
changes.append(
    insert_after_pattern(
        pc,
        anchor_pat=r'PyConfig_InitPythonConfig\(&config\);\s*',
        insertion='\n    (void)PyConfig_SetString(&config, &config.program_name, L"trump");\n',
        guard_pat=r'program_name.*L"trump"',
        desc='Set default program_name to "trump"'
    )
)

# 4) Python/sysmodule.c: implementation name and cache tag
sm = ROOT / "Python" / "sysmodule.c"
if sm.exists() and args.apply: Change(sm, "backup").backup()
changes.append(
    multi_replace(
        sm,
        [
            (r'"cpython"', r'"trumplang"', 0),
            (r'cpython-',  r'trumplang-', 0),
        ],
        desc='Set sys.implementation name="trumplang" and cache_tag prefix "trumplang-"'
    )
)

# 5) PC/getpathp.c: TRUMPHOME/TRUMPPATH preferred, fallback to PYTHON*
gp = ROOT / "PC" / "getpathp.c"
if gp.exists() and args.apply: Change(gp, "backup").backup()
# Replace home line
changes.append(
    multi_replace(
        gp,
        [
            # Replace the PYTHONHOME fetch with TRUMPHOME + fallback block
            (r'const wchar_t \*home\s*=\s*_Py_GetEnv\(config,\s*L"PYTHONHOME"\s*\);\s*',
             'const wchar_t *home = _Py_GetEnv(config, L"TRUMPHOME");\n'
             '    if (home == NULL) home = _Py_GetEnv(config, L"PYTHONHOME");\n',
             0),
            # Replace the PYTHONPATH fetch with TRUMPPATH + fallback block
            (r'const wchar_t \*path\s*=\s*_Py_GetEnv\(config,\s*L"PYTHONPATH"\s*\);\s*',
             'const wchar_t *path = _Py_GetEnv(config, L"TRUMPPATH");\n'
             '    if (path == NULL) path = _Py_GetEnv(config, L"PYTHONPATH");\n',
             0)
        ],
        desc='Prefer TRUMPHOME/TRUMPPATH with PYTHON* fallback'
    )
)

# Report
made = [c for c in changes if c.changed]
skipped = [c for c in changes if (not c.changed)]
print("TL1 identity script report:\n")
for c in changes:
    status = "CHANGED" if c.changed else "OK/NOOP"
    extra = f" [{c.note}]" if c.note else ""
    print(f"- {c.path.relative_to(ROOT)}: {status} – {c.description}{extra}")

if args.check and made:
    print("\nDry run: changes would be applied. Re-run with --apply to modify files.")
elif args.apply:
    print("\nApplied. Backups saved alongside originals as .bak.")
