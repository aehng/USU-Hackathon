"""
Python translation of the VoiceHealth JSON validator + CLI.

This mirrors the behavior of the C validator in validate_voicehealth_json.c:
- Required keys: symptoms (array), severity (1–10), potential_triggers (array)
- Automatically sanitizes data (fixes 0 to 1, null to [])
- Returns a boolean + error message string in Python
- CLI mode compatible with the C validate_cli:
    * Reads JSON from stdin
    * Prints "1" / "0" to stdout
    * Writes specific error message to stderr when invalid
    * Exit codes: 0 = valid, 1 = invalid, 2 = runtime/usage error
"""

from __future__ import annotations

import json
import sys
from typing import Optional, Tuple

# Changed minimum to 1 to match the database check constraint!
SEVERITY_MIN = 1
SEVERITY_MAX = 10

def sanitize_voicehealth_data(data: dict) -> dict:
    """
    Cleans the LLM output to ensure database compatibility.
    Converts 0 to 1, caps at 10, handles arrays, and truncates long strings.
    """
    if not isinstance(data, dict):
        return data

    # 1. Ensure array fields are actually lists
    for array_field in ["symptoms", "potential_triggers", "body_location"]:
        val = data.get(array_field)
        if val is None:
            data[array_field] = []
        elif isinstance(val, str):
            data[array_field] = [val] # Wrap single strings in a list
        elif not isinstance(val, list):
            data[array_field] = []
            
    # 2. Fix severity (default to 1, convert < 1 to 1, cap at 10)
    severity = data.get("severity")
    if not isinstance(severity, (int, float)):
        data["severity"] = SEVERITY_MIN
    elif severity < SEVERITY_MIN:
        data["severity"] = SEVERITY_MIN
    elif severity > SEVERITY_MAX:
        data["severity"] = SEVERITY_MAX
        
    # 3. Enforce VARCHAR limits to prevent Postgres crashes
    if isinstance(data.get("mood"), str):
        data["mood"] = data["mood"][:50] # Truncate to 50 chars
        
    if isinstance(data.get("time_context"), str):
        data["time_context"] = data["time_context"][:100] # Truncate to 100 chars
        
    return data

def validate_voicehealth_json_py(json_string: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that json_string is a JSON object with:
      - symptoms: array
      - severity: number in [1, 10]
      - potential_triggers: array

    Returns (is_valid, error_message_or_None).
    Error messages intentionally match the C implementation.
    """
    if json_string is None:
        return False, "Input string is null"

    try:
        obj = json.loads(json_string)
    except json.JSONDecodeError:
        return False, "Malformed JSON"

    if not isinstance(obj, dict):
        return False, "Root must be a JSON object"

    # Clean the data before we validate it!
    obj = sanitize_voicehealth_data(obj)

    symptoms = obj.get("symptoms")
    if not isinstance(symptoms, list):
        return False, "Missing or invalid 'symptoms' (must be array)"

    severity = obj.get("severity")
    if not isinstance(severity, (int, float)):
        return False, "Missing or invalid 'severity' (must be number)"

    if severity < SEVERITY_MIN or severity > SEVERITY_MAX:
        return False, f"Severity must be between {SEVERITY_MIN} and {SEVERITY_MAX}"

    potential_triggers = obj.get("potential_triggers")
    if not isinstance(potential_triggers, list):
        return False, "Missing or invalid 'potential_triggers' (must be array)"

    return True, None


def main() -> int:
    """
    CLI entrypoint, mirroring validate_cli.c:
      - Read JSON from stdin
      - Print "1" on valid, "0" on invalid
      - Print error message to stderr when invalid
    """
    data = sys.stdin.read()
    if data is None or data == "":
        print("0")
        print("No input provided on stdin", file=sys.stderr)
        return 2

    ok, err = validate_voicehealth_json_py(data)
    if ok:
        print("1")
        return 0

    print("0")
    if err:
        print(err, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())