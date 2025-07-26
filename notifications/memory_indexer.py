import os
import glob
import json
import numpy as np
import faiss
from dotenv import load_dotenv
import openai

# .env에서 API 키 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
openai.api_key = api_key

# 설정 디렉터리 및 벡터 디렉터리 경로
BASE_DIR = os.getcwd()
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
VECTOR_DIR = os.path.join(CONFIG_DIR, 'vector_index')
EMBEDDING_MODEL = 'text-embedding-ada-002'

# 벡터 디렉터리 생성
os.makedirs(VECTOR_DIR, exist_ok=True)

# 1) 회고 마크다운 파일 수집
REFLECT_DIR = os.path.join(BASE_DIR, 'reflections')
md_files = glob.glob(os.path.join(REFLECT_DIR, '*.md'))
if not md_files:
    raise FileNotFoundError(f"회고 문서(.md)가 없습니다: {REFLECT_DIR}")

docs = []
for md in md_files:
    with open(md, 'r', encoding='utf-8') as f:
        docs.append(f.read().strip())

# 2) 임베딩 생성 (OpenAI v1+)
embeddings = []
for doc in docs:
    resp = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=doc
    )
    emb = resp.data[0].embedding
    embeddings.append(np.array(emb, dtype='float32'))

# 3) FAISS 인덱스 빌드
if not embeddings:
    raise ValueError("생성된 임베딩이 없습니다.")
dim = embeddings[0].shape[0]
index = faiss.IndexFlatL2(dim)
index.add(np.vstack(embeddings))

# 4) 인덱스 및 매핑 파일 저장
index_path = os.path.join(VECTOR_DIR, 'index.faiss')
faiss.write_index(index, index_path)

docs_path = os.path.join(VECTOR_DIR, 'docs.json')
with open(docs_path, 'w', encoding='utf-8') as f:
    json.dump(docs, f, ensure_ascii=False, indent=2)

print(f"✅ 벡터 인덱스 생성 완료: {index_path}")
print(f"✅ 문서 매핑 파일 생성 완료: {docs_path}")
