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
   make
   ```

3. Run the test program (optional):
   ```bash
   ./validate_test
   ```

## CLI wrapper (for Python `subprocess`)

The `validate_cli` executable reads the JSON string from **stdin**.

- **stdout**: `1` if valid, `0` if invalid  
- **stderr**: specific error message when invalid  
- **exit code**: `0` valid, `1` invalid, `2` runtime/usage error

Example:
```bash
echo '{"symptoms":[],"severity":5,"potential_triggers":[]}' | ./validate_cli
```

Python example (note: `subprocess` is the module you want, not `os`):

```python
import subprocess

json_str = '{"symptoms":["headache"],"severity":7,"potential_triggers":["caffeine"]}'

proc = subprocess.run(
    ["./validate_cli"],
    input=json_str,
    text=True,
    capture_output=True,
)

is_valid = (proc.returncode == 0) and (proc.stdout.strip() == "1")
error_message = proc.stderr.strip()
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
