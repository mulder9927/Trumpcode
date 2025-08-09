#!/usr/bin/env python3
# Kill MSBuild TargetPath warnings by forcing <TargetName> and <OutputFile>.
from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT/"PCbuild"/"python.vcxproj", ROOT/"PCbuild"/"pythonw.vcxproj"]
want = {"python.vcxproj": ("trump","trump.exe"), "pythonw.vcxproj": ("trumpw","trumpw.exe")}

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

for p in files:
    if not p.exists(): 
        print(f"{p} missing"); 
        continue
    tn, exe = want[p.name]
    s = p.read_text(encoding="utf-8", errors="ignore"); o = s
    # Force ALL <TargetName> … not just in conditioned groups
    s = re.sub(r'<TargetName>\s*pythonw?\s*</TargetName>', f'<TargetName>{tn}</TargetName>', s, flags=re.I)
    # Force Linker OutputFile to $(OutDir)trump(.exe)
    s = re.sub(r'<OutputFile>\s*\$\(OutDir\)\s*pythonw?\.exe\s*</OutputFile>',
               f'<OutputFile>$(OutDir){exe}</OutputFile>', s, flags=re.I)
    if s != o:
        backup(p); p.write_text(s, encoding="utf-8"); print(f"{p.name}: CHANGED")
    else:
        print(f"{p.name}: OK/NOOP")
