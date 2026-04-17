import json
import argparse
import os
import time
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from rag import answer_query
from ragas import evaluate, EvaluationDataset
from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


def run_evaluation(label: str):
    print(f"\nStarting RAGAS Evaluation — Label: {label}")

    with open("data/ragas_testset.json", "r", encoding="utf-8") as f:
        testset = json.load(f)
    print(f"Loaded {len(testset)} test questions.\n")

    dataset_rows = []

    for i, item in enumerate(testset):
        print(f"[{i+1}/{len(testset)}] Querying: {item['question']}")
        try:
            result = answer_query(item["user_profile"], item["question"])
            answer = result.get("answer", "")
            chunks = result.get("retrieved_chunks", [])
            contexts = [c.get("text", "") for c in chunks if c.get("text", "").strip()]
            if not contexts:
                contexts = ["No context retrieved."]
        except Exception as e:
            print(f"  ERROR on question {i+1}: {e}")
            answer = ""
            contexts = ["No context retrieved."]

        dataset_rows.append({
            "user_input":          item["question"],
            "response":            answer,
            "retrieved_contexts":  contexts,
            "reference":           item["ground_truth"]
        })

        time.sleep(15)

    print("\nAll 20 queries done. Running RAGAS judges...\n")

    eval_dataset = EvaluationDataset.from_list(dataset_rows)

    judge_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.environ["GOOGLE_API_KEY"]
    )
    judge_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.environ["GOOGLE_API_KEY"]
    )

    metrics = [
        Faithfulness(llm=judge_llm),
        AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings),
        ContextPrecision(llm=judge_llm),
    ]

    results = evaluate(
        dataset=eval_dataset,
        metrics=metrics,
    )

    df = results.to_pandas()
    df = df.fillna(0.0)

    f_score  = round(float(df["faithfulness"].mean())      if "faithfulness"      in df.columns else 0.0, 3)
    ar_score = round(float(df["answer_relevancy"].mean())  if "answer_relevancy"  in df.columns else 0.0, 3)
    cp_score = round(float(df["context_precision"].mean()) if "context_precision" in df.columns else 0.0, 3)
    mean_score = round((f_score + ar_score + cp_score) / 3, 3)

    print(f"Faithfulness:      {f_score}")
    print(f"Answer Relevancy:  {ar_score}")
    print(f"Context Precision: {cp_score}")
    print(f"Mean:              {mean_score}\n")

    csv_path = "data/ragas_results.csv"
    new_row = pd.DataFrame([{
        "label":              label,
        "timestamp":          pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "faithfulness":       f_score,
        "answer_relevancy":   ar_score,
        "context_precision":  cp_score,
        "mean":               mean_score
    }])

    if os.path.exists(csv_path):
        new_row.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        new_row.to_csv(csv_path, mode="w", header=True, index=False)

    print(f"Results saved to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="e.g. fix6_fix8_combined")
    args = parser.parse_args()
    run_evaluation(args.label)