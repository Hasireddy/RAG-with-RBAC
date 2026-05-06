from .create_vector_store import create_vector_store

# Build vector store once on import/startup
vector_store = create_vector_store()

# Step4:Run a semantic search
def semantic_search(vector_store, query):
    """Runs a semantic search and retrieves top 3 formatted context(matching results)"""

    results = vector_store.similarity_search(query=query, k=3)

    # for i, doc in enumerate(results, start=1):
    # print(f"\n---Result{i}---")
    # print(doc.page_content)
    # print(doc.metadata)

    # Build a clean context from top-3 chunks
    context = "\n\n".join(
        f"""
    Source: {doc.metadata['source']}
    Section: {doc.metadata.get('Header 3', 'N/A')}
    Content:
    {doc.page_content}
    """
        .strip()
        for doc in results
    )
    return context

#query = "What is python?"
#context = semantic_search(vector_store, query)
#print(context)
