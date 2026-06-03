"""
ingest_cyberflow.py
───────────────────
Parses Cyberflow scan reports.
Filters HIGH and CRITICAL severity only.
Stores structured findings to MongoDB KB.

Owner: [ASSIGNED_TO] — Joel should help identify report format and location

HOW CYBERFLOW REPORTS USUALLY WORK:
    After a Cyberflow scan job runs in Jenkins, it produces a report.
    Common formats: JSON file in workspace, HTML report, or API endpoint.

    Ask Joel: "Where does the Cyberflow scan report file go after the job runs?
    Can you export a sample JSON/XML report from a past scan?"

    For now this script handles TWO scenarios:
    1. JSON report file (most common)
    2. Plain text log from Jenkins console (fallback)

HOW TO RUN:
    # Option A — with a real JSON report file
    python ingestion/ingest_cyberflow.py --file path/to/scan_report.json

    # Option B — from a saved Jenkins console log
    python ingestion/ingest_cyberflow.py --log path/to/console.txt

    # With no args — uses sample file for testing
    python ingestion/ingest_cyberflow.py
"""

import json
import re
import argparse

from knowledge_base.schema import make_kb_document
from knowledge_base.store import insert_many, clear_source
from knowledge_base.chunker import clean_text

# Only ingest these severity levels — MEDIUM is noise for a demo
SEVERITY_TO_INGEST = ["HIGH", "CRITICAL"]


def parse_json_report(filepath: str) -> list:
    """
    Parse a Cyberflow JSON scan report.
    Returns list of findings dicts.

    NOTE: Cyberflow JSON structure varies by version.
    Joel — adjust the field names below to match your actual report format.
    Run: print(json.dumps(data, indent=2)) to see your structure.
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    findings = []

    # Common Cyberflow JSON structures — adjust as needed
    # Try top-level "findings" key first
    raw_findings = (
        data.get("findings") or
        data.get("vulnerabilities") or
        data.get("results") or
        []
    )

    for item in raw_findings:
        severity = item.get("severity", "").upper()

        if severity not in SEVERITY_TO_INGEST:
            continue

        findings.append({
            "severity":    severity,
            "name":        item.get("name") or item.get("title") or "Unknown",
            "component":   item.get("component") or item.get("artifact") or "Unknown",
            "version":     item.get("version") or "",
            "cve":         item.get("cve") or item.get("cveId") or "",
            "description": item.get("description") or item.get("detail") or "",
            "remediation": item.get("remediation") or item.get("fix") or item.get("recommendation") or "",
        })

    print(f"  [cyberflow] Parsed {len(findings)} HIGH/CRITICAL findings from JSON")
    return findings


def parse_console_log(filepath: str) -> list:
    """
    Fallback: extract findings from raw Jenkins console log.
    Looks for common Cyberflow log patterns.
    """
    with open(filepath, "r") as f:
        text = f.read()

    findings = []

    # Match lines like: [HIGH] log4j-2.14.0 CVE-2021-44228 ...
    pattern = re.compile(
        r"\[(HIGH|CRITICAL)\]\s+(.+?)(?:\s+CVE-([\d-]+))?\s*[-:]\s*(.+)",
        re.IGNORECASE
    )

    for match in pattern.finditer(text):
        severity, component, cve, description = match.groups()
        findings.append({
            "severity":    severity.upper(),
            "name":        f"CVE-{cve}" if cve else "Security Finding",
            "component":   component.strip(),
            "version":     "",
            "cve":         f"CVE-{cve}" if cve else "",
            "description": description.strip(),
            "remediation": "",   # Not in console logs — KB will supplement
        })

    print(f"  [cyberflow] Extracted {len(findings)} findings from console log")
    return findings


def findings_to_docs(findings: list, source_ref: str = "") -> list:
    """Convert parsed findings to KB documents."""
    docs = []

    for f in findings:
        # Build the text the LLM will read
        text_parts = [
            f"Cyberflow {f['severity']} severity finding.",
            f"Component: {f['component']} {f['version']}".strip(),
        ]
        if f["cve"]:
            text_parts.append(f"CVE: {f['cve']}")
        if f["description"]:
            text_parts.append(f"Description: {f['description']}")

        text = " ".join(text_parts)

        # Tags for search
        tags = ["cyberflow", "security", f['severity'].lower()]
        if f["cve"]:
            tags.append(f["cve"].lower())
        if f["component"]:
            tags.append(f["component"].lower().split(":")[0])

        doc = make_kb_document(
            text=text,
            source="cyberflow",
            error_type="cyberflow_scan",
            severity=f["severity"],
            tags=tags,
            resolution=f["remediation"] if f["remediation"] else None,
            raw_reference=source_ref,
        )
        docs.append(doc)

    return docs


def ingest_cyberflow(report_file=None, log_file=None):
    """Main ingestion entry point."""
    print("\n[cyberflow] Starting Cyberflow ingestion...")

    clear_source("cyberflow")

    findings = []

    if report_file:
        findings = parse_json_report(report_file)
        source_ref = report_file
    elif log_file:
        findings = parse_console_log(log_file)
        source_ref = log_file
    else:
        # No file provided — load sample for testing
        sample = "tests/sample_failures/cyberflow_failure.txt"
        print(f"  [cyberflow] No file provided. Using sample: {sample}")
        try:
            findings = parse_console_log(sample)
            source_ref = sample
        except FileNotFoundError:
            print("  [cyberflow] Sample file not found. Run with --file or --log argument.")
            return

    docs = findings_to_docs(findings, source_ref)
    inserted = insert_many(docs)
    print(f"\n[cyberflow] Done. {inserted} documents stored to MongoDB.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to Cyberflow JSON report file")
    parser.add_argument("--log",  help="Path to Jenkins console log file")
    args = parser.parse_args()

    ingest_cyberflow(report_file=args.file, log_file=args.log)
