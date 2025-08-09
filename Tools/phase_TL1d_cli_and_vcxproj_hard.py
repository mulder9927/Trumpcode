#!/usr/bin/env python3
from pathlib import Path
import re, shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CHANGES = []

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

# ---------- CLI banner patch ----------
def patch_cli_banner():
    for rel in ("Modules/main.c", "Programs/python.c"):
        p = ROOT / rel
        if not p.exists():
            continue
        s0 = p.read_text(encoding="utf-8", errors="ignore")
        s = s0

        # Any call that prints Py_GetVersion with a literal starting with "Python "
        # printf("Python %s\n", Py_GetVersion());
        s = re.sub(r'printf\(\s*"Python(\s*%s\\n)("\s*,\s*Py_GetVersion\(\)\s*\))',
                   r'printf("TrumpLang\1\2', s)
        # wprintf(L"Python %s\n", ...)
        s = re.sub(r'w?printf\(\s*L"Python(\s*%s\\n)("\s*,\s*Py_GetVersion\(\)\s*\))',
                   r'printf(L"TrumpLang\1\2', s)
        # PySys_WriteStdout("Python %s\n", Py_GetVersion());
        s = re.sub(r'PySys_WriteStdout\(\s*"Python(\s*%s\\n)("\s*,\s*Py_GetVersion\(\)\s*\))',
                   r'PySys_WriteStdout("TrumpLang\1\2', s)
        # PySys_WriteStdout(L"Python %s\n", ...)
        s = re.sub(r'PySys_WriteStdout\(\s*L"Python(\s*%s\\n)("\s*,\s*Py_GetVersion\(\)\s*\))',
                   r'PySys_WriteStdout(L"TrumpLang\1\2', s)

        if s != s0:
            backup(p); p.write_text(s, encoding="utf-8")
            CHANGES.append(f"{rel}: CHANGED (CLI --version banner)")
        else:
            CHANGES.append(f"{rel}: OK/NOOP (no banner site matched)")

# ---------- vcxproj alignment ----------
NS = {"msb": "http://schemas.microsoft.com/developer/msbuild/2003"}
def set_targetname_everywhere(tree, want):
    root = tree.getroot()
    changed = False
    # All conditioned PropertyGroups
    for grp in root.findall(".//msb:PropertyGroup", NS):
        cond = grp.get("Condition")
        if not cond:
            continue
        tn = grp.find("msb:TargetName", NS)
        if tn is None:
            tn = ET.SubElement(grp, f"{{{NS['msb']}}}TargetName")
            tn.text = want
            changed = True
        elif tn.text != want:
            tn.text = want
            changed = True
    return changed

def fix_outputfile(tree, exe):
    root = tree.getroot()
    changed = False
    for link in root.findall(".//msb:ItemDefinitionGroup/msb:Link", NS):
        of = link.find("msb:OutputFile", NS)
        if of is None:
            # create one so TargetPath matches linker output
            of = ET.SubElement(link, f"{{{NS['msb']}}}OutputFile")
        if (of.text or "").strip().lower() != f"$(outdir){exe}":
            of.text = f"$(OutDir){exe}"
            changed = True
    return changed

def fix_postbuild_newlines(tree):
    root = tree.getroot()
    changed = False
    for pbe in root.findall(".//msb:PostBuildEvent/msb:Command", NS):
        text = pbe.text or ""
        if "setlocal set PYTHONPATH=" in text:
            text = text.replace("setlocal set ", "setlocal\r\nset ")
            if '"$(TargetPath)"' in text and "\r\n\"$(TargetPath)\"" not in text:
                text = text.replace('"$(TargetPath)"', '\r\n"$(TargetPath)"')
            pbe.text = text
            changed = True
    return changed

def patch_vcxproj(rel, want_target, exe):
    p = ROOT / rel
    if not p.exists():
        CHANGES.append(f"{rel}: MISSING")
        return
    backup(p)
    ET.register_namespace('', NS["msb"])
    tree = ET.parse(p)
    c1 = set_targetname_everywhere(tree, want_target)
    c2 = fix_outputfile(tree, exe)
    c3 = fix_postbuild_newlines(tree)
    if any((c1, c2, c3)):
        tree.write(p, encoding="utf-8", xml_declaration=True)
        CHANGES.append(f"{rel}: CHANGED (TargetName/OutputFile/PostBuild)")
    else:
        CHANGES.append(f"{rel}: OK/NOOP (already aligned)")

def main():
    patch_cli_banner()
    patch_vcxproj("PCbuild/python.vcxproj",  "trump",  "trump.exe")
    patch_vcxproj("PCbuild/pythonw.vcxproj", "trumpw", "trumpw.exe")
    print("\n".join(CHANGES))

if __name__ == "__main__":
    main()
