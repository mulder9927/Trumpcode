from pathlib import Path
import xml.etree.ElementTree as ET
import re, shutil

ROOT = Path(".").resolve()
NS = {"msb":"http://schemas.microsoft.com/developer/msbuild/2003"}
ET.register_namespace('', NS["msb"])

def backup(p: Path):
    b = p.with_suffix(p.suffix+".bak2")
    if not b.exists():
        shutil.copy2(p, b)

def ensure_global_targetname(tree, want):
    root = tree.getroot()
    # Put an unconditional PropertyGroup at top so it wins
    groups = root.findall("./msb:PropertyGroup", NS)
    tgt_grp = None
    for g in groups:
        if g.get("Condition") is None:
            tgt_grp = g; break
    if tgt_grp is None:
        tgt_grp = ET.Element(f"{{{NS['msb']}}}PropertyGroup")
        root.insert(0, tgt_grp)
    tn = tgt_grp.find("msb:TargetName", NS)
    if tn is None:
        tn = ET.SubElement(tgt_grp, f"{{{NS['msb']}}}TargetName")
    tn.text = want
    return True

def fix_output_and_postbuild(tree, exe):
    root = tree.getroot()
    changed = False
    # Ensure Link/OutputFile == $(OutDir)<exe>
    for link in root.findall(".//msb:ItemDefinitionGroup/msb:Link", NS):
        of = link.find("msb:OutputFile", NS)
        if of is None:
            of = ET.SubElement(link, f"{{{NS['msb']}}}OutputFile")
        desired = f"$(OutDir){exe}"
        if (of.text or "").strip().lower() != desired.lower():
            of.text = desired
            changed = True
    # PostBuild: point validator at $(TargetPath) and fix line breaks
    for cmd in root.findall(".//msb:PostBuildEvent/msb:Command", NS):
        text = cmd.text or ""
        new = re.sub(r'PCbuild\\amd64\\python\.exe', '$(TargetPath)', text, flags=re.I)
        new = new.replace("setlocal set ", "setlocal\r\nset ")
        if '"$(TargetPath)"' in new and "\r\n\"$(TargetPath)\"" not in new:
            new = new.replace('"$(TargetPath)"', '\r\n"$(TargetPath)"')
        if new != text:
            cmd.text = new
            changed = True
    return changed

def process(name, want, exe):
    p = ROOT / "PCbuild" / name
    if not p.exists():
        print(f"{name}: MISSING"); return
    tree = ET.parse(p)
    ensure_global_targetname(tree, want)
    fix_output_and_postbuild(tree, exe)
    backup(p)
    tree.write(p, encoding="utf-8", xml_declaration=True)
    print(f"{name}: patched")

process("python.vcxproj",  "trump",  "trump.exe")
process("pythonw.vcxproj", "trumpw", "trumpw.exe")
