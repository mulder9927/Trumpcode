#!/usr/bin/env python3
"""
TL1 complete (identity split) for CPython 3.12.11 trees.

What this does (idempotent, with .bak backups):
1) Python/sysmodule.c
   - _PySys_ImplName       -> "trumplang"
   - _PySys_ImplCacheTag   -> "trumplang-<major><minor>"  (prefix swap)
   This fixes `sys.implementation` AND the shown banner/version string.

2) Programs/_bootstrap_python.c
   - After the first PyConfig_Init*Config(&config) call, insert:
       PyConfig_SetString(&config, &config.program_name, L"trump");
   so help/path text prefers "trump". (Skipped if already present.)

NOTE: Your repo’s env variable handling for PYTHONHOME/PYTHONPATH is spread across
      initconfig/pathconfig/getpath plumbing. We’ll do TRUMPHOME/TRUMPPATH
      as TL1b (separate, provably-correct patch) after this lands.
"""

from pathlib import Path
import re, shutil, sys

ROOT = Path(__file__).resolve().parents[1]
CHANGES = []

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

def patch_sysmodule_impl_identity():
    p = ROOT / "Python" / "sysmodule.c"
    if not p.exists():
        CHANGES.append("Python/sysmodule.c: MISSING")
        return
    s = p.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # 1) Impl name -> "trumplang"
    # Typical 3.12: static const char *_PySys_ImplName = "cpython";
    s = re.sub(
        r'(static\s+const\s+char\s*\*\s*_PySys_ImplName\s*=\s*")([^"]+)(";)',
        r'\1trumplang\3',
        s,
        count=1
    )

    # 2) Cache tag prefix -> trumplang-
    # Typical 3.12: static const char *_PySys_ImplCacheTag = "cpython-312";
    s = re.sub(
        r'(static\s+const\s+char\s*\*\s*_PySys_ImplCacheTag\s*=\s*")cpython-',
        r'\1trumplang-',
        s,
        count=1
    )

    if s != orig:
        backup(p)
        p.write_text(s, encoding="utf-8")
        CHANGES.append("Python/sysmodule.c: CHANGED (impl name + cache_tag)")
    else:
        CHANGES.append("Python/sysmodule.c: OK/NOOP (impl name + cache_tag already set)")

def patch_bootstrap_program_name():
    p = ROOT / "Programs" / "_bootstrap_python.c"
    if not p.exists():
        CHANGES.append("Programs/_bootstrap_python.c: MISSING")
        return
    s = p.read_text(encoding="utf-8", errors="ignore")
    if 'program_name' in s and 'L"trump"' in s:
        CHANGES.append("Programs/_bootstrap_python.c: OK/NOOP (program_name already set)")
        return

    # Find first PyConfig_Init*Config(&config); and inject a SetString right after
    m = re.search(r'(PyConfig_Init\w*Config\s*\(\s*&config\s*\)\s*;)', s)
    if not m:
        CHANGES.append("Programs/_bootstrap_python.c: WARN (no PyConfig_Init*Config anchor)")
        return

    idx = m.end()
    insertion = '\n    (void)PyConfig_SetString(&config, &config.program_name, L"trump");\n'
    new = s[:idx] + insertion + s[idx:]
    if new != s:
        backup(p)
        p.write_text(new, encoding="utf-8")
        CHANGES.append("Programs/_bootstrap_python.c: CHANGED (set default program_name=\"trump\")")
    else:
        CHANGES.append("Programs/_bootstrap_python.c: OK/NOOP (no change)")

def main():
    patch_sysmodule_impl_identity()
    patch_bootstrap_program_name()

    print("\n".join(CHANGES))
    # Exit nonzero if nothing changed and nothing was already OK/NOOP
    if all(x.startswith(("MISSING", "WARN")) for x in CHANGES):
        sys.exit(1)

if __name__ == "__main__":
    main()
