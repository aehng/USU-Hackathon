"""
Python translation of the VoiceHealth JSON validator + CLI.

This mirrors the behavior of the C validator in validate_voicehealth_json.c:
- Required keys: symptoms (array), severity (0–10), potential_triggers (array)
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


SEVERITY_MIN = 0
SEVERITY_MAX = 10


def validate_voicehealth_json_py(json_string: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that json_string is a JSON object with:
      - symptoms: array
      - severity: number in [0, 10]
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

    symptoms = obj.get("symptoms")
    if not isinstance(symptoms, list):
        return False, "Missing or invalid 'symptoms' (must be array)"

    severity = obj.get("severity")
    if not isinstance(severity, (int, float)):
        return False, "Missing or invalid 'severity' (must be number)"

    if severity < SEVERITY_MIN or severity > SEVERITY_MAX:
        return False, "Severity must be between 0 and 10"

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

