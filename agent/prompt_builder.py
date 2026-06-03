def build_prompt(failure: dict, kb_results: list) -> str:
    """Build the prompt sent to the LLM."""

    # Format KB results
    if kb_results:
        kb_section = ""
        for i, doc in enumerate(kb_results, 1):
            kb_section += f"\n--- KB Result {i} (source: {doc['source']}) ---\n"
            kb_section += doc["text"]
            if doc.get("resolution"):
                kb_section += f"\n✅ KNOWN FIX: {doc['resolution']}"
    else:
        kb_section = "No matching documents found in knowledge base."

    prompt = f"""
CI PIPELINE FAILURE
===================
Job:        {failure.get('job_name', 'Unknown')}
Error Type: {failure.get('error_type', 'Unknown')}
Severity:   {failure.get('severity', 'Unknown')}
Component:  {failure.get('component', 'Not identified')}
CVE:        {failure.get('cve', 'None')}

FAILURE LOG (relevant lines):
{failure['error_text']}

KNOWLEDGE BASE RESULTS:
{kb_section}

Provide the resolution following the format in your instructions.
"""
    return prompt
