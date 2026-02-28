# VoiceHealth JSON validator (C)

Validates that a string is valid JSON and contains the required keys:
- **symptoms** (array)
- **severity** (number in **0–10** range)
- **potential_triggers** (array)

Returns `1` if valid, `0` if invalid. When invalid, an optional buffer can receive a specific error message.

**Error messages:**
- `"Malformed JSON"` — parse failed
- `"Root must be a JSON object"`
- `"Missing or invalid 'symptoms' (must be array)"`
- `"Missing or invalid 'severity' (must be number)"`
- `"Severity must be between 0 and 10"` — value &lt; 0 or &gt; 10
- `"Missing or invalid 'potential_triggers' (must be array)"`

## Setup

1. Download **cJSON** (single-file use):
   - [cJSON.h](https://raw.githubusercontent.com/DaveGamble/cJSON/master/cJSON.h)
   - [cJSON.c](https://raw.githubusercontent.com/DaveGamble/cJSON/master/cJSON.c)
   - Place both in this `json_filter` directory.

2. Build:
   ```bash
   gcc -o validate validate_voicehealth_json.c cJSON.c -I.
   ```

3. Run the test program (optional):
   ```bash
   gcc -o validate_test validate_voicehealth_json.c test_validate.c cJSON.c -I.
   ./validate_test
   ```

## Usage

```c
#include "validate_voicehealth_json.h"

char err[128];
const char *json = "{\"symptoms\":[\"headache\"],\"severity\":7,\"potential_triggers\":[\"caffeine\"]}";

if (validate_voicehealth_json(json, err, sizeof(err)))
    /* valid — safe to pass to DB */;
else
    /* invalid — err now holds e.g. "Malformed JSON" or "Severity must be between 0 and 10" */
    fprintf(stderr, "%s\n", err);
```

Pass `NULL, 0` for the last two arguments if you don't need the error message.
