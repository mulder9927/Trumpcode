/* Return the copyright string.  This is updated manually. */

#include "Python.h"

static const char cprt[] =
"\
TrumpLang -- Making Code Great Again.\n\
All Rights Reserved. Very strongly reserved.\n\
\n\
Built on a tremendous foundation. The best foundation.\n\
Nobody builds foundations like this. Nobody.\n\
\n\
TrumpLang is a product of winning. Tremendous winning.\n\
If you are reading this, you are a winner too.";

const char *
Py_GetCopyright(void)
{
    return cprt;
}
