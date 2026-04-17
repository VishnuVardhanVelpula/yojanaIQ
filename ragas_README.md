# YojanaIQ RAGAS Integration 

This suite enables automated evaluation of the YojanaIQ RAG pipeline using the [RAGAS >0.2.0 framework](https://docs.ragas.io/). It assesses factual grounding, retrieval accuracy, and how well context is utilized.

## Installation
Run this to ensure all strict dependencies are installed:
```bash
pip install -r requirements_fix10.txt
```

## How to Run

**1. Baseline Evaluation (Your 'Before' State)**
```bash
python evaluate.py --label fix6_fix8_combined
```

**2. Subsequent Evaluation**
When you implement future changes (like Fix 7 or Fix 9), just re-run with a new label:
```bash
python evaluate.py --label fix7_updated
```

## How to Read the Output (data/ragas_results.csv)
Your `ragas_results.csv` file automatically accumulates metric scores. You can directly copy this file's rows into your IEEE paper's results table.

**The Metrics in Plain English:**
- **Faithfulness**: Did the LLM make things up? (1.0 = highly factual, based purely on retrieved context).
- **Answer Relevancy**: Did the answer actually address the user's question, or did it go off on a tangent? (1.0 = highly concise and relevant).
- **Context Precision**: Did the retriever pull the exact paragraph needed, and was it ranked inside the top chunks? (1.0 = perfect ranking of relevant contexts).
- **Mean**: The mathematical average of the above three scores, offering a quick "overall RAG health" indicator.
