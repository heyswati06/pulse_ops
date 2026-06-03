"""
parser.py
─────────
Extracts structured info from a raw CI failure log.
Tells the agent WHAT failed and WHAT TYPE of failure it is.
"""

import re


def parse_failure_log(log_text: str, job_name: str = "") -> dict:
    """
    Parse raw failure log into structured dict.

    Returns:
    {
        "error_type":  "cyberflow_scan",
        "severity":    "HIGH",
        "error_text":  "The most relevant error lines",
        "component":   "log4j-2.14.0",   (if found)
        "cve":         "CVE-2021-44228",  (if found)
        "job_name":    "cyberflow-scan-job"
    }
    """
    log_lower = log_text.lower()
    result = {
        "error_type":  "build_failure",
        "severity":    "MEDIUM",
        "error_text":  extract_error_lines(log_text),
        "component":   extract_component(log_text),
        "cve":         extract_cve(log_text),
        "job_name":    job_name,
    }

    # Classify error type
    if "cyberflow" in log_lower or "security scan failed" in log_lower:
        result["error_type"] = "cyberflow_scan"
        result["severity"]   = "HIGH"

    elif "foss" in log_lower or "vulnerability" in log_lower or "cve-" in log_lower:
        result["error_type"] = "foss_vulnerability"
        result["severity"]   = "HIGH"

    elif "could not resolve" in log_lower or "nexus" in log_lower:
        result["error_type"] = "nexus_dependency"
        result["severity"]   = "MEDIUM"

    elif "docker" in log_lower or "container" in log_lower:
        result["error_type"] = "docker_build"
        result["severity"]   = "MEDIUM"

    elif "out of memory" in log_lower or "heap" in log_lower:
        result["error_type"] = "build_failure"
        result["severity"]   = "HIGH"

    return result


def extract_error_lines(log_text: str, max_lines: int = 20) -> str:
    """Pull the most relevant error lines from the log."""
    lines = log_text.splitlines()

    # Lines containing error keywords — these are the useful ones
    keywords = ["error", "failed", "exception", "critical", "high", "cve-",
                "could not", "unable to", "denied", "timeout", "killed"]

    error_lines = [
        line for line in lines
        if any(kw in line.lower() for kw in keywords)
    ]

    # If no keyword matches, just take the last lines (errors are at the end)
    if not error_lines:
        error_lines = lines[-max_lines:]

    return "\n".join(error_lines[:max_lines])


def extract_component(log_text: str) -> str:
    """Try to extract the component/artifact name from the log."""
    # Match patterns like: log4j-2.14.0, spring-boot-3.1.0
    match = re.search(r"([a-z][\w-]+)-(\d+\.\d+[\.\d]*)", log_text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return ""


def extract_cve(log_text: str) -> str:
    """Extract CVE ID if present."""
    match = re.search(r"CVE-\d{4}-\d+", log_text, re.IGNORECASE)
    return match.group(0).upper() if match else ""
