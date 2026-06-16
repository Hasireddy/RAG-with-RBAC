from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    ContextRelevance,
    ContextRecall,
    ResponseGroundedness,
)
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("API_KEY is missing in environment variables")

llm = LangchainLLMWrapper(
    ChatOpenAI(
        model="gpt-5-mini",
        api_key=api_key
    )
)

embeddings = LangchainEmbeddingsWrapper(
    OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key
    )
)

# Metrics (base)
context_relevance = ContextRelevance(llm=llm)
context_recall = ContextRecall(llm=llm)
response_groundedness = ResponseGroundedness(llm=llm)

answer_relevancy.llm = llm
answer_relevancy.embeddings = embeddings
faithfulness.llm = llm


def evaluate_rag_response(question: str, answer: str, contexts: list[str], reference: str = None):

    try:
        contexts = [str(c) for c in contexts]

        # Base dataset (always valid)
        data = {
            "user_input": [question],
            "response": [answer],
            "retrieved_contexts": [contexts],
        }

        # Base metrics (no reference needed)
        metrics = [
            faithfulness,
            answer_relevancy,
            #context_relevance,
            #response_groundedness,
        ]

        # Add reference + context_recall ONLY if available
        if reference is not None and reference.strip() != "":
            data["reference"] = [reference]
            metrics.append(context_recall)

        dataset = Dataset.from_dict(data)

        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
            run_config=RunConfig(
                max_retries=5,
                max_wait=60,
                timeout=120,
            )
        )

        return result

    except Exception as e:
        print(f"[RAGAS ERROR] {e}")
        return None