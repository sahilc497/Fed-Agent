import sys
import numpy as np
from sentence_transformers import SentenceTransformer

def main():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Loading cached model: {model_name} with local_files_only=True...")
    model = SentenceTransformer(model_name, local_files_only=True)
    
    doc1 = "Several sales opportunities are awaiting approval from the finance department."
    query1 = "Which deals are waiting for financial approval?"
    query_unrelated = "What is the policy for annual vacation days in human resources?"
    
    emb_doc1 = model.encode(doc1, normalize_embeddings=True)
    emb_query1 = model.encode(query1, normalize_embeddings=True)
    emb_unrelated = model.encode(query_unrelated, normalize_embeddings=True)
    
    sim_relevant = float(np.dot(emb_doc1, emb_query1))
    sim_unrelated = float(np.dot(emb_doc1, emb_unrelated))
    
    print(f"Embedding dimension: {len(emb_doc1)}")
    print(f"Similarity (Semantic Match): {sim_relevant:.4f}")
    print(f"Similarity (Unrelated): {sim_unrelated:.4f}")
    assert sim_relevant > sim_unrelated, "Semantic query did not outrank unrelated query!"
    print("SUCCESS: Genuine semantic model verified offline!")

if __name__ == "__main__":
    main()
