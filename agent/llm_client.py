"""
llm_client.py
─────────────
Single function to call your internal LLM.
Only this file needs to change if your LLM endpoint changes.
"""

import requests
from config import LLM_ENDPOINT, LLM_API_KEY, LLM_MODEL

SYSTEM_PROMPT = """
You are a senior DevOps engineer with deep knowledge of CI/CD pipelines,
security scanning, and build systems.

You will receive:
1. A CI/CD failure log
2. Relevant documents from our internal knowledge base

Your job: provide a clear, actionable resolution.

Rules:
- Be specific. Name exact files, commands, version numbers.
- If the KB contains a known fix, use it directly.
- If unsure, say so clearly — do not guess blindly.
- Keep your response structured and concise.

Always respond in this exact format:

SUMMARY: One sentence describing the root cause.
STEPS:
1. First step
2. Second step
3. (Add more as needed)
FILES_TO_CHANGE: pom.xml, Dockerfile (comma-separated, or NONE if no file changes needed)
CONFIDENCE: HIGH / MEDIUM / LOW
"""


def call_llm(prompt: str) -> str:
    """
    Call your internal LLM endpoint.
    Returns the raw text response.
    """
    try:
        response = requests.post(
            url=LLM_ENDPOINT,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens":   600,
                "temperature":  0.2,   # Low temperature = more consistent, less creative
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"  [llm] ERROR calling LLM: {e}")
        return "SUMMARY: LLM call failed.\nSTEPS:\n1. Check LLM endpoint configuration.\nFILES_TO_CHANGE: NONE\nCONFIDENCE: LOW"
