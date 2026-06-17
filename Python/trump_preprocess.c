/*
 * TrumpLang phrase pre-processor.
 *
 * Scans .trump source and replaces Trump phrases with their Python keyword
 * equivalents before the source reaches CPython's tokenizer/parser.
 *
 * Rules:
 *   - Matching is case-sensitive (Trump phrases are ALL CAPS by convention)
 *   - String literals (single or double quoted, including triple-quoted) are
 *     passed through unchanged so Trump phrases inside strings stay literal
 *   - Phrases are matched longest-first (greedy) to avoid prefix conflicts
 *   - Since every Trump phrase is longer than its Python equivalent, the
 *     output buffer is always <= input length
 */

#include "Python.h"
#include "pycore_trump.h"
#include <string.h>
#include <stdlib.h>

/* ── Phrase table ─────────────────────────────────────────────────────────
 * Entries MUST be ordered longest phrase first within each keyword group.
 * The scanning loop is greedy: first match wins.
 * ─────────────────────────────────────────────────────────────────────── */
typedef struct {
    const char *phrase;
    const char *keyword;
} TrumpEntry;

static const TrumpEntry _trump_phrases[] = {

    /* def */
    {"I'VE BEEN SAYING THIS FOR A LONG TIME",   "def"},
    {"NOBODY KNOWS MORE ABOUT THIS THAN ME",     "def"},
    {"NOBODY TALKS ABOUT THIS ENOUGH",           "def"},
    {"MANY PEOPLE DON'T KNOW THIS BUT",          "def"},
    {"SO IMPORTANT, LISTEN",                     "def"},
    {"LET ME TELL YOU",                          "def"},
    {"I'M THE BEST AT",                          "def"},
    {"EVERYONE AGREES",                          "def"},
    {"SO IMPORTANT",                             "def"},

    /* class */
    {"A TREMENDOUS ORGANIZATION CALLED",         "class"},
    {"THE TRUMP ORGANIZATION",                   "class"},
    {"MAKE AMERICA GREAT AGAIN",                 "class"},
    {"WORLD CLASS",                              "class"},
    {"BEST IN CLASS",                            "class"},

    /* return */
    {"AND THAT'S THE WINNER",                    "return"},
    {"EVERYBODY SAYS IT WORKS",                  "return"},
    {"NOBODY RETURNS BETTER THAN ME",            "return"},
    {"IT'S GONNA BE HUGE",                       "return"},
    {"TOTAL SUCCESS",                            "return"},
    {"WE'RE DONE HERE",                          "return"},
    {"BEAUTIFUL RESULT",                         "return"},
    {"WINNING",                                  "return"},

    /* if */
    {"PEOPLE ARE STARTING TO NOTICE",            "if"},
    {"MANY PEOPLE ARE STARTING TO SEE",          "if"},
    {"I'LL TELL YOU WHAT, IF",                   "if"},
    {"SOME PEOPLE WON'T SAY IT",                 "if"},
    {"SOME PEOPLE ARE SAYING",                   "if"},
    {"THIS I CAN TELL YOU",                      "if"},
    {"LOOK, THE TRUTH IS",                       "if"},
    {"IF YOU LOOK AT IT",                        "if"},
    {"IT'S OBVIOUS",                             "if"},
    {"FRANKLY, IF",                              "if"},

    /* elif */
    {"AND ANOTHER THING",                        "elif"},
    {"BUT ALSO CONSIDER",                        "elif"},
    {"SOME ARE ALSO SAYING",                     "elif"},
    {"OR WHAT ABOUT",                            "elif"},
    {"ANOTHER THING",                            "elif"},

    /* else */
    {"FAKE NEWS WOULD SAY",                      "else"},
    {"BUT SOME LOSERS THINK",                    "else"},
    {"MANY PEOPLE ARE SAYING",                   "else"},
    {"NOBODY KNOWS FOR SURE",                    "else"},
    {"ALTERNATIVE FACT",                         "else"},
    {"COULD BE WRONG, BUT",                      "else"},
    {"ON THE OTHER HAND",                        "else"},
    {"ALTERNATIVELY",                            "else"},
    {"WE'LL SEE",                                "else"},

    /* while */
    {"CAN'T STOP WON'T STOP",                   "while"},
    {"WE'RE IN THIS TOGETHER",                   "while"},
    {"WE'RE GONNA KEEP GOING",                   "while"},
    {"KEEP AMERICA GREAT",                       "while"},
    {"NEVER GIVE UP",                            "while"},
    {"KEEP IT GOING",                            "while"},
    {"AGAIN AND AGAIN",                          "while"},

    /* for */
    {"ONE BY ONE WE LOOK AT",                    "for"},
    {"WE'RE GOING THROUGH ALL OF",               "for"},
    {"LOOKING AT EVERY SINGLE",                  "for"},
    {"FOR EACH AND EVERY",                       "for"},
    {"GOING THROUGH EVERY",                      "for"},

    /* in */
    {"IN THE MIX WITH",                          "in"},
    {"INSIDE OF",                                "in"},
    {"PART OF",                                  "in"},
    {"AMONG",                                    "in"},
    {"IN",                                       "in"},

    /* break */
    {"WE'RE DONE HERE, STOP",                    "break"},
    {"I NEVER SAID THAT",                        "break"},
    {"TOTAL SHUTDOWN",                           "break"},
    {"STOP THE COUNT",                           "break"},
    {"SHUT IT DOWN",                             "break"},
    {"ENOUGH",                                   "break"},

    /* continue */
    {"MOVING FORWARD",                           "continue"},
    {"SKIP THE LOSERS",                          "continue"},
    {"KEEP GOING",                               "continue"},
    {"MOVE ON",                                  "continue"},
    {"NEXT ONE",                                 "continue"},

    /* pass */
    {"NOTHING TO SEE HERE",                      "pass"},
    {"PERFECT AS IS",                            "pass"},
    {"MOVE ALONG",                               "pass"},
    {"NO COMMENT",                               "pass"},
    {"STAND DOWN",                               "pass"},

    /* import */
    {"I KNOW PEOPLE, GET ME",                    "import"},
    {"BRING IN THE BEST",                        "import"},
    {"WE'RE GETTING",                            "import"},
    {"WE NEED",                                  "import"},
    {"GET ME",                                   "import"},

    /* from */
    {"DIRECTLY FROM",                            "from"},
    {"COMING FROM",                              "from"},
    {"SOURCED FROM",                             "from"},
    {"TAKEN FROM",                               "from"},
    {"FROM THE GREAT",                           "from"},

    /* as */
    {"WHICH WE CALL",                            "as"},
    {"ALSO CALLED",                              "as"},
    {"KNOWN AS",                                 "as"},
    {"WE CALL IT",                               "as"},
    {"NICKNAMED",                                "as"},

    /* try */
    {"TREMENDOUS ATTEMPT",                       "try"},
    {"WE'LL SEE WHAT HAPPENS",                   "try"},
    {"LET'S GIVE IT A SHOT",                     "try"},
    {"VERY LEGAL VERY COOL",                     "try"},
    {"WATCH THIS",                               "try"},

    /* except */
    {"IF THE DEEP STATE INTERFERES",             "except"},
    {"WHEN THINGS GO SOUTH",                     "except"},
    {"IF SOMETHING GOES WRONG",                  "except"},
    {"IN CASE OF DISASTER",                      "except"},
    {"COVFEFE",                                  "except"},

    /* finally */
    {"BELIEVE ME IT ALWAYS HAPPENS",             "finally"},
    {"AND THAT'S FINAL",                         "finally"},
    {"NO MATTER WHAT",                           "finally"},
    {"MARK MY WORDS",                            "finally"},
    {"AT THE END OF THE DAY",                    "finally"},

    /* raise */
    {"THIS IS AN OUTRAGE",                       "raise"},
    {"TOTAL DISGRACE",                           "raise"},
    {"YOU'RE FIRED",                             "raise"},
    {"UNACCEPTABLE",                             "raise"},
    {"GET OUT",                                  "raise"},

    /* with */
    {"TREMENDOUS PARTNERSHIP WITH",              "with"},
    {"WORKING TOGETHER WITH",                    "with"},
    {"SIDE BY SIDE WITH",                        "with"},
    {"IN CAHOOTS WITH",                          "with"},
    {"ALONGSIDE",                                "with"},

    /* yield */
    {"HERE'S ONE FOR YOU",                       "yield"},
    {"HERE IT COMES",                            "yield"},
    {"GIVING YOU",                               "yield"},
    {"TAKE THIS ONE",                            "yield"},
    {"RELEASING",                                "yield"},

    /* lambda */
    {"SMALL BEAUTIFUL FUNCTION",                 "lambda"},
    {"FAST AND FURIOUS",                         "lambda"},
    {"QUICK AND DIRTY",                          "lambda"},
    {"A LITTLE SOMETHING",                       "lambda"},
    {"ON THE FLY",                               "lambda"},

    /* global */
    {"FOR ALL OF AMERICA",                       "global"},
    {"ACROSS THE NATION",                        "global"},
    {"FEDERAL LEVEL",                            "global"},
    {"NATIONWIDE",                               "global"},
    {"EVERYONE KNOWS",                           "global"},

    /* nonlocal */
    {"FROM THE STATE LEVEL",                     "nonlocal"},
    {"LOCAL JURISDICTION",                       "nonlocal"},
    {"STATE RIGHTS",                             "nonlocal"},
    {"NEARBY SCOPE",                             "nonlocal"},

    /* del */
    {"GONE, DELETED, DESTROYED",                 "del"},
    {"PERMANENTLY REMOVED",                      "del"},
    {"BLEACHBIT",                                "del"},
    {"HILLARY STYLE",                            "del"},
    {"NUKE IT",                                  "del"},

    /* assert */
    {"THIS I CAN PROMISE",                       "assert"},
    {"TRUST ME ON THIS",                         "assert"},
    {"I GUARANTEE",                              "assert"},
    {"I SWEAR TO YOU",                           "assert"},
    {"BELIEVE ME",                               "assert"},

    /* async */
    {"AT THE SAME TIME",                         "async"},
    {"BIGLY CONCURRENT",                         "async"},
    {"SIMULTANEOUSLY",                           "async"},
    {"MEANWHILE",                                "async"},
    {"RUNNING IN PARALLEL",                      "async"},

    /* await */
    {"WE'RE WAITING ON",                         "await"},
    {"STAND BY",                                 "await"},
    {"WAIT FOR IT",                              "await"},
    {"PATIENCE",                                 "await"},
    {"HOLD ON",                                  "await"},

    /* not */
    {"TOTALLY FALSE",                            "not"},
    {"WITCH HUNT",                               "not"},
    {"NOT TRUE",                                 "not"},
    {"WRONG",                                    "not"},
    {"FAKE",                                     "not"},

    /* and */
    {"COMBINED WITH",                            "and"},
    {"TOGETHER WITH",                            "and"},
    {"AND ALSO",                                 "and"},
    {"PLUS ALSO",                                "and"},

    /* or */
    {"COULD ALSO BE",                            "or"},
    {"ALTERNATIVELY",                            "or"},
    {"OR MAYBE",                                 "or"},
    {"POSSIBLY",                                 "or"},

    /* True */
    {"ONE HUNDRED PERCENT",                      "True"},
    {"WITHOUT QUESTION",                         "True"},
    {"TOTALLY TRUE",                             "True"},
    {"ABSOLUTELY",                               "True"},
    {"PERFECT",                                  "True"},

    /* False */
    {"COMPLETELY WRONG",                         "False"},
    {"TOTALLY FALSE",                            "False"},
    {"WITCH HUNT",                               "False"},
    {"FAKE NEWS",                                "False"},
    {"RIGGED",                                   "False"},

    /* None */
    {"EMPTY LIKE BIDEN",                         "None"},
    {"NOTHING THERE",                            "None"},
    {"ZERO SUBSTANCE",                           "None"},
    {"DOESN'T EXIST",                            "None"},
    {"VOID",                                     "None"},

    /* == */
    {"IS IDENTICAL TO",                          "=="},
    {"IS THE SAME AS",                           "=="},
    {"MATCHES",                                  "=="},
    {"EQUALS",                                   "=="},

    /* != */
    {"IS TOTALLY DIFFERENT FROM",                "!="},
    {"IS NOT THE SAME AS",                       "!="},
    {"DOESN'T MATCH",                            "!="},
    {"IS FAKE COMPARED TO",                      "!="},

    /* > */
    {"IS GREATER THAN",                          ">"},
    {"IS BIGGER THAN",                           ">"},
    {"DOMINATES",                                ">"},
    {"CRUSHES",                                  ">"},
    {"BEATS",                                    ">"},

    /* < */
    {"IS LESS THAN",                             "<"},
    {"IS SMALLER THAN",                          "<"},
    {"IS WEAKER THAN",                           "<"},
    {"IS BEHIND",                                "<"},
    {"LOSES TO",                                 "<"},

    /* >= */
    {"IS BIGGER THAN OR MATCHES",                ">="},
    {"IS AT LEAST AS GREAT AS",                  ">="},
    {"IS GREATER THAN OR EQUAL TO",              ">="},

    /* <= */
    {"IS SMALLER THAN OR MATCHES",               "<="},
    {"IS LESS THAN OR EQUAL TO",                 "<="},
    {"IS AT MOST",                               "<="},

    /* colon — BIGLY closes a block header line: "LET ME TELL YOU foo(x) BIGLY" */
    {"BIGLY",                                    ":"},

    /* print (builtin — maps to print function name) */
    {"EVERYBODY NEEDS TO KNOW",                  "print"},
    {"YOU WON'T BELIEVE THIS",                   "print"},
    {"FAKE NEWS SAYS",                           "print"},
    {"I'M TELLING YOU",                          "print"},
    {"I SAID IT FIRST",                          "print"},
    {"LOOK, FOLKS",                              "print"},
    {"SADLY",                                    "print"},

    /* input */
    {"WHAT'S YOUR ANSWER",                       "input"},
    {"THE AUDIENCE SAYS",                        "input"},
    {"ASK THE PEOPLE",                           "input"},
    {"TAKE A POLL",                              "input"},
    {"WHAT DO YOU SAY",                          "input"},

    /* len */
    {"HOW BIG IS",                               "len"},
    {"COUNT THE CROWD",                          "len"},
    {"COUNT OF",                                 "len"},
    {"HOW MANY",                                 "len"},
    {"THE SIZE OF",                              "len"},

    /* range */
    {"ALL THE WAY FROM",                         "range"},
    {"THE NUMBERS FROM",                         "range"},
    {"NUMBERS BETWEEN",                          "range"},
    {"COUNT FROM",                               "range"},
    {"STARTING AT",                              "range"},

    /* type */
    {"WHAT KIND OF",                             "type"},
    {"WHAT IS",                                  "type"},
    {"IDENTIFY",                                 "type"},
    {"CLASSIFY",                                 "type"},

    /* str */
    {"SAY IT LOUD",                              "str"},
    {"IN WORDS",                                 "str"},
    {"SPEAK IT",                                 "str"},
    {"AS TEXT",                                  "str"},
    {"VERBALLY",                                 "str"},

    /* int */
    {"MAKE IT A NUMBER",                         "int"},
    {"AS A NUMBER",                              "int"},
    {"THE NUMBER",                               "int"},
    {"WHOLE NUMBER",                             "int"},

    /* float */
    {"PRECISE NUMBER",                           "float"},
    {"WITH DECIMALS",                            "float"},
    {"THE EXACT AMOUNT",                         "float"},
    {"DECIMAL NUMBER",                           "float"},

    /* bool */
    {"BOOLEAN ANSWER",                           "bool"},
    {"IS IT REAL",                               "bool"},
    {"TRUE OR FAKE",                             "bool"},
    {"YES OR NO",                                "bool"},

    /* list */
    {"TREMENDOUS ARRAY",                         "list"},
    {"THE BEST LIST",                            "list"},
    {"MY LIST OF",                               "list"},

    /* dict */
    {"THE SECRET FILES",                         "dict"},
    {"KEY AND VALUE",                            "dict"},
    {"THE DOSSIER",                              "dict"},
    {"LOOKUP TABLE",                             "dict"},

    /* tuple */
    {"UNCHANGEABLE",                             "tuple"},
    {"SET IN STONE",                             "tuple"},
    {"LOCKED IN",                                "tuple"},
    {"FIXED FOREVER",                            "tuple"},

    /* set */
    {"UNIQUE CROWD",                             "set"},
    {"NO DUPLICATES",                            "set"},
    {"DISTINCT MEMBERS",                         "set"},
    {"ONE OF EACH",                              "set"},

    /* max */
    {"GREATEST OF",                              "max"},
    {"THE WINNER",                               "max"},
    {"BIGGEST OF",                               "max"},
    {"THE BEST OF",                              "max"},

    /* min */
    {"THE LOSER",                                "min"},
    {"WEAKEST OF",                               "min"},
    {"SMALLEST OF",                              "min"},
    {"THE WORST OF",                             "min"},

    /* sum */
    {"ADD THEM ALL UP",                          "sum"},
    {"THE GRAND TOTAL",                          "sum"},
    {"ALL COMBINED",                             "sum"},
    {"TOTAL OF",                                 "sum"},

    /* sorted */
    {"ORGANIZED BEAUTIFULLY",                    "sorted"},
    {"SORTED LIKE A WINNER",                     "sorted"},
    {"PUT IN ORDER",                             "sorted"},
    {"RANKED",                                   "sorted"},

    /* reversed */
    {"THE OTHER WAY",                            "reversed"},
    {"IN REVERSE",                               "reversed"},
    {"BACKWARDS",                                "reversed"},
    {"FLIPPED",                                  "reversed"},

    /* enumerate */
    {"ONE BY ONE NUMBERED",                      "enumerate"},
    {"NUMBERED LIST",                            "enumerate"},
    {"INDEX AND VALUE",                          "enumerate"},
    {"WITH NUMBERS",                             "enumerate"},

    /* zip */
    {"MATCHED TOGETHER",                         "zip"},
    {"SIDE BY SIDE",                             "zip"},
    {"PAIRED UP",                                "zip"},
    {"COUPLED WITH",                             "zip"},

    /* map */
    {"DO THIS TO ALL OF",                        "map"},
    {"TRANSFORM EVERY",                          "map"},
    {"APPLY TO EACH",                            "map"},
    {"MAKE EACH ONE",                            "map"},

    /* filter */
    {"KEEP THE WINNERS",                         "filter"},
    {"REMOVE THE LOSERS",                        "filter"},
    {"ONLY THE GOOD ONES",                       "filter"},
    {"ONLY WHERE",                               "filter"},

    /* open */
    {"OPEN THE BEAUTIFUL FILE",                  "open"},
    {"UNLOCK THE FILE",                          "open"},
    {"ACCESS THE RECORDS",                       "open"},
    {"GET THE FILE",                             "open"},

    /* isinstance */
    {"IS IT A KIND OF",                          "isinstance"},
    {"CHECK THE TYPE OF",                        "isinstance"},
    {"IS THIS A",                                "isinstance"},

    /* hasattr */
    {"CHECK IF IT HAS",                          "hasattr"},
    {"DOES IT HAVE",                             "hasattr"},
    {"DOES THIS HAVE",                           "hasattr"},

    /* getattr */
    {"TAKE FROM IT",                             "getattr"},
    {"GRAB FROM",                                "getattr"},
    {"GET FROM IT",                              "getattr"},

    /* setattr */
    {"ASSIGN TO IT",                             "setattr"},
    {"SET ON IT",                                "setattr"},
    {"PUT ON IT",                                "setattr"},

    /* super */
    {"THE ORIGINAL",                             "super"},
    {"MY PREDECESSOR",                           "super"},
    {"INHERITED FROM",                           "super"},

    /* self (contextual — maps literally) */
    {"THIS TREMENDOUS INSTANCE",                 "self"},
    {"ME, THE BEST",                             "self"},

    /* Fatal kill switch */
    {"EPSTEIN LIST",                             "raise SystemExit(1138)"},

    /* Sentinel */
    {NULL, NULL}
};


/* ── Helper: are we inside a string literal? ───────────────────────────── */

static int
skip_string(const char *src, size_t i, size_t len, size_t *out_end)
{
    /* Handles "", '', """""", '''''' */
    char q = src[i];
    if (q != '"' && q != '\'') return 0;

    size_t start = i;
    i++;

    /* Check for triple quote */
    if (i + 1 < len && src[i] == q && src[i+1] == q) {
        i += 2;
        /* Scan for closing triple quote */
        while (i + 2 < len) {
            if (src[i] == '\\') { i += 2; continue; }
            if (src[i] == q && src[i+1] == q && src[i+2] == q) {
                *out_end = i + 3;
                return 1;
            }
            i++;
        }
        *out_end = len; /* unclosed — hand off to parser */
        return 1;
    }

    /* Single-quoted string */
    while (i < len) {
        if (src[i] == '\\') { i += 2; continue; }
        if (src[i] == q) { *out_end = i + 1; return 1; }
        if (src[i] == '\n') break; /* unclosed single-line string */
        i++;
    }
    *out_end = i;
    return 1;
}


/* ── Main pre-processor ─────────────────────────────────────────────────── */

char *
_Trump_PreprocessSource(const char *src)
{
    size_t src_len = strlen(src);

    /*
     * Every Trump phrase is longer than its Python equivalent, so the
     * output is always <= input in size. One extra byte for NUL.
     */
    char *out = (char *)PyMem_RawMalloc(src_len + 1);
    if (out == NULL) return NULL;

    size_t i = 0;
    size_t o = 0;

    while (i < src_len) {
        /* Pass string literals through unchanged */
        if (src[i] == '"' || src[i] == '\'') {
            size_t str_end;
            if (skip_string(src, i, src_len, &str_end)) {
                while (i < str_end) out[o++] = src[i++];
                continue;
            }
        }

        /* Pass comments through unchanged */
        if (src[i] == '#') {
            while (i < src_len && src[i] != '\n') out[o++] = src[i++];
            continue;
        }

        /* Try to match a Trump phrase (table is longest-first per group) */
        int matched = 0;
        for (int p = 0; _trump_phrases[p].phrase != NULL; p++) {
            const char *phrase   = _trump_phrases[p].phrase;
            const char *keyword  = _trump_phrases[p].keyword;
            size_t       plen    = strlen(phrase);

            if (i + plen > src_len) continue;
            if (strncmp(src + i, phrase, plen) != 0) continue;

            /* Require a word boundary after the phrase:
               next char must be whitespace, punctuation, or end of source */
            size_t next = i + plen;
            if (next < src_len) {
                char nc = src[next];
                if ((nc >= 'A' && nc <= 'Z') ||
                    (nc >= 'a' && nc <= 'z') ||
                    (nc >= '0' && nc <= '9') ||
                    nc == '_' || nc == '\'' ) continue; /* prefix of longer word */
            }

            size_t klen = strlen(keyword);
            memcpy(out + o, keyword, klen);
            o += klen;
            i += plen;
            matched = 1;
            break;
        }

        if (!matched) {
            out[o++] = src[i++];
        }
    }

    out[o] = '\0';
    return out;
}


/* ── Filename detector ──────────────────────────────────────────────────── */

int
_Trump_IsTrumpFile(PyObject *filename)
{
    if (filename == NULL || !PyUnicode_Check(filename)) return 0;
    Py_ssize_t len;
    const char *fname = PyUnicode_AsUTF8AndSize(filename, &len);
    if (fname == NULL) return 0;
    return len >= 6 && strcmp(fname + len - 6, ".trump") == 0;
}
