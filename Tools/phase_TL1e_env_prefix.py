from pathlib import Path
import re, shutil

root = Path(__file__).resolve().parents[1]
pre = root / "Python" / "preconfig.c"
ic  = root / "Python" / "initconfig.c"

# --- patch Python/preconfig.c: _Py_GetEnv prefers TRUMP* for HOME/PATH ---
sp = pre.read_text(encoding="utf-8", errors="ignore")
bp = pre.with_suffix(pre.suffix + ".bak_TL1e")
if not bp.exists(): shutil.copy2(pre, bp)

needle = "const char*\n_Py_GetEnv(int use_environment, const char *name)\n{"
if needle in sp and "TRUMPHOME" not in sp:
    insert_after = needle
    extra = r'''
    /* TrumpLang: prefer TRUMPHOME/TRUMPPATH when CPython asks for PYTHONHOME/PYTHONPATH */
    if (!use_environment) {
        return NULL;
    }
    if (name && strcmp(name, "PYTHONHOME") == 0) {
        const char *v = getenv("TRUMPHOME");
        if (v) return v;
    }
    if (name && strcmp(name, "PYTHONPATH") == 0) {
        const char *v = getenv("TRUMPPATH");
        if (v) return v;
    }
'''
    sp = sp.replace(needle, needle + extra)
    pre.write_text(sp, encoding="utf-8")
    print("OK: preconfig.c patched (_Py_GetEnv prefers TRUMP*)")
else:
    print("preconfig.c: already patched or anchor not found")

# --- patch Python/initconfig.c: help text mentions TRUMP* vars (cosmetic only) ---
si = ic.read_text(encoding="utf-8", errors="ignore")
bi = ic.with_suffix(ic.suffix + ".bak_TL1e")
if not bi.exists(): shutil.copy2(ic, bi)

# Add TRUMPHOME/TRUMPPATH lines to usage_envvars string, if present
si_new = re.sub(
    r'(\"Environment variables that change behavior:\\n\".*?\"PYTHONPATH\s+:\s+\'%lc\'-separated.*?\\n\")',
    r'\1"TRUMPHOME      : preferred alias for PYTHONHOME\\n"'
    r'"TRUMPPATH       : preferred alias for PYTHONPATH\\n"',
    si,
    flags=re.S
)
if si_new != si:
    ic.write_text(si_new, encoding="utf-8")
    print("OK: initconfig.c usage text updated to mention TRUMP*")
else:
    print("initconfig.c: usage text unchanged (pattern not found or already updated)")
