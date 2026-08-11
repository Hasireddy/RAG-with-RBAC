from langchain_core.documents import Document
from app.rag.semantic_docs_search import semantic_search


# Tests for Role Based Access based on the department
# User's department-> semantic search -> vector store gives candidate documents -> Remove weak matches -> Remove unauthorized departments -> Keep authorized documents -> Return context

# Fake vector store for testing
class FakeVectorStore:
    def __init__(self, results):
        self.results = results

    def similarity_search_with_score(self, query, k):
        return self.results


# AUTHORIZATION
# Test for finance documents access related to finance department employee
def test_finance_user_can_access_finance_document():
    # Arrange
    document = Document(
        page_content="Finance expense policy",
        metadata={
            "department": "Finance",
            "source": "finance.md",
            "Header3": "Expenses"
        },
    )


    vector_store = FakeVectorStore([
        (document, 0.3)
    ])

    # Act
    result = semantic_search(
        vector_store=vector_store,
        query="Why did employee benefits and HR costs increase by 10% during the fiscal year?",
        departments=["Finance"]
    )


    # Assert
    assert result["status"] == "SUCCESS"
    assert len(result["documents"]) == 1
    assert result["documents"][0].metadata["department"] == "Finance"


# AUTHORIZATION
# Test for Engineering document access to Finance department employee
def test_finance_user_cannot_access_engineering_document():
    document = Document(
        page_content="Engineering deployment policy",
        metadata={
            "department": "Engineering",
            "source": "engineering.md",
            "Header3": "Deployment"
        },
    )

    vector_store = FakeVectorStore([
        (document, 0.3)
    ])

    result = semantic_search(
        vector_store=vector_store,
        query="What is deployment policy?",
        departments=["Finance"],
    )
    assert result["status"] == "UNAUTHORIZED"
    assert result["documents"] == []
    assert result["contexts"] == []
    assert result["context"] == ""


# AUTHORIZATION
# Test for General document access related to Finance department employee
def test_finance_user_can_access_general_document():
    document = Document(
        page_content="Company holiday policy",
        metadata={
            "department": "general",
            "source": "general.md",
            "Header3": "Holidays",
        }
    )

    vector_store = FakeVectorStore([
        (document, 0.3)
    ])

    result = semantic_search(
        vector_store=vector_store,
        query="What is the holiday policy?",
        departments=["Finance"],
    )

    assert result["status"] == "SUCCESS"
    assert len(result["documents"]) == 1
    assert result["documents"][0].metadata["department"] == "general"


# AUTHORIZATION
# Test RBAC filtering with multiple documents
#When the search returns a mixture of authorized and unauthorized documents, does RBAC correctly filter out every unauthorized document?
def test_finance_user_only_gets_authorized_documents():
    finance_document = Document(
        page_content="finance budget policy",
        metadata={
            "department": "Finance",
            "source": "finance.md",
            "Header3": "Budget",
        }
    )

    engineering_document = Document(
        page_content="Engineering deployment policy",
        metadata={
            "department": "Engineering",
            "source": "engineering.md",
            "Header3": "Deployment",
        },
    )

    marketing_document = Document(
        page_content="Marketing campaign policy",
        metadata={
            "department": "Marketing",
            "source": "marketing.md",
            "Header3": "Campaigns",
        },
    )

    general_document = Document(
        page_content="Company holiday policy",
        metadata={
            "department": "general",
            "source": "general.md",
            "Header3": "Holidays",
        },
    )

    vector_store = FakeVectorStore(
        [
            (finance_document, 0.2),
            (engineering_document, 0.3),
            (marketing_document, 0.4),
            (general_document, 0.5),
        ]
    )

    result = semantic_search(
        vector_store=vector_store,
        query="What are the company policies?",
        departments=["Finance"],
    )

    assert result["status"] == "SUCCESS"
    #print("STATUS:", result["status"])

    #print("DOCUMENTS:")

    #for doc in result["documents"]:
        #print(
            #doc.metadata.get("department"),
            #doc.metadata.get("source")
        #)

    assert len(result["documents"]) == 2

    departments = [
        doc.metadata["department"]
        for doc in result["documents"]
    ]

    assert "Finance" in departments
    assert "general" in departments

    assert "Engineering" not in departments
    assert "Marketing" not in departments




# AUTHORIZATION
# Test that Financial user can access multiple Finance documents at the same time.
def test_finance_user_can_access_multiple_finance_documents():
    # Arrange
    finance_document_1 = Document(
        page_content="Finance budget policy",
        metadata={
            "department": "Finance",
            "source": "budget.md",
            "Header3": "Budget",
        },
    )

    finance_document_2 = Document(
        page_content="Finance expense policy",
        metadata={
            "department": "Finance",
            "source": "expenses.md",
            "Header3": "Expenses",
        },
    )

    finance_document_3 = Document(
        page_content="Finance reporting policy",
        metadata={
            "department": "Finance",
            "source": "reporting.md",
            "Header3": "Reporting",
        },
    )

    vector_store = FakeVectorStore([
        (finance_document_1, 0.2),
        (finance_document_2, 0.4),
        (finance_document_3, 0.6),
    ])

    # Act
    result = semantic_search(
        vector_store=vector_store,
        query="What are the finance policies?",
        departments=["Finance"],
    )

    # Assert
    assert result["status"] == "SUCCESS"
    assert len(result["documents"]) == 3

    departments = [
        doc.metadata["department"]
        for doc in result["documents"]
    ]

    assert departments.count("Finance") == 3




# RELEVANCE THRESHOLD
# Test for documents with distance greater than 1.5(Not relevant enough and too weak documents are discarded)
def test_returns_not_found_when_no_relevant_documents():
    document = Document(
        page_content="Some unrelated information",
        metadata={
            "department": "Finance",
            "source": "unrelated.md",
            "Header3": "Other",
        },
    )

    vector_store = FakeVectorStore([
        (document, 1.8)
    ])

    result = semantic_search(
        vector_store=vector_store,
        query="What are the employee benefits?",
        departments=["Finance"],
    )

    assert result["status"] == "NOT_FOUND"
    assert result["documents"] == []
    assert result["contexts"] == []
    assert result["context"] == ""


# RELEVANCE THRESHOLD
# Test for documents exactly with threshold 1.5
# Code contains if distance > 1.5, continue. With distance 1.5 > 1.5, document should not be skipped
def test_document_at_distance_threshold_is_accepted():

    # Arrange
    document = Document(
        page_content="Finance policy",
        metadata={
            "department": "Finance",
            "source": "finance.md",
            "Header3": "Policy",
        },
    )

    vector_store = FakeVectorStore([
        (document, 1.5)
    ])

    # Act
    result = semantic_search(
        vector_store=vector_store,
        query="What is the finance policy?",
        departments=["Finance"],
    )

    # Assert
    assert result["status"] == "SUCCESS"
    assert len(result["documents"]) == 1
    assert result["documents"][0].metadata["department"] == "Finance"


# RELEVANCE THRESHOLD
# Test with distance 1.50001 above threshold, documents should be ignored
# Even though this is a Finance document and the user is a Finance user, it should still be rejected because the semantic match is too weak.
def test_document_above_distance_threshold_is_rejected():

    # Arrange
    document = Document(
        page_content="Finance policy",
        metadata={
            "department": "Finance",
            "source": "finance.md",
            "Header3": "Policy",
        },
    )

    vector_store = FakeVectorStore([
        (document, 1.5001)
    ])

    # Act
    result = semantic_search(
        vector_store=vector_store,
        query="What is the finance policy?",
        departments=["Finance"],
    )

    # Assert
    assert result["status"] == "NOT_FOUND"
    assert result["documents"] == []
    assert result["contexts"] == []
    assert result["context"] == ""


# RELEVANCE THRESHOLD- Unauthorized and Weak documents
# Test for relevant(distance < 1.5) but unauthorized(Document does not belong to the employee department) and weak document(distance > 1.5) but belongs to employee department.
# Both documents must be ignored
# The Engineering document is relevant(distance < 1.5), but the user isn't allowed to see it.
# The weak Finance document is simply ignored.
def test_returns_unauthorized_when_relevant_document_is_not_allowed():
    engineering_document = Document(
        page_content="Engineering deployment policy",
        metadata={
            "department": "Engineering",
            "source": "engineering.md",
            "Header3": "Deployment",
        },
    )

    weak_finance_document = Document(
        page_content="Old finance information",
        metadata={
            "department": "Finance",
            "source": "old_finance.md",
            "Header3": "Archive",
        },
    )

    vector_store = FakeVectorStore([
        (engineering_document, 0.3),
        (weak_finance_document, 1.8),
    ])

    result = semantic_search(
        vector_store=vector_store,
        query="What is the engineering deployment policy?",
        departments=["Finance"],
    )

    assert result["status"] == "UNAUTHORIZED"
    assert result["documents"] == []
    assert result["contexts"] == []
    assert result["context"] == ""


# EDGE CASES FOR Document MISSING DEPARTMENT
# Test for missing user department should be treated as unauthorized
# The document has no department
def test_document_without_department_is_not_authorized():
    document = Document(
        page_content="Document without department",
        metadata={
            "source": "unknown.md",
            "Header3": "Unknown",
        },
    )

    vector_store = FakeVectorStore([
            (document, 0.3)
        ])

    result = semantic_search(
        vector_store=vector_store,
        query="What is this document about?",
        departments=["Finance"],
    )

    assert result["status"] == "UNAUTHORIZED"
    assert result["documents"] == []
    assert result["contexts"] == []
    assert result["context"] == ""


# User with nonexistent department
# Test to check if user provides a department that doesn't exist
def test_user_with_nonexistent_department_gets_unauthorized():

    # Arrange
    finance_document = Document(
        page_content="Finance budget policy",
        metadata={
            "department": "Finance",
            "source": "finance.md",
            "Header3": "Budget",
        },
    )

    vector_store = FakeVectorStore([
        (finance_document, 0.3)
    ])

    # Act
    result = semantic_search(
        vector_store=vector_store,
        query="What is the finance budget policy?",
        departments=["NonExistentDepartment"],
    )

    # Assert
    assert result["status"] == "UNAUTHORIZED"
    assert result["documents"] == []
    assert result["contexts"] == []
    assert result["context"] == ""



# user with no department
# Test to check that User with no department can access general documents
def test_user_with_no_department_can_only_access_general():

    # Arrange
    finance_document = Document(
        page_content="Finance budget policy",
        metadata={
            "department": "Finance",
            "source": "finance.md",
            "Header3": "Budget",
        },
    )

    general_document = Document(
        page_content="Company holiday policy",
        metadata={
            "department": "general",
            "source": "general.md",
            "Header3": "Holidays",
        },
    )

    vector_store = FakeVectorStore([
        (finance_document, 0.3),
        (general_document, 0.4),
    ])

    # Act
    result = semantic_search(
        vector_store=vector_store,
        query="What are the company policies?",
        departments=[],
    )

    # Assert
    assert result["status"] == "SUCCESS"
    assert len(result["documents"]) == 1

    departments = [
        doc.metadata["department"]
        for doc in result["documents"]
    ]

    assert "general" in departments
    assert "Finance" not in departments



