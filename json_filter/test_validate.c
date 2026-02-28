/**
 * Quick test for validate_voicehealth_json. Compile with:
 *   gcc -o validate_test validate_voicehealth_json.c test_validate.c cJSON.c -I.
 */

#include "validate_voicehealth_json.h"
#include <stdio.h>

#define BUF_SIZE 128

int main(void)
{
    char err[BUF_SIZE];
    const char *valid = "{\"symptoms\":[\"headache\"],\"severity\":7,\"potential_triggers\":[\"caffeine\"]}";
    const char *missing_severity = "{\"symptoms\":[],\"potential_triggers\":[]}";
    const char *wrong_type = "{\"symptoms\":\"not-array\",\"severity\":5,\"potential_triggers\":[]}";
    const char *bad_json = "{ invalid json }";
    const char *severity_high = "{\"symptoms\":[\"pain\"],\"severity\":11,\"potential_triggers\":[]}";
    const char *severity_neg = "{\"symptoms\":[],\"severity\":-1,\"potential_triggers\":[]}";

    printf("Valid JSON:           %s (expect 1)\n", validate_voicehealth_json(valid, err, BUF_SIZE) ? "PASS" : "FAIL");

    err[0] = '\0';
    printf("Missing severity:     %s (expect 0)\n", !validate_voicehealth_json(missing_severity, err, BUF_SIZE) ? "PASS" : "FAIL");
    if (err[0]) printf("  -> %s\n", err);

    err[0] = '\0';
    printf("Wrong type symptoms:  %s (expect 0)\n", !validate_voicehealth_json(wrong_type, err, BUF_SIZE) ? "PASS" : "FAIL");
    if (err[0]) printf("  -> %s\n", err);

    err[0] = '\0';
    printf("Bad JSON:             %s (expect 0)\n", !validate_voicehealth_json(bad_json, err, BUF_SIZE) ? "PASS" : "FAIL");
    if (err[0]) printf("  -> %s\n", err);

    err[0] = '\0';
    printf("Severity > 10:        %s (expect 0)\n", !validate_voicehealth_json(severity_high, err, BUF_SIZE) ? "PASS" : "FAIL");
    if (err[0]) printf("  -> %s\n", err);

    err[0] = '\0';
    printf("Severity < 0:         %s (expect 0)\n", !validate_voicehealth_json(severity_neg, err, BUF_SIZE) ? "PASS" : "FAIL");
    if (err[0]) printf("  -> %s\n", err);

    return 0;
}
