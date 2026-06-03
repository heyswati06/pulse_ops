from knowledge_base.store import get_collection


def find_relevant_docs(query: str, error_type: str = None, limit: int = 3) -> list:
    """
    Search MongoDB KB by text similarity.
    Returns top `limit` matching documents.

    MongoDB text search matches on: text, tags, resolution fields
    (all three are indexed — see store.py)

    Args:
        query      : The error message or keywords to search for
        error_type : Optional — narrow results to one failure type
        limit      : Max docs to return (3 is enough for LLM context)
    """
    collection = get_collection()

    # Build filter
    search_filter = {
        "$text":     {"$search": query},
        "is_active": True,
    }
    if error_type:
        search_filter["error_type"] = error_type

    results = collection.find(
        search_filter,
        {"score": {"$meta": "textScore"}}   # score = relevance
    ).sort(
        [("score", {"$meta": "textScore"})]  # highest relevance first
    ).limit(limit)

    docs = list(results)
    print(f"  [search] Query: '{query[:60]}...' → {len(docs)} results found")
    return docs


def find_by_tags(tags: list, limit: int = 3) -> list:
    """
    Alternative search — find docs matching specific tags.
    Useful when text search returns no results.
    """
    collection = get_collection()
    results = collection.find(
        {"tags": {"$in": tags}, "is_active": True}
    ).limit(limit)
    return list(results)
