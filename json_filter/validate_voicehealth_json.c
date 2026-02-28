/**
 * VoiceHealth JSON validator — required keys: symptoms (array), severity (0–10), potential_triggers (array).
 * Add cJSON.c and cJSON.h from https://github.com/DaveGamble/cJSON to this directory, then:
 *   gcc -o validate validate_voicehealth_json.c cJSON.c -I.
 */

#include "validate_voicehealth_json.h"
#include "cJSON.h"
#include <stddef.h>
#include <stdio.h>

#define SEVERITY_MIN 0
#define SEVERITY_MAX 10

static void set_error(char *error_msg, size_t error_size, const char *msg)
{
    if (error_msg != NULL && error_size > 0)
        snprintf(error_msg, error_size, "%s", msg);
}

int validate_voicehealth_json(const char *json_string, char *error_msg, size_t error_size)
{
    if (json_string == NULL)
    {
        set_error(error_msg, error_size, "Input string is null");
        return 0;
    }

    cJSON *root = cJSON_Parse(json_string);
    if (root == NULL)
    {
        set_error(error_msg, error_size, "Malformed JSON");
        return 0;
    }

    if (!cJSON_IsObject(root))
    {
        cJSON_Delete(root);
        set_error(error_msg, error_size, "Root must be a JSON object");
        return 0;
    }

    cJSON *symptoms = cJSON_GetObjectItemCaseSensitive(root, "symptoms");
    if (symptoms == NULL || !cJSON_IsArray(symptoms))
    {
        cJSON_Delete(root);
        set_error(error_msg, error_size, "Missing or invalid 'symptoms' (must be array)");
        return 0;
    }

    cJSON *severity_item = cJSON_GetObjectItemCaseSensitive(root, "severity");
    if (severity_item == NULL || !cJSON_IsNumber(severity_item))
    {
        cJSON_Delete(root);
        set_error(error_msg, error_size, "Missing or invalid 'severity' (must be number)");
        return 0;
    }

    double s = severity_item->valuedouble;
    if (s < SEVERITY_MIN || s > SEVERITY_MAX)
    {
        cJSON_Delete(root);
        set_error(error_msg, error_size, "Severity must be between 0 and 10");
        return 0;
    }

    cJSON *potential_triggers = cJSON_GetObjectItemCaseSensitive(root, "potential_triggers");
    if (potential_triggers == NULL || !cJSON_IsArray(potential_triggers))
    {
        cJSON_Delete(root);
        set_error(error_msg, error_size, "Missing or invalid 'potential_triggers' (must be array)");
        return 0;
    }

    cJSON_Delete(root);
    return 1;
}
