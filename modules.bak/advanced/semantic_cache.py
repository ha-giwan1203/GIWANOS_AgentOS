
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 모델 및 인덱스 경로 설정
model = SentenceTransformer('all-MiniLM-L6-v2')
index_path = 'C:/giwanos/vector_cache/local_index.faiss'
cache_data_path = 'C:/giwanos/vector_cache/cache_responses.npy'

def load_index():
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        logging.info('Faiss index loaded successfully.')
        return index
    else:
        logging.error('Faiss index file not found.')
        return None

def check_cache(query, threshold=0.8):
    index = load_index()
    if index is None:
        return None

    query_embedding = model.encode([query])
    D, I = index.search(query_embedding, k=1)

    if D[0][0] < (1 - threshold):
        if os.path.exists(cache_data_path):
            cached_responses = np.load(cache_data_path, allow_pickle=True).item()
            response = cached_responses.get(int(I[0][0]), None)
            if response:
                logging.info(f'Cache hit: {response}')
                return response
        else:
            cached_responses = {}
            np.save(cache_data_path, cached_responses)
            logging.info('Cache file created (initial empty cache).')

    logging.info('Cache miss')
    return None

def update_cache(new_query, new_response):
    embeddings = model.encode([new_query])
    index = load_index()
    if index:
        index.add(embeddings)
        faiss.write_index(index, index_path)
        if os.path.exists(cache_data_path):
            cached_responses = np.load(cache_data_path, allow_pickle=True).item()
        else:
            cached_responses = {}
        cached_responses[len(cached_responses)] = new_response
        np.save(cache_data_path, cached_responses)
        logging.info('Cache updated successfully.')

def main():
    query = "GIWANOS 시스템 자동화의 장점은 무엇인가요?"
    response = check_cache(query)
    if not response:
        response = "GIWANOS 시스템 자동화는 운영 효율성, 비용 절감, 지속적 성능 향상 등의 장점이 있습니다."
        update_cache(query, response)
        logging.info(f'New response cached: {response}')

if __name__ == "__main__":
    main()


