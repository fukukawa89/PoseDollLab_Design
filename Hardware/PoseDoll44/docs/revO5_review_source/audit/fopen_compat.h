/* Host-only portability shim. Does not alter the PDR4 implementation or test. */
#include <stdio.h>
#include <errno.h>
static inline int fopen_s(FILE **stream, const char *path, const char *mode) {
    if (!stream) return EINVAL;
    *stream = fopen(path, mode);
    return *stream ? 0 : (errno ? errno : EIO);
}
