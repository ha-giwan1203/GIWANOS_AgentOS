
import numpy as np

def enhanced_cot_evaluation(chunk, query):
    relevance_score = np.random.uniform(0.5, 1.0) if query in chunk else np.random.uniform(0, 0.5)
    length_penalty = min(len(chunk) / 100, 1)
    final_score = relevance_score * length_penalty
    return final_score

def evaluate_and_rerank_enhanced(chunks, query):
    scored_chunks = []
    for chunk in chunks:
        score = enhanced_cot_evaluation(chunk, query)
        scored_chunks.append((chunk, score))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return scored_chunks
