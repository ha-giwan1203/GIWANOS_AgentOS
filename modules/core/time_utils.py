# ================= VELOS 운영 철학 선언문 =================
# - 단일 시간 원천(UTC)만 저장한다. 표시용은 최종 단계에서만 변환한다.
# - 경과 시간은 벽시계가 아닌 monotonic()으로 계산한다.
# - 파일명 변경 금지, 경로 고정, 제공 전 자가 검증 필수.
# =========================================================
from datetime import datetime, timezone, timedelta
import time as _t

KST = timezone(timedelta(hours=9))

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso_utc(dt: datetime | None = None) -> str:
    dt = dt or now_utc()
    return dt.astimezone(timezone.utc).isoformat()

def now_kst() -> datetime:
    return now_utc().astimezone(KST)

def monotonic() -> float:
    return _t.monotonic()

if __name__ == "__main__":
    print("UTC:", iso_utc())
    print("KST:", now_kst().isoformat())
