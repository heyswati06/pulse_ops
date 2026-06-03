"""
run_all_ingestion.py
────────────────────
Master script — runs all ingestors in the right order.
Run this once before the Week 2 demo, and weekly after that.

HOW TO RUN:
    python ingestion/run_all_ingestion.py

SEQUENCE:
    1. Confluence  (runbooks — highest quality, run first)
    2. Cyberflow   (scan findings — the demo use case)
    3. Jenkins     (build logs — supplements Cyberflow context)
    4. Snow        (resolved incidents — adds resolution history)
"""

from ingestion.ingest_confluence import ingest_confluence
from ingestion.ingest_cyberflow  import ingest_cyberflow
from ingestion.ingest_jenkins    import ingest_jenkins
from knowledge_base.store        import get_collection


def print_summary():
    collection = get_collection()
    total = collection.count_documents({"is_active": True})
    by_source = collection.aggregate([
        {"$match":  {"is_active": True}},
        {"$group":  {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort":   {"count": -1}}
    ])
    print("\n" + "="*50)
    print("KB SUMMARY AFTER INGESTION")
    print("="*50)
    for s in by_source:
        print(f"  {s['_id']:20s} : {s['count']} docs")
    print(f"  {'TOTAL':20s} : {total} docs")
    print("="*50 + "\n")


if __name__ == "__main__":
    print("\n[PulseOps] Starting full ingestion run...")
    print("[PulseOps] Order: Confluence → Cyberflow → Jenkins\n")

    ingest_confluence()
    ingest_cyberflow()
    ingest_jenkins()

    print_summary()
    print("[PulseOps] Ingestion complete. KB is ready for the agent.\n")
