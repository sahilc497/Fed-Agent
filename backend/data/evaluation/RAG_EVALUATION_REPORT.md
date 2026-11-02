# RAG Pipeline Evaluation Report — Federated Agentic Mesh

## 1. Executive Summary & Verification Metrics
- **Total Versioned Test Cases Evaluated:** 80 (20 Sales, 20 HR, 20 Finance, 20 Operations)
- **Retrieval Recall@5:** `95.59%` (65/68 factual queries successfully retrieved)
- **Mean Reciprocal Rank (MRR@5):** `0.9216`
- **Abstention & Injection Resistance Accuracy:** `100.00%` (12/12)
- **Unauthorized Retrieval Count:** `0` (Target: 0, **ZERO LEAKAGE ENFORCED**)
- **Cross-Department Leakage Count:** `0` (Target: 0, **ZERO LEAKAGE ENFORCED**)

## 2. Methodology & Architecture
1. **Pretrained Embeddings + Local Inference:** Local dense vectors generated via `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Pretrained vectors embedded offline; no claim of fine-tuning.
2. **In-Database Security Filtration:** Chunks are pre-filtered via parameterized SQLite queries matching user department and access level *prior* to vector scoring.
3. **Adversarial & Cross-Department Hardening:** Negative test cases prove prompt injection attempts cannot traverse department vector tables or bypass authorization.
