#!/usr/bin/env python3
from pathlib import Path
import shutil, re

root = Path(__file__).resolve().parents[1]
ic = root / "Python" / "initconfig.c"

text = ic.read_text(encoding="utf-8", errors="ignore")
bak = ic.with_suffix(ic.suffix + ".bak_TL1e_fix")
if not bak.exists():
    shutil.copy2(ic, bak)

# Insert a TRUMPPATH read *before* the existing PYTHONPATH read.
anchor = re.compile(
    r'if\s*\(\s*config->pythonpath_env\s*==\s*NULL\s*\)\s*\{\s*'
    r'status\s*=\s*CONFIG_GET_ENV_DUP\(\s*config,\s*&config->pythonpath_env,'
    r'\s*L?"PYTHONPATH",\s*"PYTHONPATH"\s*\)\s*;\s*'
, re.S)

inject = (
    'if (config->pythonpath_env == NULL) {\n'
    '    /* TrumpLang: prefer TRUMPPATH when reading PYTHONPATH */\n'
    '    status = CONFIG_GET_ENV_DUP(config, &config->pythonpath_env,\n'
    '                                L"TRUMPPATH", "TRUMPPATH");\n'
    '    if (_PyStatus_EXCEPTION(status)) {\n'
    '        return status;\n'
    '    }\n'
    '}\n'
)

new = anchor.sub(inject + r'\g<0>', text, count=1)
if new == text:
    print("No change (anchor not found or already patched).")
else:
    ic.write_text(new, encoding="utf-8")
    print("OK: initconfig.c now reads TRUMPPATH before PYTHONPATH.")
