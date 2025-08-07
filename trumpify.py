import os
import re

BASE_DIR = "./"  # Run from project root
RENAME_RULES = {
    "python.exe": "trump.exe",
    "pythonw.exe": "trumpw.exe",
    "python": "trump",
    "py": "tr",  # careful: may hit false positives
    "_Py": "_Tr",
    "PYTHON": "TRUMP",
    "PY_": "TR_",  # includes PY_VERSION etc.
    "PY3": "TR3",
}

EXCLUDED_DIRS = {".git", "__pycache__", "venv", "build", "PCbuild/arm64", "PCbuild/win64"}
EXCLUDED_EXTS = {".pyc", ".pyd", ".exe", ".dll", ".lib", ".obj", ".exp", ".png", ".ico", ".zip", ".tar", ".gz", ".bz2"}

log = []

def should_skip_file(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in EXCLUDED_EXTS or any(excluded in path for excluded in EXCLUDED_DIRS)

def scan_file_content(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for i, line in enumerate(lines, 1):
            for pattern, replacement in RENAME_RULES.items():
                if pattern in line:
                    log.append(f"[CONTENT] {path}:{i} → {pattern} → {replacement}\n")
    except:
        pass  # Binary or unreadable

def scan_filenames():
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            full_path = os.path.join(root, f)
            if should_skip_file(full_path):
                continue

            # Check filename
            for pattern, replacement in RENAME_RULES.items():
                if pattern in f:
                    log.append(f"[FILENAME] {full_path} → rename to {f.replace(pattern, replacement)}\n")

            # Check file contents
            scan_file_content(full_path)

# Run it
scan_filenames()

# Output results
with open("rename_dryrun.txt", "w", encoding="utf-8") as out:
    out.writelines(log)

print(f"Dry run complete. Found {len(log)} possible replacements.")
