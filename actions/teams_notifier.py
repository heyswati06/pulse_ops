"""
teams_notifier.py
─────────────────
Posts PulseOps resolution suggestion to a Teams channel via incoming webhook.

HOW TO GET WEBHOOK URL:
    In your Teams child channel → ... → Connectors → Incoming Webhook → Configure
    Copy the URL. Paste into .env as TEAMS_WEBHOOK_URL
"""

import requests
from config import TEAMS_WEBHOOK_URL

CONFIDENCE_EMOJI = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}


def post_to_teams(job_name: str, failure: dict, fix: dict):
    """
    Post a structured fix suggestion to the Teams channel.
    Uses simple Teams message card format — no special setup needed.
    """
    confidence_icon = CONFIDENCE_EMOJI.get(fix.get("confidence", "MEDIUM"), "🟡")
    steps_text = "\n".join(
        f"{i+1}. {step}" for i, step in enumerate(fix.get("steps", []))
    )
    files_text = (
        ", ".join(fix.get("files_to_change", [])) or "No file changes needed"
    )

    message = {
        "@type":      "MessageCard",
        "@context":   "https://schema.org/extensions",
        "themeColor": "00C9A7",
        "summary":    f"PulseOps: Fix suggestion for {job_name}",
        "sections": [
            {
                "activityTitle":    f"⚡ PulseOps — CI Failure Detected",
                "activitySubtitle": f"Job: **{job_name}** | Error: {failure.get('error_type')} | Severity: {failure.get('severity')}",
                "activityText":     f"**Root Cause:** {fix.get('summary', 'Unknown')}",
                "facts": [
                    {"name": "Component",   "value": failure.get("component") or "N/A"},
                    {"name": "CVE",         "value": failure.get("cve") or "N/A"},
                    {"name": "Confidence",  "value": f"{confidence_icon} {fix.get('confidence')}"},
                    {"name": "Files",       "value": files_text},
                ],
            },
            {
                "title": "📋 Resolution Steps",
                "text":  steps_text or "No steps generated.",
            }
        ]
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=message, timeout=10)
        response.raise_for_status()
        print("  [teams] ✅ Message posted successfully")
    except Exception as e:
        print(f"  [teams] ERROR posting to Teams: {e}")


def test_webhook():
    """Quick test — send a dummy message to verify webhook is working."""
    test_message = {
        "@type":      "MessageCard",
        "@context":   "https://schema.org/extensions",
        "themeColor": "00C9A7",
        "summary":    "PulseOps webhook test",
        "text":       "✅ PulseOps Teams webhook is working! Squad is ready to go. 🚀"
    }
    requests.post(TEAMS_WEBHOOK_URL, json=test_message)
    print("[teams] Test message sent. Check your Teams channel.")


if __name__ == "__main__":
    test_webhook()
