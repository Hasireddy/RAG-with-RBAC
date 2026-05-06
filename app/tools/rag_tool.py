from rag.get_api_response import get_response as run_rag_pipeline

@tool
def rag_tool(query:str) -> str:
    """
    Use this tool to answer questions using internal company documents.
    It performs semantic search + LLM reasoning and returns a grounded response.
    """

    print(f"[RAG TOOL] Query: {query}")
    result = run_rag_pipeline(query)
    return result


