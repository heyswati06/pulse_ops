"""
response_parser.py
──────────────────
Parses the structured LLM response into a Python dict.
"""

import re


def parse_llm_response(raw_response: str) -> dict:
    """
    Parse the LLM's structured response.

    Expected format from LLM:
        SUMMARY: ...
        STEPS:
        1. ...
        2. ...
        FILES_TO_CHANGE: pom.xml, Dockerfile
        CONFIDENCE: HIGH
    """
    result = {
        "summary":          "",
        "steps":            [],
        "files_to_change":  [],
        "confidence":       "MEDIUM",
        "raw":              raw_response,
    }

    lines = raw_response.strip().splitlines()
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("SUMMARY:"):
            result["summary"] = line.split(":", 1)[1].strip()
            current_section = "summary"

        elif line.upper().startswith("STEPS:"):
            current_section = "steps"

        elif line.upper().startswith("FILES_TO_CHANGE:"):
            files_raw = line.split(":", 1)[1].strip()
            if files_raw.upper() != "NONE":
                result["files_to_change"] = [f.strip() for f in files_raw.split(",")]
            current_section = None

        elif line.upper().startswith("CONFIDENCE:"):
            result["confidence"] = line.split(":", 1)[1].strip().upper()
            current_section = None

        elif current_section == "steps":
            # Numbered steps: "1. Do this"
            step_match = re.match(r"^\d+\.\s+(.+)", line)
            if step_match:
                result["steps"].append(step_match.group(1))

    return result
