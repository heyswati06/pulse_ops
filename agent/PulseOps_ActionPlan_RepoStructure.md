# PulseOps — Source Action Plan + Repo Structure
> Squad: PulseOps | Lead: Swati Sharma | Last updated: 29 May 2026

---

## 1. SOURCE ACTION PLAN TABLE

| # | Source | What to Identify (Page/Query/Job) | What to Extract | Script to Write | Assigned To | Priority | Target |
|---|--------|-----------------------------------|-----------------|-----------------|-------------|----------|--------|
| 1 | **Jenkins** | Top 5 failing job names + their build log URLs | Error section only (last 30 lines of failed build), job name, timestamp, error type | `ingest_jenkins.py` — fetch failed builds via Jenkins REST API, extract error block, chunk, store to MongoDB | | 🔴 HIGH | Week 1 |
| 2 | **Cyberflow Scans** | Cyberflow scan job names in Jenkins + report export format | Vulnerability name, severity (HIGH/CRITICAL only), affected component, remediation guidance | `ingest_cyberflow.py` — parse scan report JSON/XML, filter HIGH+CRITICAL, store structured doc per finding | | 🔴 HIGH | Week 1 |
| 3 | **FOSS Scans** | FOSS scan job names + output format (JSON/XML/HTML) | Package name, CVE ID, severity, recommended version fix | `ingest_foss.py` — parse FOSS output, extract CVE entries, map to fix suggestion, store to MongoDB | | 🔴 HIGH | Week 1 |
| 4 | **Confluence** | 5-8 page IDs: Cyberflow runbook, FOSS guide, deployment troubleshooting, KB articles | Full page text cleaned to plain text, chunked to 300-word segments | `ingest_confluence.py` — Confluence REST API, fetch by page ID, strip HTML, chunk, store | | 🔴 HIGH | Week 1 |
| 5 | **ServiceNow / JIRA** | Assignment group name + query filter for DevOps incidents last 180 days, resolved only | Short description, resolution notes, category, tags | `ingest_snow.py` — Snow REST API, filter by assignment group + state=Resolved, extract resolution notes | | 🟡 MED | Week 1-2 |
| 6 | **Git / GitHub / Bitbucket** | Repos with most frequent PR failures or build breaks | PR title, error in CI comment, linked Jenkins job, fix commit message | `ingest_git.py` — Git API, fetch PRs with failed checks, extract CI failure comment + merge commit message | | 🟡 MED | Week 2 |
| 7 | **Nexus** | Nexus repo URLs where dependency resolution fails | Artifact name, version, group ID, error type (not found / checksum fail) | `ingest_nexus.py` — parse Nexus logs or API, extract failed resolution events, map to fix (version update/mirror) | | 🟡 MED | Week 2 |
| 8 | **Docker / Container Issues** | Docker registry URL + list of images that fail to build/pull | Image name, tag, error message (layer fail / auth fail / size limit) | `ingest_docker.py` — parse Docker build logs from Jenkins, extract failure type, map to known fix | | 🟢 LOW | Week 3 |
| 9 | **SHP / IKP** | SHP pipeline names + IKP job definitions | Pipeline stage failures, config issues, environment errors | `ingest_shp.py` — parse SHP/IKP pipeline logs, extract stage failure + error message | | 🟢 LOW | Week 3 |
| 10 | **Email/Teams alerts** | DevOps alert channels or mailboxes for build/deploy notifications | Alert type, system, error summary, timestamp | `ingest_alerts.py` — Teams webhook listener or email parser, extract structured alert fields | | 🟢 LOW | Wave 2 |

---

## 2. WHAT TO PICK FIRST FOR WEEK 2 DEMO

**Answer: Jenkins failed builds + Cyberflow scan failures. Together.**

Here is why:

```
Jenkins log shows:     "Cyberflow scan FAILED — HIGH severity vulnerability detected"
                                ↓
Your agent reads it    Identifies it is a Cyberflow failure
                                ↓
Queries KB             Finds matching Cyberflow remediation from Confluence runbook
                                ↓
Posts to Teams         "Vulnerability: log4j-2.14. Fix: update to 2.17.1 in pom.xml"
                                ↓
Raises PR              Automated fix PR created in the repo
```

This is your **complete happy path** — one failure type, one KB source, one output.
Demo-able. Impressive. Achievable in 2 weeks.

**Start ingesting:**
1. Confluence runbook pages for Cyberflow (Joel gives you page IDs)
2. Last 30 days Cyberflow HIGH/CRITICAL scan results
3. Last 30 days Jenkins failed builds from Cyberflow scan job only

Everything else is Week 3 onwards.

---

## 3. REPO STRUCTURE

```
pulseops/
│
├── README.md                          # How to run the whole thing
├── .env.example                       # All env vars — LLM key, Mongo URI, webhook URLs
├── requirements.txt                   # All Python dependencies
├── config.py                          # Central config — reads from .env
│
├── ingestion/                         # One file per source — each person owns their file
│   ├── __init__.py
│   ├── ingest_jenkins.py              # Fetch failed Jenkins build logs
│   ├── ingest_cyberflow.py            # Parse Cyberflow scan reports
│   ├── ingest_foss.py                 # Parse FOSS vulnerability reports
│   ├── ingest_confluence.py           # Fetch + chunk Confluence pages
│   ├── ingest_snow.py                 # Fetch resolved ServiceNow incidents
│   ├── ingest_git.py                  # Fetch failed PR CI checks from Git
│   ├── ingest_nexus.py                # Parse Nexus dependency failures
│   ├── ingest_docker.py               # Parse Docker build/pull failures
│   └── run_all_ingestion.py           # Master script — runs all ingestors in sequence
│
├── knowledge_base/
│   ├── __init__.py
│   ├── schema.py                      # MongoDB document structure (see below)
│   ├── store.py                       # Insert / update / delete KB documents
│   ├── search.py                      # Search KB by keyword (MongoDB text search)
│   └── chunker.py                     # Split long text into 300-word chunks
│
├── agent/
│   ├── __init__.py
│   ├── trigger.py                     # Detect CI failure event (poll or webhook)
│   ├── parser.py                      # Extract error type + context from failure log
│   ├── prompt_builder.py              # Build LLM prompt from failure + KB results
│   ├── llm_client.py                  # Your internal LLM API call — single function
│   ├── response_parser.py             # Parse LLM response into structured fix
│   └── agent.py                       # Main agent — wires all steps together
│
├── actions/
│   ├── __init__.py
│   ├── teams_notifier.py              # Post fix suggestion to Teams via webhook
│   └── git_pr_raiser.py              # Raise a draft PR with the suggested fix
│
├── data/
│   └── runbooks/                      # Raw text files — drop Confluence exports here
│       ├── cyberflow_runbook.txt
│       ├── foss_guide.txt
│       └── deployment_troubleshooting.txt
│
└── tests/
    ├── test_ingestion.py
    ├── test_search.py
    ├── test_agent.py
    └── sample_failures/               # Sample failed build logs for testing
        ├── cyberflow_failure.txt
        ├── foss_failure.txt
        └── jenkins_failure.txt
```

---

## 4. MONGODB DOCUMENT STRUCTURE

Every document in the `knowledge` collection follows this exact schema:

```python
# knowledge_base/schema.py

from datetime import datetime

def make_kb_document(
    text: str,
    source: str,
    error_type: str,
    tags: list,
    resolution: str = None,
    severity: str = None,
    raw_reference: str = None
) -> dict:
    """
    Standard KB document.
    Every ingestor calls this function — consistent structure across all sources.
    """
    return {
        # ── Core fields ──────────────────────────────
        "text": text,                  # The full chunk text — what the LLM reads
        "resolution": resolution,      # Known fix if available (from Snow/Confluence)

        # ── Source metadata ──────────────────────────
        "source": source,              # "jenkins" | "cyberflow" | "confluence" | "snow" etc
        "error_type": error_type,      # "cyberflow_scan" | "foss_vulnerability" | "build_fail"
        "severity": severity,          # "HIGH" | "CRITICAL" | "MEDIUM" | None

        # ── Search fields ────────────────────────────
        "tags": tags,                  # ["log4j", "dependency", "vulnerability"]

        # ── Audit fields ─────────────────────────────
        "raw_reference": raw_reference,  # URL or job name this came from
        "fetched_at": datetime.utcnow(),
        "is_active": True              # Set False to soft-delete stale docs
    }

# Example — Cyberflow finding
example = make_kb_document(
    text="HIGH severity vulnerability detected in log4j-2.14.0. CVE-2021-44228.",
    source="cyberflow",
    error_type="cyberflow_scan",
    resolution="Update log4j to 2.17.1 in pom.xml. Run: mvn dependency:tree to verify removal.",
    severity="HIGH",
    tags=["log4j", "CVE-2021-44228", "dependency", "vulnerability"],
    raw_reference="https://jenkins/job/cyberflow-scan/build/142"
)
```

---

## 5. THE AGENT — Full Wiring

```python
# agent/agent.py
# This is the main script. Run this when a CI failure is detected.

from agent.trigger import detect_failure
from agent.parser import parse_failure_log
from knowledge_base.search import find_relevant_docs
from agent.prompt_builder import build_prompt
from agent.llm_client import call_llm
from agent.response_parser import parse_llm_response
from actions.teams_notifier import post_to_teams
from actions.git_pr_raiser import raise_pr

def run_agent(failure_log: str, job_name: str, repo_url: str):

    print(f"[PulseOps] Failure detected in job: {job_name}")

    # Step 1 — Parse what kind of failure this is
    failure = parse_failure_log(failure_log)
    # failure = { "error_type": "cyberflow_scan", "error_text": "...", "component": "log4j" }

    # Step 2 — Search KB for relevant docs
    kb_results = find_relevant_docs(
        query=failure["error_text"],
        error_type=failure["error_type"],
        limit=3
    )

    # Step 3 — Build the LLM prompt
    prompt = build_prompt(failure, kb_results)

    # Step 4 — Call your internal LLM
    llm_response = call_llm(prompt)

    # Step 5 — Parse the response into structured fix
    fix = parse_llm_response(llm_response)
    # fix = { "summary": "...", "steps": ["...", "..."], "files_to_change": ["pom.xml"] }

    # Step 6 — Post to Teams
    post_to_teams(
        job_name=job_name,
        failure_summary=failure["error_text"],
        fix=fix
    )

    # Step 7 — Raise a draft PR if files to change are identified
    if fix.get("files_to_change"):
        raise_pr(
            repo_url=repo_url,
            fix=fix,
            job_name=job_name
        )

    print(f"[PulseOps] Resolution posted. Job: {job_name}")
```

---

## 6. LLM CALL — The Part You Already Know

```python
# agent/llm_client.py
# Replace call_internal_llm_api with your actual internal API call

import requests

def call_llm(prompt: str) -> str:
    """
    Single function — your internal LLM endpoint.
    You already know how to do this part.
    """
    response = requests.post(
        url="YOUR_INTERNAL_LLM_ENDPOINT",
        headers={
            "Authorization": "Bearer YOUR_TOKEN",
            "Content-Type": "application/json"
        },
        json={
            "model": "YOUR_MODEL_NAME",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a DevOps expert. You will be given a CI/CD failure log "
                        "and relevant knowledge base documents. "
                        "Provide a clear, actionable resolution. "
                        "Be specific — name exact files, commands, and version numbers. "
                        "Format your response as: "
                        "SUMMARY: one sentence. "
                        "STEPS: numbered list. "
                        "FILES_TO_CHANGE: comma-separated list of files, or NONE."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500
        }
    )
    return response.json()["choices"][0]["message"]["content"]
```

---

## 7. PROMPT STRUCTURE — What Goes to the LLM

```python
# agent/prompt_builder.py

def build_prompt(failure: dict, kb_results: list) -> str:

    kb_context = ""
    for i, doc in enumerate(kb_results, 1):
        kb_context += f"\n--- KB Result {i} (source: {doc['source']}) ---\n"
        kb_context += doc["text"]
        if doc.get("resolution"):
            kb_context += f"\nKNOWN FIX: {doc['resolution']}"

    prompt = f"""
CI PIPELINE FAILURE DETECTED
=============================
Job: {failure.get('job_name', 'Unknown')}
Error Type: {failure.get('error_type', 'Unknown')}
Severity: {failure.get('severity', 'Unknown')}

FAILURE LOG:
{failure['error_text']}

RELEVANT KNOWLEDGE BASE RESULTS:
{kb_context if kb_context else "No matching KB documents found."}

Based on the above, provide the resolution.
If KB results contain a known fix, use it directly.
If not, reason from the failure log and suggest the most likely fix.
Always be specific — exact file names, commands, version numbers.
"""
    return prompt
```

---

## 8. QUICK START — What Each Person Runs First

```bash
# Clone the repo
git clone <repo-url>
cd pulseops

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your values
cp .env.example .env

# Anil — test your Jenkins ingestor
python ingestion/ingest_jenkins.py --job "cyberflow-scan-job" --days 30

# Niru — test MongoDB connection + store one doc
python knowledge_base/store.py --test

# Joel — load the Confluence runbook pages
python ingestion/ingest_confluence.py --pages "PAGE_ID_1,PAGE_ID_2"

# Rama — test the Teams webhook
python actions/teams_notifier.py --test

# Swati — run the full agent on a sample failure
python agent/agent.py --log tests/sample_failures/cyberflow_failure.txt
```

---

## 9. WEEK 2 DEMO CHECKLIST

Before 4th June this should be ticked:

```
[ ] MongoDB running + knowledge collection created
[ ] At least 5 Confluence chunks ingested (Joel's pages)
[ ] At least 3 Cyberflow HIGH severity findings ingested
[ ] agent.py runs end-to-end on sample_failures/cyberflow_failure.txt
[ ] Teams webhook posts the fix suggestion successfully
[ ] Demo scenario agreed: exact failure log → expected Teams message
[ ] README written so any squad member can run it in 5 mins
```

---

*Add your Assigned_To column to the source table above and share in the child channel.*
*One person per source = one person owns identify + script. No overlaps.*
