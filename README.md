# PulseOps 🤖⚡
> DevOps AI Knowledge Agent — Reference Data Service Line AI COI Wave 1

Detects CI/CD failures → queries a knowledge base → posts fix suggestions to Teams → raises draft PRs.

---

## Sequence — What Happens When

```
SETUP (run once before demo)           RUNTIME (every CI failure)
────────────────────────────           ──────────────────────────
1. Copy .env.example → .env            1. trigger.py detects failure
2. Fill in credentials                 2. agent.py reads the log
3. Run: python ingestion/              3. Searches MongoDB KB
        run_all_ingestion.py           4. Calls LLM with context
   → Confluence pages fetched          5. Posts fix to Teams
   → Cyberflow findings stored         6. Raises draft PR (Week 3+)
   → Jenkins failed logs stored
   → All chunks saved to MongoDB
```

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd pulseops
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your credentials

# 3. Test MongoDB connection
python knowledge_base/store.py

# 4. Test Teams webhook
python actions/teams_notifier.py

# 5. Run ingestion (populate the KB)
python ingestion/run_all_ingestion.py

# 6. Run agent on sample failure (the demo!)
python agent/agent.py \
  --log tests/sample_failures/cyberflow_failure.txt \
  --job cyberflow-scan-job
```

---

## Who Owns What

| File | Owner |
|------|-------|
| `ingestion/ingest_jenkins.py`    | [ASSIGNED_TO] |
| `ingestion/ingest_cyberflow.py`  | [ASSIGNED_TO] |
| `ingestion/ingest_confluence.py` | [ASSIGNED_TO] |
| `knowledge_base/store.py`        | Niru |
| `knowledge_base/search.py`       | Niru |
| `agent/agent.py`                 | Swati |
| `agent/llm_client.py`            | Swati |
| `actions/teams_notifier.py`      | Rama |
| `actions/git_pr_raiser.py`       | Rama |

---

## Week 2 Demo Checklist

- [ ] MongoDB connected and KB has docs (`python knowledge_base/store.py`)
- [ ] Confluence runbook pages ingested
- [ ] Cyberflow HIGH/CRITICAL findings ingested
- [ ] Jenkins failed builds ingested
- [ ] Agent runs on `cyberflow_failure.txt` end-to-end
- [ ] Teams webhook posts fix suggestion
- [ ] Demo scenario agreed with Joel

---

## Folder Structure

```
pulseops/
├── ingestion/          # One script per source — fetch + store
├── knowledge_base/     # MongoDB operations — store, search, schema
├── agent/              # Core agent — parse, prompt, LLM call, response
├── actions/            # Output — Teams post, PR raise
├── tests/              # Sample failure logs for testing
└── data/runbooks/      # Drop raw text files here (manual fallback)
```
