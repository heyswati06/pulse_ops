from datetime import datetime

# ─────────────────────────────────────────────────────────────
# VALID VALUES — use these exact strings everywhere
# ─────────────────────────────────────────────────────────────
VALID_SOURCES = [
    "jenkins",
    "cyberflow",
    "foss",
    "confluence",
    "snow",
    "git",
    "nexus",
    "docker",
    "shp",
    "manual",        # for hand-crafted entries
]

VALID_ERROR_TYPES = [
    "cyberflow_scan",
    "foss_vulnerability",
    "build_failure",
    "deploy_failure",
    "nexus_dependency",
    "docker_pull",
    "docker_build",
    "test_failure",
    "config_error",
    "general",
]

VALID_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", None]


def make_kb_document(
    text: str,
    source: str,
    error_type: str,
    tags: list,
    resolution: str = None,
    severity: str = None,
    raw_reference: str = None,
    job_name: str = None,
) -> dict:
    """
    Single standard structure for every KB document.
    Every ingestor calls this. Never build the dict manually.

    Args:
        text          : The chunk of text the LLM will read
        source        : Where it came from — see VALID_SOURCES
        error_type    : Type of failure — see VALID_ERROR_TYPES
        tags          : List of keywords for text search ["log4j", "CVE-2021-44228"]
        resolution    : Known fix text if available (from Snow or Confluence)
        severity      : CRITICAL / HIGH / MEDIUM / LOW / None
        raw_reference : URL, job name, or Snow ticket number this came from
        job_name      : Jenkins job name if applicable
    """
    assert source in VALID_SOURCES,     f"Invalid source: {source}"
    assert error_type in VALID_ERROR_TYPES, f"Invalid error_type: {error_type}"
    assert severity in VALID_SEVERITIES,    f"Invalid severity: {severity}"

    return {
        "text":          text,
        "resolution":    resolution,
        "source":        source,
        "error_type":    error_type,
        "severity":      severity,
        "tags":          tags,
        "job_name":      job_name,
        "raw_reference": raw_reference,
        "fetched_at":    datetime.utcnow(),
        "is_active":     True,
    }
