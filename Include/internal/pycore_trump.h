#ifndef Py_INTERNAL_TRUMP_H
#define Py_INTERNAL_TRUMP_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * TrumpLang pre-processor.
 * Substitutes Trump phrases with Python keywords in .trump source files.
 * Called by pyrun_file() before the source reaches the parser.
 *
 * Returns a newly heap-allocated string. Caller must free() it.
 * Returns NULL on allocation failure.
 */
extern char *_Trump_PreprocessSource(const char *src);

/*
 * Returns 1 if the given PyUnicode filename ends in ".trump", else 0.
 */
extern int _Trump_IsTrumpFile(PyObject *filename);

#ifdef __cplusplus
}
#endif

#endif /* Py_INTERNAL_TRUMP_H */
