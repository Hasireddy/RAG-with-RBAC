import re
from .create_vector_store import create_vector_store
from langfuse.langchain import CallbackHandler
import time
import logging

logger = logging.getLogger(__name__)
langfuse_handler = CallbackHandler()

# Build vector store once on import/startup
vector_store = create_vector_store()

def query_aware_compress(text, query):
    sentences = re.split(r'(?<=[.!?])\s+', text)

    query_terms = set(query.lower().split())

    def score_sentence(s):
        s_lower = s.lower()
        return sum(1 for t in query_terms if t in s_lower)

    scored = [(score_sentence(s), s) for s in sentences]

    # keep top matching sentences
    scored.sort(reverse=True, key=lambda x: x[0])

    # take:
    # - all strong matches
    # - fallback top 2 if no matches
    top = [s for score, s in scored if score > 0]

    if not top:
        top = [s for _, s in scored[:2]]

    # safety: always keep max 5 sentences
    return " ".join(top[:5])




# Step4:Run a semantic search
def semantic_search(vector_store, query, departments):
    """Runs a semantic search with department based RAG and retrieves top 3 formatted context(matching results)"""

    allowed_departments = departments + ["general"]
    scored_results = vector_store.similarity_search_with_score(query=query, k=10)

    filtered_results = []
    relevant_but_unauthorized = False

    logger.info(f"RBAC retrieval | allowed = {allowed_departments} | threshold = 1")
    for doc, distance in scored_results:
        logger.info(
            f"    candidate dept = {doc.metadata.get('department')} | distance = {distance} | source = {doc.metadata.get('source')}"
        )
        # ignoring all weak matches entirely regardless of the department
        if distance > 1.5:
            continue

        if doc.metadata.get("department") in allowed_departments:
            filtered_results.append(doc)
        else:
            relevant_but_unauthorized = True

    filtered_results.sort(
        key=lambda d: query.lower() in d.page_content.lower(),
        reverse=True
    )

    if not filtered_results:
        status = "UNAUTHORIZED" if relevant_but_unauthorized else "NOT_FOUND"
        logger.info(f"RBAC decision | status = {status}")
        return{
           "context": "",
           "contexts": [],
           "documents": [],
           "status": status
        }
    logger.info(f"RBAC decision | filtered results = {len(filtered_results)}")
    compressed_chunks = []

    for doc in filtered_results:
        compressed = query_aware_compress(doc.page_content, query)

        compressed_chunks.append(
            f"""
            Source: {doc.metadata['source']}
            Section: {doc.metadata.get('Header 3', 'N/A')}
            Content:
            {compressed}
            """.strip()
        )

    context = "\n\n".join(compressed_chunks)


    #return context, "SUCCESS"
    return {
        "context": context,
        "contexts": [
            doc.page_content
            for doc in filtered_results
        ],
        "documents": filtered_results,
        "status": "SUCCESS"
    }





