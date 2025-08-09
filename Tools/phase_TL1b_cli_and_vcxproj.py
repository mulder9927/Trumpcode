#!/usr/bin/env python3
"""
TL1b: CLI banner -> 'TrumpLang', and fix VCXPROJ Target/Command warnings.

- Patches 'Modules/main.c' to print "TrumpLang %s\n" when showing --version.
  (Covers printf sites around Py_GetVersion.)
- Also tries 'Programs/python.c' if that code path exists in your tree.
- Fixes PCbuild\python*.vcxproj:
    * Makes ALL <TargetName> 'trump'/'trumpw' (not just x64 configs).
    * Ensures <Link><OutputFile> and computed TargetPath agree.
    * Restores PostBuild 'setlocal' on separate lines (CRLF),
      or disables the ucrt validator if it keeps failing.

Idempotent; writes .bak the first time it changes each file.
"""

from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parents[1]
CHANGES = []

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():
        shutil.copy2(p, b)

def patch_cli_banner():
    changed_any = False
    for rel in ("Modules/main.c", "Programs/python.c"):
        p = ROOT / rel
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        orig = s

        # Typical sites:
        #   printf("Python %s\n", Py_GetVersion());
        #   Py_ExitStatusException ...; printf("Python %s\n", Py_GetVersion());
        s = re.sub(r'printf\(\s*"Python\s*%s\\n"\s*,\s*Py_GetVersion\(\)\s*\)',
                   r'printf("TrumpLang %s\n", Py_GetVersion())', s)

        # Just in case: string literal that says "Python " next to Py_GetVersion
        s = re.sub(r'"Python\s*%s\\n"', r'"TrumpLang %s\n"', s)

        if s != orig:
            backup(p)
            p.write_text(s, encoding="utf-8")
            CHANGES.append(f"{rel}: CHANGED (CLI banner)")
            changed_any = True
        else:
            CHANGES.append(f"{rel}: OK/NOOP (no banner site or already patched)")
    return changed_any

def patch_vcxproj(relpath, want_target):
    p = ROOT / relpath
    if not p.exists():
        CHANGES.append(f"{relpath}: MISSING")
        return

    s = p.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # 1) Force ALL <TargetName> to our desired name
    s, n1 = re.subn(r'<TargetName>\s*pythonw?\s*</TargetName>',
                    f'<TargetName>{want_target}</TargetName>', s, flags=re.I)

    # 2) Make Linker OutputFile match OutDir + desired exe
    exe = "trumpw.exe" if want_target == "trumpw" else "trump.exe"
    s, n2 = re.subn(r'<OutputFile>\s*\$\(OutDir\)pythonw?\.exe\s*</OutputFile>',
                    f'<OutputFile>$(OutDir){exe}</OutputFile>', s, flags=re.I)

    # 3) Fix flattened PostBuild Command: ensure CRLF line breaks after 'setlocal' and before "$(TargetPath)"
    s, n3 = re.subn(r'<Command>\s*setlocal\s+set\s+PYTHONPATH=',
                    '<Command>setlocal&#x0D;&#x0A;set PYTHONPATH=', s)
    s, n4 = re.subn(r'([^>])"\$\(TargetPath\)"', r'\1&#x0D;&#x0A;"$(TargetPath)"', s)

    # 4) If the validator keeps failing in your setup, you can comment this block to disable instead:
    #    (Uncomment next two lines to nuke the validator step)
    # s = re.sub(r'<PostBuildEvent>.*?</PostBuildEvent>', '<PostBuildEvent><Command></Command></PostBuildEvent>', s, flags=re.S)

    if s != orig:
        backup(p)
        p.write_text(s, encoding="utf-8")
        CHANGES.append(f"{relpath}: CHANGED (targets/outputfile/postbuild)")
    else:
        CHANGES.append(f"{relpath}: OK/NOOP (already aligned)")

def main():
    patch_cli_banner()
    patch_vcxproj("PCbuild/python.vcxproj", "trump")
    patch_vcxproj("PCbuild/pythonw.vcxproj", "trumpw")

    print("\n".join(CHANGES))

if __name__ == "__main__":
    main()
