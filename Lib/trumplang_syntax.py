
# Auto-generated TL3a: Trump syntax preprocessor & loader
import io, os, re, sys, tokenize, importlib.abc, importlib.machinery, builtins

# --- Aliases (multiple phrases => one token) ---
# Uppercase, no punctuation here; we normalize input tokens before matching.
ALIASES = {
    # def
    ("LET","ME","TELL","YOU"): "def",
    ("IVE","BEEN","SAYING","THIS","FOR","A","LONG","TIME"): "def",
    ("NOBODY","TALKS","ABOUT","THIS","ENOUGH"): "def",
    ("SO","IMPORTANT"): "def",
    ("EVERYONE","AGREES"): "def",

    # if / elif / else
    ("BELIEVE","ME",): "if",
    ("ON","THE","OTHER","HAND"): "elif",
    ("SADLY",): "else",

    # loops
    ("KEEP","GOING"): "while",
    ("FOR","THE","PEOPLE"): "for",

    # flow control twist
    ("CONTRADICT","THE","NARRATIVE"): "break",
    ("MOVE","ALONG"): "continue",

    # truthiness
    ("ABSOLUTELY",): "True",
    ("FAKE","NEWS"): "False",
    ("EMPTY","CHAIR"): "None",

    # operators
    ("AND","BY","THE","WAY"): "and",
    ("OR","MAYBE"): "or",
    ("WRONG",): "not",

    # return / print
    ("BRING","IT","BACK"): "return",
    ("I","SAID","IT","FIRST"): "print",
    # --- TL3b additions ---
    ("LOOK","FOLKS"): "print",
    ("YOU","WONT","BELIEVE","THIS"): "print",
    ("SO","TRUE","SO","TRUE"): "return",
    ("TOTAL","SUCCESS"): "return",
    ("THIS","I","CAN","TELL","YOU"): "if",
    ("PEOPLE","ARE","SAYING"): "else",
    ("KEEP","WINNING"): "continue",
    ("MAKE","IT","STOP"): "break",
    ("IN",): "in",

}

# Allow punctuation variants like "BELIEVE ME," or trailing ":" on control heads.
# We'll drop a trailing comma and keep ":" as required by Python syntax.
PUNCT_DROP = {","}
PUNCT_KEEP = {":"}  # we keep ":"; if the phrase ends with it, we emit ":" after the mapped keyword

def _is_word(tok):
    return tok.type == tokenize.NAME and tok.string.isidentifier()

def _is_punct(tok):
    return tok.type == tokenize.OP and tok.string in {",", ":"}

def _canon(s):  # normalize NAMEs like "I’ve" -> "IVE", strip apostrophes/curly quotes
    s = s.upper()
    s = s.replace("’","'").replace("‘","'").replace("“",'"').replace("”",'"')
    s = s.replace("'","")
    return s

# Fast index by first word to reduce matching cost
FIRST = {}
for key, val in ALIASES.items():
    FIRST.setdefault(key[0], []).append((key, val))

class TrumpSyntaxError(SyntaxError): pass

def translate_source(src: str, *, strict: bool, filename: str="<unknown>") -> str:
    """
    Token-based phrase replacer:
      - Only operates on code tokens (never touches strings/comments).
      - Matches multi-word sequences -> Python keywords.
      - Enforces 'no break' rule in strict mode (suggests CONTRADICT THE NARRATIVE).
    """
    out = []
    g = tokenize.generate_tokens(io.StringIO(src).readline)
    buffered = []
    pending_colon = False

    def flush_buffer():
        nonlocal pending_colon
        if buffered:
            out.extend(tokline(t) for t in buffered)
            buffered.clear()
        if pending_colon:
            out.append(":")
            pending_colon = False

    def tokline(t):
        return t.line if t.type in (tokenize.NL, tokenize.NEWLINE) else t.string

    try:
        tokens = list(g)
    except tokenize.TokenError as e:
        raise

    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]

        # enforce 'no break' rule
        if strict and t.type == tokenize.NAME and t.string == "break":
            raise TrumpSyntaxError("Use 'CONTRADICT THE NARRATIVE' instead of 'break' in TrumpLang strict mode")
        if strict and t.type == tokenize.NAME and t.string == "continue":
            raise TrumpSyntaxError("Use 'MOVE ALONG' instead of 'continue' in TrumpLang strict mode")

        # Try phrase match at this position (sequence of NAME/OP)
        if _is_word(t):
            start = i
            words = []
            punct = None
            j = i
            while j < n and (_is_word(tokens[j]) or _is_punct(tokens[j])):
                if _is_word(tokens[j]):
                    words.append(_canon(tokens[j].string))
                else:
                    punct = tokens[j].string  # only track the last punct in phrase
                # Tentatively stop if newline/indent/dedent soon?
                j += 1
                # Limit phrase window so it can't eat whole lines
                if len(words) > 8:
                    break

            replaced = False
            if words:
                first = words[0]
                for key, mapped in FIRST.get(first, ()):
                    L = len(key)
                    if words[:L] == list(key):
                        # Confirm the raw tokens match in shape (NAME/OP), don’t cross NEWLINE
                        # Compute how many concrete tokens to consume (including optional trailing punct)
                        consume = 0
                        seen_words = 0
                        k = start
                        while k < n and seen_words < L:
                            if _is_word(tokens[k]):
                                seen_words += 1
                            elif _is_punct(tokens[k]):
                                # phrase shouldn't include punctuation *between* words
                                break
                            consume += 1
                            k += 1
                        # optional punctuation immediately after the phrase
                        keep_colon = False
                        drop_punct = False
                        if k < n and _is_punct(tokens[k]):
                            if tokens[k].string in PUNCT_DROP:
                                drop_punct = True
                                consume += 1
                            elif tokens[k].string in PUNCT_KEEP:
                                keep_colon = True
                                consume += 1

                        # Emit mapped keyword
                        out.append(mapped)
                        if keep_colon:
                            out.append(":")
                        elif mapped in ("if","elif","else","for","while","def") and not keep_colon:
                            # let Python syntax demand a ":" later; don't auto-add here unless explicitly present
                            pass

                        i = start + consume
                        replaced = True
                        break
            if replaced:
                continue

        # default: pass token through
        if t.type in (tokenize.NL, tokenize.NEWLINE):
            out.append(t.line)
        else:
            out.append(t.string)
        i += 1

    return "".join(out)

# --- Loader: .trump files ---
class TrumpLoader(importlib.machinery.SourceFileLoader):
    def get_data(self, path):
        data = super().get_data(path)
        try:
            text = data.decode('utf-8')
        except Exception:
            return data
        strict = True  # .trump files are always strict
        text2 = translate_source(text, strict=strict, filename=path)
        return text2.encode('utf-8')

class TrumpFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # Allow 'import foo' where foo.trump exists on sys.path
        name = fullname.rsplit(".", 1)[-1]
        search = path or sys.path
        for base in search:
            p = os.path.join(base, name + ".trump")
            if os.path.isfile(p):
                loader = TrumpLoader(fullname, p)
                return importlib.machinery.ModuleSpec(fullname, loader)
        return None

def _mode_enabled():
    # -X trumplang=strict or env TRUMP_SYNTAX=1
    for x in getattr(sys, "_xoptions", ()):
        if x.lower().startswith("trumplang=") and "strict" in x.lower():
            return True
    if os.environ.get("TRUMP_SYNTAX","").strip() in ("1","true","yes","on"):
        return True
    return False

_ORIG_COMPILE = builtins.compile

def _compile_hook(source, filename, mode, flags=0, dont_inherit=False, optimize=-1):
    try:
        strict = _mode_enabled() or (isinstance(filename, str) and filename.endswith(".trump"))
        if strict and isinstance(source, str):
            source = translate_source(source, strict=True, filename=filename or "<string>")
    except TrumpSyntaxError as e:
        raise SyntaxError(str(e))
    return _ORIG_COMPILE(source, filename, mode, flags, dont_inherit, optimize)

def install():
    # Enable for: .trump imports, and compile() hijack when strict mode is on
    if TrumpFinder not in map(type, sys.meta_path):
        sys.meta_path.insert(0, TrumpFinder())
    builtins.compile = _compile_hook

# Called from site.py bootstrap when strict mode is requested
def bootstrap_if_requested():
    if _mode_enabled():
        install()
