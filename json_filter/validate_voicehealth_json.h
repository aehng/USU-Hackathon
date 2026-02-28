/**
 * VoiceHealth JSON validator — checks for required keys before DB write.
 * Requires cJSON: https://github.com/DaveGamble/cJSON
 *
 * Compile with: gcc -o validate validate_voicehealth_json.c cJSON.c -I.
 */

#ifndef VALIDATE_VOICEHEALTH_JSON_H
#define VALIDATE_VOICEHEALTH_JSON_H

#include <stddef.h>

/**
 * Validates that the input string is valid JSON and contains:
 *   - symptoms (array)
 *   - severity (number in 0–10 range)
 *   - potential_triggers (array)
 *
 * Returns 1 if valid, 0 if invalid.
 *
 * If invalid and error_msg is non-NULL and error_size > 0, copies a specific
 * error message into error_msg (always null-terminated). Example messages:
 *   "Malformed JSON"
 *   "Severity must be between 0 and 10"
 *   "Missing or invalid 'symptoms' (must be array)"
 *   etc.
 *
 * Caller retains ownership of json_string; it is not modified.
 */
int validate_voicehealth_json(const char *json_string, char *error_msg, size_t error_size);

#endif /* VALIDATE_VOICEHEALTH_JSON_H */
