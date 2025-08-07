"""
##############################################################
# VELOS OPERATION DECLARATION
# ▶ 파일명 : velos_rag_poc.py      (⚠ 절대 변경 금지)
# ▶ 경   로 : C:/giwanos/scripts/
# ▶ 목   적 : Qdrant + LangChain 기반 “자동 기억 회수” PoC
# ▶ 요   약 : 외부 저장된 문서를 임베딩→저장→검색→LLM 프롬프트
#              로 주입하는 완전 자동 RAG 파이프라인을 검증한다.
# ▶ 핵심 규칙
#   1) 파일명·경로 고정   2) 실행 전·후 자체 검증 필수
#   3) 오류 발생 시 예외 로깅 후 종료
##############################################################
"""

import os, sys, json, time, logging
from typing import List, Dict

# ──────────────────────────────
# ① 경로 셋업 (모듈 충돌 방지)
# ──────────────────────────────
ROOT_DIR = r"C:/giwanos"
sys.path.append(ROOT_DIR)

# ──────────────────────────────
# ② 로깅 초기화
# ──────────────────────────────
LOG_PATH = os.path.join(ROOT_DIR, "data", "logs", "rag_poc_log.txt")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s",
                    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                              logging.StreamHandler(sys.stdout)])

# ──────────────────────────────
# ③ 외부 라이브러리
# ──────────────────────────────
try:
    from qdrant_client import QdrantClient
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Qdrant as LC_Qdrant
    from langchain.memory import ConversationVectorStoreTokenBufferMemory
    from langchain.chat_models import ChatOpenAI
    from langchain.chains import ConversationalRetrievalChain
except ImportError as e:
    logging.error("필수 라이브러리가 없습니다. requirements_rag.txt 설치 후 다시 실행하십시오.")
    raise e

# ──────────────────────────────
# ④ 설정
# ──────────────────────────────
QDRANT_URL = os.getenv("VEL_QDRANT_URL", "http://127.0.0.1:6333")
COLLECTION = "velos-memory"
EMBED_MODEL = "jhgan/ko-sbert-sts"

# ──────────────────────────────
# ⑤ 초기화 함수
# ──────────────────────────────
def init_vector_store():
    client = QdrantClient(url=QDRANT_URL)
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vs = LC_Qdrant(client=client,
                   collection_name=COLLECTION,
                   embeddings=embeddings)
    return vs

# ──────────────────────────────
# ⑥ 자체 검증 루틴
# ──────────────────────────────
def self_validate(vs):
    """
    1) 더미 문서 2개 upsert
    2) 쿼리로 회수되는지 테스트
    """
    docs = [
        {"id": "mem1", "text": "벡터 데이터베이스는 검색 강화 생성(RAG)의 핵심이다."},
        {"id": "mem2", "text": "VELOS 시스템은 GPT-4o 기반 고도화 AI 운영 플랫폼이다."}
    ]
    # upsert
    for d in docs:
        vs.add_texts(texts=[d["text"]], metadatas=[{"source": d["id"]}])

    # 검색
    hits = vs.similarity_search("RAG 파이프라인의 핵심은 벡터 DB입니다.", k=2)
    assert len(hits) >= 1, "자체 검증 실패: 유사 문서 회수가 0개입니다."
    logging.info("✅ 자체 검증 통과 - 유사 문서 %d개 회수", len(hits))

# ──────────────────────────────
# ⑦ 대화 루프
# ──────────────────────────────
def run_chat(vs):
    memory = ConversationVectorStoreTokenBufferMemory(
        vectorstore=vs,
        k=6,
        max_token_limit=2000,
    )
    llm = ChatOpenAI(model_name="gpt-4o-mini",
                     temperature=0.2,
                     request_timeout=30)
    rag_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vs.as_retriever(search_kwargs={"k": 6}),
        memory=memory,
    )
    logging.info("🚀 Velos RAG PoC 대화 루프 시작 (종료: Ctrl+C)")
    while True:
        try:
            question = input("YOU> ").strip()
            if not question:
                continue
            start = time.time()
            answer = rag_chain({"question": question})["answer"]
            elapsed = time.time() - start
            print(f"VEL> {answer}\n   (latency {elapsed*1000:.1f} ms)\n")
        except KeyboardInterrupt:
            print("\n[종료 요청] 안녕히 가세요.")
            break
        except Exception as e:
            logging.exception("대화 루프 오류: %s", e)
            print("⚠ 오류가 발생했습니다. 로그를 확인하세요.")

# ──────────────────────────────
# ⑧ 메인
# ──────────────────────────────
if __name__ == "__main__":
    try:
        vectordb = init_vector_store()
        self_validate(vectordb)
        run_chat(vectordb)
    except Exception:
        logging.exception("PoC 전체 실패 – 세부 로그 참조")
        sys.exit(1)
