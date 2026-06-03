from pymongo import MongoClient, TEXT
from config import MONGO_URI, MONGO_DB

# ── Connection (reused across all calls) ──────────────────
_client = None

def get_collection():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    db = _client[MONGO_DB]
    collection = db["knowledge"]

    # Create text index once — enables MongoDB text search
    existing_indexes = collection.index_information()
    if "text_index" not in existing_indexes:
        collection.create_index(
            [("text", TEXT), ("tags", TEXT), ("resolution", TEXT)],
            name="text_index"
        )
    return collection


def insert_document(doc: dict) -> str:
    """Insert one KB document. Returns inserted ID."""
    collection = get_collection()
    result = collection.insert_one(doc)
    print(f"  [store] Inserted: {doc['source']} | {doc['error_type']} | id={result.inserted_id}")
    return str(result.inserted_id)


def insert_many(docs: list) -> int:
    """Bulk insert. Returns count inserted."""
    if not docs:
        print("  [store] Nothing to insert.")
        return 0
    collection = get_collection()
    result = collection.insert_many(docs)
    print(f"  [store] Inserted {len(result.inserted_ids)} documents.")
    return len(result.inserted_ids)


def clear_source(source: str):
    """Soft-delete all docs from a source before re-ingesting."""
    collection = get_collection()
    result = collection.update_many(
        {"source": source},
        {"$set": {"is_active": False}}
    )
    print(f"  [store] Soft-deleted {result.modified_count} docs from source: {source}")


def test_connection():
    """Quick sanity check — run this first."""
    try:
        collection = get_collection()
        count = collection.count_documents({"is_active": True})
        print(f"[store] MongoDB connected. Active KB docs: {count}")
        return True
    except Exception as e:
        print(f"[store] Connection FAILED: {e}")
        return False


if __name__ == "__main__":
    test_connection()
