
import os, sys, builtins, traceback, random
import trumplang_rhetoric as _rhet

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
        for riff in _rhet.pick_rants(max_n=max_rants, positive_bias=positive_bias):
            old_print(riff)
    builtins.print = trump_print

def _press_excepthook(exc_type, exc, tb):
    sys.stderr.write("🚨 Something happened, folks.\n")
    sys.stderr.write(">>> " + random.choice(_rhet.PRESS) + "\n")
    cap = _max(default_normal=5)  # press gets up to 5 negatives by default
    for riff in _rhet.pick_rants(max_n=cap, positive_bias=False):
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
