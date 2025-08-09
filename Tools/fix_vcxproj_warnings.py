#!/usr/bin/env python3
from pathlib import Path
import re, shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"msb": "http://schemas.microsoft.com/developer/msbuild/2003"}
ET.register_namespace('', NS["msb"])

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

def force_global_targetname(tree, want):
    root = tree.getroot()
    # Append a new unconditional PropertyGroup at the end so it wins
    grp = ET.SubElement(root, f"{{{NS['msb']}}}PropertyGroup")
    tn = ET.SubElement(grp, f"{{{NS['msb']}}}TargetName")
    tn.text = want
    return True

def fix_outputfile_and_postbuild(tree, exe_name):
    root = tree.getroot()
    changed = False
    # Ensure Link/OutputFile uses $(OutDir)<exe_name>
    for link in root.findall(".//msb:ItemDefinitionGroup/msb:Link", NS):
        of = link.find("msb:OutputFile", NS)
        if of is None:
            of = ET.SubElement(link, f"{{{NS['msb']}}}OutputFile")
        desired = f"$(OutDir){exe_name}"
        if (of.text or "").strip().lower() != desired.lower():
            of.text = desired
            changed = True
    # Fix post-build validator to use $(TargetPath) (instead of hardcoded python.exe)
    for cmd in root.findall(".//msb:PostBuildEvent/msb:Command", NS):
        text = cmd.text or ""
        new = re.sub(r'PCbuild\\amd64\\python\.exe', '$(TargetPath)', text, flags=re.I)
        # also restore CRLF between setlocal / set / "$(TargetPath)"
        new = new.replace("setlocal set ", "setlocal\r\nset ")
        if '"$(TargetPath)"' in new and "\r\n\"$(TargetPath)\"" not in new:
            new = new.replace('"$(TargetPath)"', '\r\n"$(TargetPath)"')
        if new != text:
            cmd.text = new
            changed = True
    return changed

def process(project_rel, want_target, exe_name):
    p = ROOT / project_rel
    if not p.exists():
        print(f"{project_rel}: MISSING")
        return
    backup(p)
    tree = ET.parse(p)
    c1 = force_global_targetname(tree, want_target)
    c2 = fix_outputfile_and_postbuild(tree, exe_name)
    tree.write(p, encoding="utf-8", xml_declaration=True)
    print(f"{project_rel}: CHANGED (global TargetName + OutputFile/PostBuild)")

process("PCbuild/python.vcxproj",  "trump",  "trump.exe")
process("PCbuild/pythonw.vcxproj", "trumpw", "trumpw.exe")
