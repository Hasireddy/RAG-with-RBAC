import csv
import os
from datetime import datetime

METRICS_CSV_PATH = "rag_metrics.csv"
RAGAS_METRIC_NAMES = ["faithfulness", "answer_relevancy", "nv_context_relevance", "nv_response_groundedness"]


def log_metrics_to_csv(trace_id: str, session_id: str, emp_name: str, question: str, scores_df):
    file_exists = os.path.exists(METRICS_CSV_PATH)

    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "trace_id": trace_id,
        "session_id": session_id,
        "employee": emp_name,
        "question": question,
    }

    for metric in RAGAS_METRIC_NAMES:
        if metric in scores_df.columns:
            value = scores_df[metric][0]
            row[metric] = round(float(value), 4) if value == value else None  # None for NaN

    with open(METRICS_CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)