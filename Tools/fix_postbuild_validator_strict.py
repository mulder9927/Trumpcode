# Tools/fix_postbuild_validator_strict.py
from pathlib import Path; import shutil, re
p = Path("PCbuild/python.vcxproj")
s = p.read_text(encoding="utf-8", errors="ignore")
bak = p.with_suffix(p.suffix + ".bak_post3")
if not bak.exists(): shutil.copy2(p, bak)
new = re.sub(r'PCbuild\\amd64\\python\.exe', '$(TargetPath)', s, flags=re.I)
new = new.replace('setlocal set PYTHONPATH=', 'setlocal&#x0D;&#x0A;set PYTHONPATH=')
new = new.replace('"$(TargetPath)"', '&#x0D;&#x0A;"$(TargetPath)"')
if new != s:
    p.write_text(new, encoding="utf-8")
    print("OK: fixed post-build validator to use $(TargetPath).")
else:
    print("No change needed.")
