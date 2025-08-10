
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(texts):
    embeddings = model.encode(texts)
    logging.info('Embeddings generated successfully.')
    return embeddings

def save_embeddings(embeddings, filepath='C:/giwanos/vector_cache/embeddings.npy'):
    np.save(filepath, embeddings)
    logging.info(f'Embeddings saved to {filepath}.')

def create_or_update_index(embeddings, index_path='C:/giwanos/vector_cache/local_index.faiss'):
    dimension = embeddings.shape[1]
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        logging.info('Existing Faiss index loaded.')
    else:
        index = faiss.IndexFlatL2(dimension)
        logging.info('New Faiss index created.')
        
    index.add(embeddings)
    faiss.write_index(index, index_path)
    logging.info(f'Index updated and saved to {index_path}.')

def main():
    texts = [
        "GIWANOS 시스템은 자동화를 통해 운영 효율을 극대화합니다.",
        "Adaptive Reasoning을 통해 시스템의 판단력을 향상시킵니다.",
        "로컬 캐싱은 API 호출 비용을 줄이는 데 도움이 됩니다."
    ]
    
    embeddings = generate_embeddings(texts)
    save_embeddings(embeddings)
    create_or_update_index(embeddings)

if __name__ == "__main__":
    main()


