"""
ingest_jenkins.py
─────────────────
Fetches failed Jenkins build logs via REST API.
Extracts only the ERROR section (last N lines).
Stores to MongoDB KB.

Owner: [ASSIGNED_TO]

HOW TO RUN:
    python ingestion/ingest_jenkins.py

HOW TO GET YOUR JENKINS JOB NAMES:
    Ask your team lead or check:
    https://YOUR_JENKINS_URL/api/json?tree=jobs[name]
    This lists all jobs. Pick the ones that fail most.
"""

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

from config import JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
from knowledge_base.schema import make_kb_document
from knowledge_base.store import insert_many, clear_source
from knowledge_base.chunker import clean_text, chunk_text

# ── CONFIG — edit these ───────────────────────────────────
# Ask your team: which Jenkins jobs fail most often?
# These are the job names to monitor for Week 2 demo
JOBS_TO_WATCH = [
    "cyberflow-scan-job",        # Replace with your actual job name
    "foss-vulnerability-check",  # Replace with your actual job name
    # "your-app-build-job",      # Add more as needed
]

# How many past failed builds to pull per job
BUILDS_TO_FETCH = 10

# Only extract last N lines of the log (errors are usually at the end)
LOG_TAIL_LINES = 40
# ─────────────────────────────────────────────────────────


def get_auth():
    return HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN)


def get_failed_build_numbers(job_name: str) -> list:
    """
    Get list of failed build numbers for a job.
    Jenkins API returns builds in reverse order (newest first).
    """
    url = f"{JENKINS_URL}/job/{job_name}/api/json"
    params = {"tree": f"builds[number,result,timestamp]{{0,{BUILDS_TO_FETCH}}}"}

    try:
        response = requests.get(url, auth=get_auth(), params=params, timeout=10)
        response.raise_for_status()
        builds = response.json().get("builds", [])

        # Only keep FAILED builds
        failed = [b["number"] for b in builds if b.get("result") == "FAILURE"]
        print(f"  [jenkins] Job '{job_name}': {len(failed)} failed builds found")
        return failed

    except Exception as e:
        print(f"  [jenkins] ERROR fetching builds for {job_name}: {e}")
        return []


def get_build_log(job_name: str, build_number: int) -> str:
    """
    Fetch console log for a specific build.
    Returns last LOG_TAIL_LINES lines only — errors live here.
    """
    url = f"{JENKINS_URL}/job/{job_name}/{build_number}/consoleText"

    try:
        response = requests.get(url, auth=get_auth(), timeout=15)
        response.raise_for_status()
        lines = response.text.splitlines()

        # Take last N lines — that's where failures are
        tail = "\n".join(lines[-LOG_TAIL_LINES:])
        return tail

    except Exception as e:
        print(f"  [jenkins] ERROR fetching log {job_name}#{build_number}: {e}")
        return ""


def classify_error(log_text: str) -> tuple:
    """
    Very simple rule-based classifier.
    Returns (error_type, severity, tags)

    You can expand these rules as Joel identifies more patterns.
    """
    log_lower = log_text.lower()

    if "cyberflow" in log_lower or "security scan" in log_lower:
        return "cyberflow_scan", "HIGH", ["cyberflow", "security", "scan"]

    if "foss" in log_lower or "vulnerability" in log_lower or "cve-" in log_lower:
        return "foss_vulnerability", "HIGH", ["foss", "vulnerability", "dependency"]

    if "nexus" in log_lower or "could not resolve" in log_lower or "artifact" in log_lower:
        return "nexus_dependency", "MEDIUM", ["nexus", "dependency", "artifact"]

    if "docker" in log_lower or "container" in log_lower:
        return "docker_build", "MEDIUM", ["docker", "container"]

    if "out of memory" in log_lower or "heap space" in log_lower:
        return "build_failure", "HIGH", ["memory", "heap", "java"]

    # Default
    return "build_failure", "MEDIUM", ["build", "jenkins"]


def ingest_jenkins():
    """
    Main ingestion function.
    Run this manually before Week 2 demo to populate the KB.
    """
    print("\n[jenkins] Starting Jenkins ingestion...")
    print(f"[jenkins] Jobs to process: {JOBS_TO_WATCH}\n")

    # Clear old Jenkins docs before re-ingesting (avoid duplicates)
    clear_source("jenkins")

    all_docs = []

    for job_name in JOBS_TO_WATCH:
        failed_builds = get_failed_build_numbers(job_name)

        for build_num in failed_builds:
            log_text = get_build_log(job_name, build_num)

            if not log_text:
                continue

            # Classify the error
            error_type, severity, tags = classify_error(log_text)

            # Clean + chunk (each chunk = one KB document)
            cleaned = clean_text(log_text)
            chunks  = chunk_text(cleaned, chunk_size=200)

            for chunk in chunks:
                doc = make_kb_document(
                    text=chunk,
                    source="jenkins",
                    error_type=error_type,
                    severity=severity,
                    tags=tags,
                    job_name=job_name,
                    raw_reference=f"{JENKINS_URL}/job/{job_name}/{build_num}/consoleText"
                )
                all_docs.append(doc)

    inserted = insert_many(all_docs)
    print(f"\n[jenkins] Done. {inserted} documents stored to MongoDB.\n")


if __name__ == "__main__":
    ingest_jenkins()
