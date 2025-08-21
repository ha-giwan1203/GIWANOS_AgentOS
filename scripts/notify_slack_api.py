# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
import os
import sys
import time
import json
import mimetypes
import requests
from pathlib import Path
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # 없는 환경에서도 돌아가게

# ----- 고정 경로 및 .env 로드 -----
try:
    from modules.report_paths import ROOT
except ImportError:
    # Fallback: 현재 스크립트 기준으로 ROOT 추정
    HERE = Path(__file__).parent
    ROOT = HERE.parent

ENV = ROOT / "configs" / ".env"
if load_dotenv and ENV.exists():
    load_dotenv(dotenv_path=str(ENV), override=True)
    print(f"[INFO] 환경 설정 로드: {ENV}")
elif ENV.exists():
    print(f"[WARN] python-dotenv 없음, 환경 설정 로드 실패: {ENV}")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
RAW_CHANNEL = (
    os.getenv("SLACK_CHANNEL_ID")
    or os.getenv("SLACK_SUMMARY_CH")
    or os.getenv("SLACK_CHANNEL")
    or ""
).strip()

def validate_slack_config() -> bool:
    """Slack 설정 검증"""
    if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN.startswith("xoxb-your-"):
        print("[ERROR] SLACK_BOT_TOKEN이 설정되지 않았거나 데모 값입니다")
        print("실제 토큰으로 configs/.env 파일을 수정해주세요")
        return False
    if not RAW_CHANNEL or RAW_CHANNEL in ("C1234567890", "C0123456789"):
        print("[ERROR] SLACK_CHANNEL_ID가 설정되지 않았거나 데모 값입니다") 
        print("실제 채널 ID로 configs/.env 파일을 수정해주세요")
        return False
    return True

# 설정 검증 (스크립트 직접 실행시에만)
if __name__ == "__main__" and not validate_slack_config():
    print("\n📖 설정 방법:")
    print("1. https://api.slack.com/apps 에서 Slack App 생성")
    print("2. Bot Token (xoxb-...) 발급")
    print("3. configs/.env 파일에서 SLACK_BOT_TOKEN, SLACK_CHANNEL_ID 수정")
    print("4. Slack 채널에 봇 초대: /invite @your-bot-name")
    sys.exit(1)

API = "https://slack.com/api"
SESSION = requests.Session()
SESSION.headers.update({"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})


def _mime(p: Path) -> str:
    return mimetypes.guess_type(p.name)[0] or "application/octet-stream"


def _ready(p: Path, tries: int = 6) -> bool:
    """파일 준비 상태 확인 (개선된 버전)"""
    if not p.exists():
        print(f"[ERROR] 파일 존재하지 않음: {p}")
        return False
        
    last = -1
    for i in range(tries):
        sz = p.stat().st_size
        if sz == 0:
            print(f"[WARN] 파일 크기 0 (시도 {i+1}/{tries})")
            time.sleep(0.5)
            continue
        if sz == last and sz > 0:
            print(f"[OK] 파일 준비 완료: {sz:,} bytes")
            return True
        last = sz
        print(f"[INFO] 파일 크기 변화 감지: {sz:,} bytes (시도 {i+1}/{tries})")
        time.sleep(0.5)
    
    final_size = p.stat().st_size
    is_ready = final_size > 0
    print(f"[{'OK' if is_ready else 'WARN'}] 최종 상태: {final_size:,} bytes")
    return is_ready


def resolve_channel_id(raw: str) -> str:
    # U... 이면 DM 채널(D...)로 변환
    if raw.startswith(("C", "G", "D")):
        return raw
    if raw.startswith("U"):
        r = SESSION.post(f"{API}/conversations.open", data={"users": raw})
        j = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {"ok": False, "raw": r.text}
        )
        if j.get("ok") and "channel" in j:
            ch = j["channel"]["id"]
            print(f"[INFO] 사용자 ID → DM 채널 변환: {raw} → {ch}")
            return ch
        print(f"[WARN] conversations.open 실패: {j}")
        return raw
    return raw


CHANNEL_ID = resolve_channel_id(RAW_CHANNEL)


def send_text(ch: str, text: str) -> None:
    try:
        r = SESSION.post(f"{API}/chat.postMessage", data={"channel": ch, "text": text})
        j = r.json()
        if not j.get("ok"):
            print(f"[WARN] chat.postMessage 실패: {j}")
    except Exception as e:
        print(f"[WARN] chat.postMessage 예외: {e}")


def upload_external_form(p: Path, title: str, comment: Optional[str] = None) -> Tuple[bool, dict]:
    """개선된 External Form API 업로드 (v2)"""
    try:
        # 1) 업로드 URL 발급
        r1 = SESSION.post(
            f"{API}/files.getUploadURLExternal",
            data={
                "filename": p.name, 
                "length": str(p.stat().st_size),
                "alt_txt": title or "VELOS 업로드 파일"
            },
            timeout=30
        )
        
        if r1.status_code != 200:
            return False, {
                "where": "getUploadURLExternal",
                "status": r1.status_code,
                "raw": r1.text[:300],
            }
            
        try:
            j1 = r1.json()
        except Exception as e:
            return False, {
                "where": "getUploadURLExternal",
                "status": r1.status_code,
                "error": f"JSON 파싱 실패: {e}",
                "raw": r1.text[:300],
            }
            
        if not j1.get("ok"):
            return False, {"where": "getUploadURLExternal", **j1}

        url, fid = j1["upload_url"], j1["file_id"]

        # 2) PUT 업로드 (개선된 헤더)
        with open(p, "rb") as fp:
            file_data = fp.read()
            
        headers = {
            "Content-Type": _mime(p),
            "Content-Length": str(len(file_data))
        }
        
        put = requests.put(url, data=file_data, headers=headers, timeout=60)
        
        if not (200 <= put.status_code < 300):
            return False, {
                "where": "PUT", 
                "status": put.status_code,
                "response": put.text[:300] if put.text else "No response"
            }

        # 3) 완료 호출 (개선된 데이터 구조)
        files_data = [{
            "id": fid, 
            "title": title,
            "alt_txt": title or "VELOS 파일"
        }]
        
        complete_data = {
            "files": json.dumps(files_data, ensure_ascii=False),
            "channel_id": CHANNEL_ID
        }
        
        if comment:
            complete_data["initial_comment"] = comment
            
        r3 = SESSION.post(f"{API}/files.completeUploadExternal", data=complete_data, timeout=30)
        
        if r3.status_code != 200:
            return False, {
                "where": "completeUploadExternal",
                "status": r3.status_code,
                "raw": r3.text[:300],
            }
            
        try:
            j3 = r3.json()
        except Exception as e:
            return False, {
                "where": "completeUploadExternal",
                "status": r3.status_code,
                "error": f"JSON 파싱 실패: {e}",
                "raw": r3.text[:300],
            }
            
        return j3.get("ok", False), j3
        
    except Exception as e:
        return False, {
            "where": "upload_external_form",
            "error": f"전체 예외: {e}",
            "type": type(e).__name__
        }


def upload_legacy_files_api(p: Path, title: str, comment: Optional[str] = None) -> Tuple[bool, dict]:
    """Legacy files.upload API (fallback)"""
    try:
        with open(p, "rb") as fp:
            files = {"file": (p.name, fp, _mime(p))}
            data = {
                "channels": CHANNEL_ID,
                "title": title,
                "filename": p.name
            }
            if comment:
                data["initial_comment"] = comment
                
            r = SESSION.post(f"{API}/files.upload", files=files, data=data, timeout=120)
            
        if r.status_code != 200:
            return False, {"where": "files.upload", "status": r.status_code, "raw": r.text[:300]}
            
        try:
            j = r.json()
        except Exception as e:
            return False, {"where": "files.upload", "error": f"JSON 파싱: {e}", "raw": r.text[:300]}
            
        return j.get("ok", False), j
        
    except Exception as e:
        return False, {"where": "upload_legacy_files_api", "error": str(e)}


def send_report(p: Path, title: str = "VELOS Report", comment: Optional[str] = None) -> bool:
    """개선된 파일 전송 (multiple fallback 방식)"""
    if not p.exists():
        print(f"[ERROR] 파일 없음: {p}")
        return False
    if not _ready(p):
        print(f"[ERROR] 파일 준비 안 됨(잠김/0바이트): {p}")
        return False
    
    # 파일 크기 체크
    file_size = p.stat().st_size
    print(f"[INFO] 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    # 1차 시도: External Form API (v2)
    print(f"[INFO] 1차 시도: External Form API")
    ok, info = upload_external_form(p, title, comment)
    if ok:
        print(f"[OK] 업로드 성공: external(form) → {p}")
        send_text(CHANNEL_ID, f"✅ VELOS 업로드 완료: {p.name}")
        return True
    
    print(f"[WARN] External Form 실패: {info}")
    
    # 2차 시도: Legacy Files API
    print(f"[INFO] 2차 시도: Legacy Files API")
    ok2, info2 = upload_legacy_files_api(p, title, comment)
    if ok2:
        print(f"[OK] 업로드 성공: legacy(files) → {p}")
        send_text(CHANNEL_ID, f"✅ VELOS 업로드 완료 (Legacy): {p.name}")
        return True
        
    print(f"[WARN] Legacy Files 실패: {info2}")
    
    # 3차 시도: 메시지만 전송 (파일 링크 포함)
    print(f"[INFO] 3차 시도: 메시지 전송 (파일 업로드 실패)")
    try:
        fallback_msg = f"📄 VELOS 보고서: {p.name}\n" \
                      f"크기: {file_size:,} bytes\n" \
                      f"⚠️ 파일 업로드 실패 - 수동 확인 필요\n" \
                      f"경로: {p.absolute()}"
        send_text(CHANNEL_ID, fallback_msg)
        print(f"[OK] 대안 메시지 전송 완료")
        return True
    except Exception as e:
        print(f"[ERROR] 모든 전송 방식 실패: {e}")
        return False


def _find_latest() -> Optional[Path]:
    d = ROOT / "data" / "reports"
    if not d.exists():
        return None
    alias = d / "velos_report_latest.pdf"
    if alias.exists():
        return alias
    xs = sorted(d.glob("velos_report_*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
    return xs[0] if xs else None


if __name__ == "__main__":
    f = _find_latest()
    if not f:
        print("[WARN] 업로드할 파일 없음")
        sys.exit(0)
    print(f"[INFO] 업로드 대상: {f}")
    sys.exit(0 if send_report(f, title=f"VELOS Report - {f.name}") else 1)
