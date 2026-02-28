/**
 * CLI wrapper for validate_voicehealth_json().
 *
 * Usage (recommended): echo '{"symptoms":[],"severity":5,"potential_triggers":[]}' | ./validate_cli
 *
 * Output:
 *   stdout: "1\n" if valid, "0\n" if invalid
 *   stderr: error message when invalid
 *
 * Exit codes:
 *   0 = valid
 *   1 = invalid
 *   2 = runtime/usage error
 */

#include "validate_voicehealth_json.h"
#include <stdio.h>
#include <stdlib.h>

static char *read_all_stdin(size_t *out_len)
{
    size_t cap = 4096;
    size_t len = 0;
    char *buf = (char *)malloc(cap);
    if (!buf)
        return NULL;

    for (;;)
    {
        size_t space = cap - len;
        if (space < 2048)
        {
            size_t new_cap = cap * 2;
            char *new_buf = (char *)realloc(buf, new_cap);
            if (!new_buf)
            {
                free(buf);
                return NULL;
            }
            buf = new_buf;
            cap = new_cap;
            space = cap - len;
        }

        size_t n = fread(buf + len, 1, space, stdin);
        len += n;

        if (n == 0)
            break;
    }

    /* Ensure null-terminated */
    if (len + 1 > cap)
    {
        char *new_buf = (char *)realloc(buf, len + 1);
        if (!new_buf)
        {
            free(buf);
            return NULL;
        }
        buf = new_buf;
    }
    buf[len] = '\0';

    if (out_len)
        *out_len = len;
    return buf;
}

int main(void)
{
    size_t len = 0;
    char *json = read_all_stdin(&len);
    if (!json)
    {
        fprintf(stderr, "Failed to read stdin\n");
        return 2;
    }

    if (len == 0)
    {
        fprintf(stderr, "No input provided on stdin\n");
        free(json);
        return 2;
    }

    char err[256];
    err[0] = '\0';

    int ok = validate_voicehealth_json(json, err, sizeof(err));
    if (ok)
    {
        fputs("1\n", stdout);
        free(json);
        return 0;
    }

    fputs("0\n", stdout);
    if (err[0] != '\0')
        fprintf(stderr, "%s\n", err);

    free(json);
    return 1;
}

