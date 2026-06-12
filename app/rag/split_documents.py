from langchain_text_splitters import MarkdownHeaderTextSplitter
from .load_documents import load_documents



# Step2: Split the loaded and parsed document into chunks
def split_docs_chunks():
    """Splits documents into chunks. or example, a markdown file is organized by headers.
    Creating chunks within specific header groups is an intuitive idea.
    To address this challenge, we can use MarkdownHeaderTextSplitter.
    This will split a markdown file by a specified set of headers."""

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    docs = load_documents()
    #print(f"Loaded docs: {len(docs)}")

    all_chunks = []
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=True)

    for doc in docs:
        md_header_splits = markdown_splitter.split_text(doc.page_content)

        for chunk in md_header_splits:
            base_metadata = dict(doc.metadata or {})
            chunk_metadata = dict(chunk.metadata or {})

            merged_metadata = {
                **base_metadata,
                **chunk_metadata,
                "department": base_metadata.get("department", "general")
            }

            chunk.metadata = merged_metadata
            all_chunks.append(chunk)

    #print(f"Total chunks created: {len(all_chunks)}")

    return all_chunks


#chunks = split_docs_chunks()
#print(chunks[:2])

"""Document(
    page_content="The specific body text located underneath a secondary heading...",
    metadata={
        'source': 'E:\\masterschool\\...\\resources\\data\\finance\\policies.md',
        'department': 'finance',
        'Header 1': 'Company Overview',
        'Header 2': 'Financial Policies'
    }
)"""


