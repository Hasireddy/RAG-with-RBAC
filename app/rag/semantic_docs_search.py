from .create_vector_store import create_vector_store
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()

# Build vector store once on import/startup
vector_store = create_vector_store()

# Step4:Run a semantic search

def semantic_search(vector_store, query, departments, k=5):

    allowed_departments = list(set(departments + ["general"]))

    results = vector_store.similarity_search_with_score(
        query=query,
        k=k,
        filter={
            "department": {
                "$in": allowed_departments
            }
        }
    )

    if not results:
        return ""

    filtered_docs = []

    for doc, score in results:
        # lower score = better match (depends on DB)
        if score < 0.75:
            filtered_docs.append(doc)

    if not filtered_docs:
        return ""

    # Deduplicate
    seen = set()
    unique_docs = []

    for doc in filtered_docs:
        content_hash = hash(doc.page_content)

        if content_hash not in seen:
            seen.add(content_hash)
            unique_docs.append(doc)

    context = "\n\n".join(
        f"[{i+1}] "
        f"Source={doc.metadata.get('source','Unknown')} | "
        f"Section={doc.metadata.get('section','N/A')} | "
        f"Dept={doc.metadata.get('department','N/A')}\n"
        f"{doc.page_content}"
        for i, doc in enumerate(unique_docs)
    )

    return context