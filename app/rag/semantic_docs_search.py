from .create_vector_store import create_vector_store


# Build vector store once on import/startup
vector_store = create_vector_store()

# Step4:Run a semantic search
def semantic_search(vector_store, query, departments):
    """
    Semantic search with department-based RBAC filtering
    """

    allowed_departments = list(set(departments + ["general"]))

    results = vector_store.similarity_search(
        query=query,
        k=3,
        filter={
            "department": {
                "$in": allowed_departments
            }
        }
    )

    context = "\n\n".join(
        f"""
        Source: {doc.metadata.get('source', 'Unknown')}
        Section: {doc.metadata.get('Header 3', 'N/A')}
        Department: {doc.metadata.get('department', 'N/A')}
        
        Content:
        {doc.page_content}
        """.strip()
        for doc in results
    )

    return context
