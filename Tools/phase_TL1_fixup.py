#!/usr/bin/env python3
# TL1 fixups for CPython 3.12.11 tree (banner, program_name, TRUMPHOME)
from pathlib import Path
import re, sys, shutil

ROOT = Path(__file__).resolve().parents[1]
changes = []

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

def patch_getversion():
    p = ROOT / "Python" / "getversion.c"
    if not p.exists(): return "Python/getversion.c: MISSING"
    s = p.read_text(encoding="utf-8", errors="ignore")

    # Find any PyOS_snprintf(...) that formats a banner with "Python %s"
    # Be robust to spacing and variable names.
    if 'TrumpLang %s' in s:
        return "Python/getversion.c: OK/NOOP (already TrumpLang)"
    if 'Python %s' not in s and 'Python\\0' not in s:
        # Fallback: replace any "Python " inside a string literal used in the banner function
        # Narrow scope to the Py_GetVersion function body to avoid false positives.
        m = re.search(r'\bPy_GetVersion\s*\([^)]*\)\s*{(?P<body>.*?)}', s, re.S)
        if m:
            body = m.group("body")
            new_body = re.sub(r'"Python ', '"TrumpLang ', body)
            if new_body != body:
                backup(p)
                s = s[:m.start("body")] + new_body + s[m.end("body"):]
                p.write_text(s, encoding="utf-8")
                return "Python/getversion.c: CHANGED (banner literal fallback)"
        return "Python/getversion.c: WARN (couldn’t locate banner literal)"
    # Direct replacement path
    new = re.sub(r'"Python %s\s*\(%s\)"', r'"TrumpLang %s (%s)"', s)
    if new != s:
        backup(p); p.write_text(new, encoding="utf-8")
        return "Python/getversion.c: CHANGED (banner)"
    # Broader replace in case of slight formatting differences
    new = s.replace('"Python %s"', '"TrumpLang %s"')
    if new != s:
        backup(p); p.write_text(new, encoding="utf-8")
        return "Python/getversion.c: CHANGED (banner alt)"
    return "Python/getversion.c: WARN (pattern not found)"

def patch_programs_program_name():
    p = ROOT / "Programs" / "python.c"
    if not p.exists(): return "Programs/python.c: MISSING"
    s = p.read_text(encoding="utf-8", errors="ignore")
    if 'program_name' in s and 'L"trump"' in s:
        return "Programs/python.c: OK/NOOP (program_name already set)"

    # Strategy: insert after any PyConfig_Init*(&config); line, or just before Py_InitializeFromConfig
    anchor = re.search(r'PyConfig_Init\w*Config\s*\(\s*&config\s*\)\s*;', s)
    insertion = '\n    (void)PyConfig_SetString(&config, &config.program_name, L"trump");\n'
    if anchor:
        idx = anchor.end()
        backup(p)
        s = s[:idx] + insertion + s[idx:]
        p.write_text(s, encoding="utf-8")
        return "Programs/python.c: CHANGED (after PyConfig_Init*Config)"
    # fallback: before Py_InitializeFromConfig(&config)
    anchor2 = re.search(r'Py_InitializeFromConfig\s*\(\s*&config\s*\)\s*;', s)
    if anchor2:
        idx = anchor2.start()
        backup(p)
        s = s[:idx] + insertion + s[idx:]
        p.write_text(s, encoding="utf-8")
        return "Programs/python.c: CHANGED (before Py_InitializeFromConfig)"
    return "Programs/python.c: WARN (no config init/initialize anchor found)"

def patch_pathconfig_trumphome():
    p = ROOT / "Python" / "pathconfig.c"
    if not p.exists():
        return "Python/pathconfig.c: MISSING"
    s = p.read_text(encoding="utf-8", errors="ignore")

    # Look for env reads using _Py_GetEnv(..., L"PYTHONHOME") or similar.
    # In 3.12.11 Windows, logic is a bit spread; we’ll patch all L"PYTHONHOME" literals to prefer TRUMPHOME with fallback.
    if 'TRUMPHOME' in s:
        return "Python/pathconfig.c: OK/NOOP (TRUMPHOME present)"
    # Replace occurrences of _Py_GetEnv(config, L"PYTHONHOME") with a two-line fetch that prefers TRUMPHOME
    pattern = r'(\bconst\s+wchar_t\s*\*\s*home\s*=\s*_Py_GetEnv\s*\(\s*config\s*,\s*L"PYTHONHOME"\s*\)\s*;\s*)'
    if re.search(pattern, s):
        repl = ('const wchar_t *home = _Py_GetEnv(config, L"TRUMPHOME");\n'
                '    if (home == NULL) home = _Py_GetEnv(config, L"PYTHONHOME");\n')
        new = re.sub(pattern, repl, s)
        if new != s:
            backup(p); p.write_text(new, encoding="utf-8")
            return "Python/pathconfig.c: CHANGED (TRUMPHOME preferred)"
    # If there’s no direct assignment, try a generic literal replacement at use sites
    if 'L"PYTHONHOME"' in s:
        new = s.replace('L"PYTHONHOME"', 'L"TRUMPHOME"')  # crude pref — but we must also add fallback
        # Add fallback nearby: attempt to find a subsequent NULL-check on 'home'; if absent, we’ll inject one.
        if new != s:
            # Try to inject fallback after the line that fetches home
            lines = s.splitlines(True)
            for i, line in enumerate(lines):
                if '_Py_GetEnv' in line and 'TRUMPHOME' in line:
                    # already done
                    break
                if '_Py_GetEnv' in line and 'PYTHONHOME' in line:
                    lines[i] = line.replace('L"PYTHONHOME"', 'L"TRUMPHOME"')
                    # insert fallback right after
                    lines.insert(i+1, '    if (home == NULL) home = _Py_GetEnv(config, L"PYTHONHOME");\n')
                    backup(p)
                    p.write_text(''.join(lines), encoding="utf-8")
                    return "Python/pathconfig.c: CHANGED (TRUMPHOME + fallback injected)"
    return "Python/pathconfig.c: WARN (couldn’t locate PYTHONHOME fetch site)"

def main():
    results = []
    results.append(patch_getversion())
    results.append(patch_programs_program_name())
    results.append(patch_pathconfig_trumphome())

    print("\n".join(results))
    # Fail if all were warnings or missing
    if all(r.startswith(("WARN", "MISSING")) or ": WARN" in r or ": MISSING" in r for r in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
