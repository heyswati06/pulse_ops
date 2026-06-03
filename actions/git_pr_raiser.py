"""
git_pr_raiser.py
────────────────
Raises a draft PR with the fix suggestion.
Week 3 feature — skip for Week 2 demo, agent still works without it.

Owner: Rama
"""

import requests
from config import GIT_TOKEN, GIT_BASE_URL


def raise_pr(repo_url: str, fix: dict, job_name: str) -> bool:
    """
    Raise a draft PR with fix suggestion as PR description.
    NOTE: This is a placeholder — wire to your actual Git API.

    For Week 2 demo — this can just print the PR content,
    no actual API call needed. Comment out the requests.post below.
    """
    pr_body = f"""## 🤖 PulseOps — Auto-suggested Fix

**Triggered by:** CI failure in `{job_name}`

**Root cause:** {fix.get('summary', 'Unknown')}

**Files to change:** {', '.join(fix.get('files_to_change', []))}

**Resolution steps:**
{chr(10).join(f"- {s}" for s in fix.get("steps", []))}

---
*This PR was raised automatically by PulseOps.*
*Please review before merging. Confidence: {fix.get('confidence')}*
"""

    print("\n[git] Draft PR content:")
    print(pr_body)

    # Uncomment below once Git API access is confirmed — Week 3
    # headers = {"Authorization": f"Bearer {GIT_TOKEN}"}
    # payload = {
    #     "title": f"[PulseOps] Auto-fix: {fix.get('summary', '')[:60]}",
    #     "body":  pr_body,
    #     "head":  "pulseops/auto-fix",
    #     "base":  "main",
    #     "draft": True
    # }
    # response = requests.post(f"{GIT_BASE_URL}/repos/{repo_url}/pulls",
    #                          headers=headers, json=payload)
    # print(f"  [git] PR raised: {response.json().get('html_url')}")

    return True
