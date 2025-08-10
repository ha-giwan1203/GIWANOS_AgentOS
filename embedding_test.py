from sentence_transformers import SentenceTransformer

m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
vec = m.encode(["VELOS 임베딩 정상 동작 테스트"])
print("임베딩 차원:", vec.shape)
print("첫 5개 값:", vec[0][:5])
