from .create_vector_store import create_vector_store
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()

# Build vector store once on import/startup
vector_store = create_vector_store()

# Step4:Run a semantic search

def semantic_search(vector_store, query, departments, k=5):
    """Runs a semantic search with department based RAG and retrieves top 5 formatted context(matching results)"""
    #results = vector_store.similarity_search(query=query, k=5)
    # results = vector_store.similarity_search(query=query, k=3)
    #departments.append("general")
    #filtered_results = [result for result in results if result.metadata.get("department") in departments]
    allowed_departments = list(set(departments + ["general"]))

    results = vector_store.similarity_search(
        query=query,
        k=10,
        filter={
            "department": {
                "$in": allowed_departments
            }
        }
    )

    if not results:
        print("[semantic_search] No results found for departments:", allowed_departments)
        return ""

    # Build a clean context from top-3 chunks
    context = "\n\n".join(
        f"""Source: {doc.metadata.get('source', 'Unknown')}
    Section: {doc.metadata.get('Header 3', 'N/A')}
    Department: {doc.metadata.get('department', 'N/A')}

    Content:
    {doc.page_content}""".strip()
        for doc in results[:k]  # Ensures top 3 formatted context matches
    )

    print("***************************************************")
    print("Context compiled successfully:\n", context[:1000])
    return context





