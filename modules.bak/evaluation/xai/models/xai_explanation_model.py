# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

import logging

logger = logging.getLogger("xai_explanation")

def log_gpt_cost(content: str):
    try:
        logger.info(f"[XAI] GPT 응답 길이: {len(content)}자")
        # TODO: 실제 비용 계산 및 로그 저장 로직 추가
    except Exception as e:
        logger.error(f"[XAI] 비용 로깅 실패: {e}")


