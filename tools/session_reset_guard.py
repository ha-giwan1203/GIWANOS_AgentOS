# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
import os
import re
import subprocess
import sys

MIN_LEN = 300  # 이보다 짧으면 의심
MUST_KEYS = ["VELOS_ROOT", "절대경로 금지", "최소 수정", "PR 브랜치"]


def needs_reinject(text):
    if len(text) < MIN_LEN:
        return True
    text_low = text.lower()
    miss = [k for k in MUST_KEYS if k.lower() not in text_low]
    return len(miss) >= 2


def rebuild_context_pack():
    import os
    default_root = "/home/user/webapp" if os.name == "posix" else r"C:\giwanos"
    root = os.getenv("VELOS_ROOT", default_root)
    
    script_path = os.path.join(root, "tools", "make_context_pack.py")
    doc_path = os.path.join(root, "docs", "CONTEXT_PACK.md")
    
    subprocess.run(["python", script_path], check=False)
    with open(doc_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    # stdin으로 GPT 응답을 받는다고 가정
    text = sys.stdin.read()
    if needs_reinject(text):
        cp = rebuild_context_pack()
        sys.stdout.write("<<CONTEXT_REINJECT>>\n")
        sys.stdout.write(cp)
        sys.stdout.write("\n\n")
        sys.stdout.write("<<ORIGINAL_REPLY>>\n")
        sys.stdout.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
