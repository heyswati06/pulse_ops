"""
agent.py
────────
Main PulseOps agent.
Wires: failure log → parse → search KB → LLM → Teams post → PR raise

HOW TO RUN (test with a sample failure):
    python agent/agent.py --log tests/sample_failures/cyberflow_failure.txt --job cyberflow-scan-job
"""

import argparse
from agent.parser          import parse_failure_log
from knowledge_base.search import find_relevant_docs
from agent.prompt_builder  import build_prompt
from agent.llm_client      import call_llm
from agent.response_parser import parse_llm_response
from actions.teams_notifier import post_to_teams
from actions.git_pr_raiser  import raise_pr


def run_agent(failure_log: str, job_name: str = "", repo_url: str = ""):
    """
    Full agent pipeline.

    Args:
        failure_log : Raw console log text from the failed build
        job_name    : Jenkins job name (for context + logging)
        repo_url    : Git repo URL (for PR raising — optional)
    """
    print(f"\n[PulseOps] ⚡ Failure detected | Job: {job_name}")
    print("[PulseOps] Step 1/5 — Parsing failure log...")

    # ── Step 1: Parse ─────────────────────────────────────
    failure = parse_failure_log(failure_log, job_name)
    print(f"           Error type : {failure['error_type']}")
    print(f"           Severity   : {failure['severity']}")
    print(f"           Component  : {failure.get('component', 'N/A')}")
    print(f"           CVE        : {failure.get('cve', 'N/A')}")

    # ── Step 2: Search KB ─────────────────────────────────
    print("\n[PulseOps] Step 2/5 — Searching knowledge base...")
    kb_results = find_relevant_docs(
        query=failure["error_text"],
        error_type=failure["error_type"],
        limit=3
    )
    print(f"           Found {len(kb_results)} relevant KB documents")

    # ── Step 3: Build prompt ──────────────────────────────
    print("\n[PulseOps] Step 3/5 — Building LLM prompt...")
    prompt = build_prompt(failure, kb_results)

    # ── Step 4: Call LLM ──────────────────────────────────
    print("\n[PulseOps] Step 4/5 — Calling LLM...")
    raw_response = call_llm(prompt)
    fix = parse_llm_response(raw_response)

    print(f"\n           Summary    : {fix['summary']}")
    print(f"           Confidence : {fix['confidence']}")
    print(f"           Steps      : {len(fix['steps'])} steps")
    print(f"           Files      : {fix['files_to_change']}")

    # ── Step 5: Post to Teams ─────────────────────────────
    print("\n[PulseOps] Step 5/5 — Posting to Teams...")
    post_to_teams(
        job_name=job_name,
        failure=failure,
        fix=fix
    )

    # ── Step 6: Raise PR (optional) ───────────────────────
    if repo_url and fix.get("files_to_change"):
        print("\n[PulseOps] Raising draft PR...")
        raise_pr(repo_url=repo_url, fix=fix, job_name=job_name)

    print("\n[PulseOps] ✅ Done.\n")
    return fix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PulseOps Agent")
    parser.add_argument("--log",  required=True, help="Path to failure log file")
    parser.add_argument("--job",  default="",    help="Jenkins job name")
    parser.add_argument("--repo", default="",    help="Git repo URL for PR raising")
    args = parser.parse_args()

    with open(args.log, "r") as f:
        log_text = f.read()

    run_agent(failure_log=log_text, job_name=args.job, repo_url=args.repo)
