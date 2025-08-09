#!/usr/bin/env python3
"""
Probe TrumpLang TL1 inventory (no changes) — writes JSON + text report.

Outputs:
  build/probe_TL1.json
  build/probe_TL1.txt

Run:
  python3 tools/probe_TL1_inventory.py
"""

from pathlib import Path
import re, json, sys
import xml.etree.ElementTree as ET
from textwrap import indent

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "build"
OUTDIR.mkdir(parents=True, exist_ok=True)

def read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return ""

def grep(path: Path, patterns, flags=0, context=2):
    text = read(path)
    hits = []
    if not text:
        return hits
    for pat in (patterns if isinstance(patterns, (list, tuple)) else [patterns]):
        for m in re.finditer(pat, text, flags):
            line_idx = text.count("\n", 0, m.start())
            lines = text.splitlines()
            start = max(0, line_idx - context)
            end = min(len(lines), line_idx + context + 1)
            snippet = "\n".join(f"{i+1:>6}: {lines[i]}" for i in range(start, end))
            hits.append({
                "pattern": pat,
                "lineno": line_idx + 1,
                "span": [m.start(), m.end()],
                "snippet": snippet
            })
    return hits

def msproj_targets(vcxproj: Path):
    info = {"exists": vcxproj.exists(), "targets": []}
    if not vcxproj.exists():
        return info
    ET.register_namespace('', "http://schemas.microsoft.com/developer/msbuild/2003")
    tree = ET.parse(vcxproj)
    root = tree.getroot()
    ns = {'msb': root.tag.split('}')[0].strip('{')}
    for cfg in ("Debug", "Release"):
        for plat in ("x64",):
            cond = f"'$(Configuration)|$(Platform)'=='{cfg}|{plat}'"
            groups = root.findall(f".//msb:PropertyGroup[@Condition=\"{cond}\"]", ns)
            for g in groups:
                tn = g.find("msb:TargetName", ns)
                info["targets"].append({"cfg": cfg, "plat": plat, "target": (tn.text if tn is not None else None)})
    return info

def detect_version():
    # Prefer Include/patchlevel.h
    paths = [
        ROOT / "Include" / "patchlevel.h",
        ROOT / "PC" / "pyconfig.h"
    ]
    ver = {}
    rx = re.compile(r'#define\s+PY_(MAJOR|MINOR|MICRO)_VERSION\s+(\d+)')
    for p in paths:
        txt = read(p)
        if not txt:
            continue
        for m in rx.finditer(txt):
            ver[m.group(1).lower()] = int(m.group(2))
        if ver:
            break
    if ver:
        ver_str = f"{ver.get('major','?')}.{ver.get('minor','?')}.{ver.get('micro','?')}"
    else:
        ver_str = "unknown"
    return {"version": ver_str, "source": str(p) if ver else None}

def first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None

report = {
    "root": str(ROOT),
    "version": detect_version(),
    "files": {},
    "vcxproj": {},
}

# 1) Banner formatting site
getversion = ROOT / "Python" / "getversion.c"
report["files"]["Python/getversion.c"] = {
    "exists": getversion.exists(),
    "banner_hits": grep(getversion, r'PyOS_snprintf\([^;]*["\']Python %s.*["\']', flags=re.DOTALL) or
                   grep(getversion, r'["\']Python %s \(%s\)["\']')
}

# 2) Program name injection anchor
programs = ROOT / "Programs" / "python.c"
report["files"]["Programs/python.c"] = {
    "exists": programs.exists(),
    "config_init_hits": grep(programs, r'PyConfig_InitPythonConfig\s*\(\s*&config\s*\)\s*;', flags=0, context=4),
    "already_sets_program_name": grep(programs, r'program_name.*L"trump"', flags=0, context=3)
}

# 3) sys.implementation site
sysmodule = ROOT / "Python" / "sysmodule.c"
report["files"]["Python/sysmodule.c"] = {
    "exists": sysmodule.exists(),
    "cpython_name_hits": grep(sysmodule, r'["\']cpython["\']', context=3),
    "cache_tag_hits": grep(sysmodule, r'cache_tag|cpython-', context=3)
}

# 4) Env var sites for HOME/PATH (Windows vs cross-platform moved around)
env_candidate_paths = [
    ROOT / "PC" / "getpathp.c",
    ROOT / "Python" / "pathconfig.c",
    ROOT / "Modules" / "getpath.c",
]
env_file = first_existing(env_candidate_paths)
if env_file:
    report["files"][str(env_file.relative_to(ROOT))] = {
        "exists": True,
        "pyhome_hits": grep(env_file, r'PYTHONHOME', context=2),
        "pypath_hits": grep(env_file, r'PYTHONPATH', context=2),
        "trhome_hits": grep(env_file, r'TRUMPHOME', context=2),
        "trpath_hits": grep(env_file, r'TRUMPPATH', context=2),
    }
else:
    report["files"]["<env_lookup_file>"] = {"exists": False}

# 5) vcxproj target names
py_vcx = ROOT / "PCbuild" / "python.vcxproj"
pyw_vcx = ROOT / "PCbuild" / "pythonw.vcxproj"
report["vcxproj"]["PCbuild/python.vcxproj"] = msproj_targets(py_vcx)
report["vcxproj"]["PCbuild/pythonw.vcxproj"] = msproj_targets(pyw_vcx)

# 6) Extra: count occurrences to sanity check
def count_token(path, token):
    return read(path).count(token) if path.exists() else 0

report["counts"] = {
    "getversion.c:Python literal count": count_token(getversion, "Python %s"),
    "sysmodule.c:'cpython' literal count": count_token(sysmodule, '"cpython"'),
}

# Write JSON
json_path = OUTDIR / "probe_TL1.json"
json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

# Write a friendly text summary
lines = []
lines.append(f"Repo: {report['root']}")
lines.append(f"Detected CPython version: {report['version']['version']} (source: {report['version']['source']})\n")

def add_file_section(title, key):
    f = report["files"].get(key, {})
    lines.append(f"[{title}] {key}  exists={f.get('exists')}")
    for subk, val in f.items():
        if subk == "exists": continue
        if isinstance(val, list):
            lines.append(f"  {subk}: {len(val)} hits")
            for h in val[:3]:
                lines.append(indent(h['snippet'], "    ") + ("\n    ...\n" if len(val) > 3 else ""))
        else:
            lines.append(f"  {subk}: {val}")
    lines.append("")

add_file_section("Banner", "Python/getversion.c")
add_file_section("Programs Init", "Programs/python.c")
add_file_section("Sys Implementation", "Python/sysmodule.c")

for k, v in report["files"].items():
    if k.endswith("getpathp.c") or k.endswith("pathconfig.c") or k.endswith("getpath.c"):
        add_file_section("Env Lookup", k)

lines.append("[VCXPROJ Targets]")
for k, v in report["vcxproj"].items():
    lines.append(f"  {k}: exists={v['exists']}")
    for t in v.get("targets", []):
        lines.append(f"    {t['cfg']}|{t['plat']}: {t['target']}")
lines.append("")
txt_path = OUTDIR / "probe_TL1.txt"
txt_path.write_text("\n".join(lines), encoding="utf-8")

print(f"Wrote:\n  {json_path}\n  {txt_path}")
