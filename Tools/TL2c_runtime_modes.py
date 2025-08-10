#!/usr/bin/env python3
from pathlib import Path
import re, shutil

root = Path(__file__).resolve().parents[1]

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    bak = path.with_suffix(path.suffix + ".bak_TL2c")
    if not bak.exists() and path.exists():
        shutil.copy2(path, bak)
    path.write_text(text, encoding="utf-8")
    print(("Updated" if path.exists() else "Added"), path)

# --- rich rant/press content (pulls ideas you shared) ---
rhetoric = r'''
import os, random

if (seed := os.environ.get("TRUMPSEED")):
    try: random.seed(int(seed))
    except Exception: random.seed(seed)

POSITIVE = [
    "Total respect. It’s beautiful.",
    "Incredible. People are saying it’s the best.",
    "Tremendous result. Everyone agrees.",
    "So strong. Very strong.",
    "Historic. Never been done before.",
    "We’re doing numbers—big numbers.",
    "People can’t believe how good it is.",
    "World‑class. The best anywhere.",
    "They said it couldn’t be done—done.",
    "Winning like you wouldn’t believe.",
    "Legendary performance. Off the charts.",
    "Unbelievable. They’re calling it perfect.",
    "We love to see it. Everybody loves it.",
    "Exactly as predicted. Nailed it.",
    "Picture‑perfect. Couldn’t be better.",
]

NEGATIVE = [
    "Sad! Nobody’s ever seen anything like it.",
    "Disaster. We inherited this.",
    "Very unfair. Everyone knows it.",
    "Total witch hunt against math.",
    "Crooked situation. Not good.",
    "Rigged from day one. Frankly.",
    "A lot of problems—terrible problems.",
    "We’re looking into it. Not pretty.",
    "Could have been prevented. Not by me.",
    "Embarrassing. People are talking.",
    "Out of control. A complete mess.",
    "Not what we wanted. Believe me.",
    "They botched it. Everyone says so.",
    "We’ll fix it—fast. But wow.",
    "Should never happen again. Ever.",
]

PRESS = [
    "A lot of people don’t understand this, but it’s very technical.",
    "Look, folks, I didn’t build it, but I know how it works. Trust me.",
    "We’re looking into it. There may have been interference.",
    "Nobody could’ve seen this coming, but we handled it better than anyone.",
    "Some people say it’s the worst error ever—people are saying.",
    "We’ve got tremendous experts. The best people.",
    "This would’ve never happened under my administration.",
    "We inherited a mess, but we’re doing numbers now—big numbers.",
    "We found the bug. It was hiding. Nobody else could’ve found it.",
    "Don’t worry, we’re going to fix it. Fast. Very fast.",
]

def _rate():
    try: return max(0.0, min(1.0, float(os.environ.get("TRUMP_RANT_RATE", "0.35"))))
    except Exception: return 0.35

def pick_rants(max_n: int, positive_bias: bool):
    pool = POSITIVE if positive_bias else NEGATIVE
    out = []
    while len(out) < max_n and random.random() < _rate():
        out.append(random.choice(pool))
    return out
'''

bootstrap = r'''
import os, sys, builtins, traceback, random
from .trumplang_rhetoric import pick_rants, PRESS as PRESS_MONOLOGUES

def _mode():
    m = (os.environ.get("TRUMPMODE") or "").strip().lower()
    if not m:
        for x in getattr(sys, "_xoptions", ()):
            if x.lower().startswith("trumplang="):
                m = x.split("=",1)[1].strip().lower()
                break
    return m

def _max(default_normal: int) -> int:
    try: return int(os.environ.get("TRUMP_MAX_RANTS", str(default_normal)))
    except Exception: return default_normal

def _wrap_print(max_rants: int, positive_bias: bool):
    old_print = builtins.print
    def trump_print(*args, **kwargs):
        old_print(*args, **kwargs)
        for riff in pick_rants(max_n=max_rants, positive_bias=positive_bias):
            old_print(riff)
    builtins.print = trump_print

def _press_excepthook(exc_type, exc, tb):
    sys.stderr.write("🚨 Something happened, folks.\n")
    sys.stderr.write(">>> " + random.choice(PRESS_MONOLOGUES) + "\n")
    cap = _max(default_normal=5)  # press gets up to 5 negatives by default
    for riff in pick_rants(max_n=cap, positive_bias=False):
        sys.stderr.write("— " + riff + "\n")
    last = traceback.extract_tb(tb)[-1] if tb else None
    if last:
        sys.stderr.write(f"📍 {last.filename}:{last.lineno} in {last.name}\n")
    sys.stderr.write(f"{exc_type.__name__}: {exc}\n")

def _install():
    m = _mode()
    if m in ("press", "press-conference", "pc"):
        _wrap_print(_max(default_normal=5), positive_bias=True)
        sys.excepthook = _press_excepthook
    elif m in ("rant", "rants"):
        _wrap_print(_max(default_normal=2), positive_bias=True)

_install()
'''

# Write/refresh Lib files
write(root/"Lib"/"trumplang_rhetoric.py", rhetoric)
write(root/"Lib"/"trumplang_bootstrap.py", bootstrap)

# Ensure Lib/site.py loads bootstrap when TRUMPMODE or -X is set
site_py = root/"Lib"/"site.py"
s = site_py.read_text(encoding="utf-8", errors="ignore")
if "_trumplang_maybe_bootstrap" not in s:
    hook = r'''
# --- TrumpLang hook: conditionally load bootstrap for rant/press modes ---
def _trumplang_maybe_bootstrap():
    import os, sys
    mode = (os.environ.get("TRUMPMODE") or "").strip()
    if not mode:
        for x in getattr(sys, "_xoptions", ()):
            if x.lower().startswith("trumplang="):
                mode = x.split("=",1)[1]
                break
    if mode:
        try:
            import trumplang_bootstrap  # noqa: F401
        except Exception as e:
            sys.stderr.write(f"[TrumpLang] bootstrap failed: {e}\n")
_trumplang_maybe_bootstrap()
# --- end TrumpLang hook ---
'''
    s = s + "\n" + hook
    write(site_py, s)
else:
    print("Site hook already present; no change.")
print("TL2c: done.")
