"""
기존 Chrome 쿠키를 Playwright 프로필에 복사하는 스크립트.
Chrome이 닫혀 있어야 합니다.
"""
import json
import shutil
import sqlite3
import sys
from pathlib import Path

CHROME_USER_DATA = Path.home() / "AppData/Local/Google/Chrome/User Data"
PROFILE_DIR = Path.home() / ".flow-collector-profile"
FLOW_DOMAIN = ".flow.team"


def find_chrome_profile():
    """Chrome 기본 프로필 경로 찾기"""
    default = CHROME_USER_DATA / "Default"
    if (default / "Cookies").exists():
        return default
    # Profile 1, 2... 시도
    for i in range(1, 10):
        p = CHROME_USER_DATA / f"Profile {i}"
        if (p / "Cookies").exists():
            return p
    return None


def copy_cookies():
    """Chrome에서 flow.team 쿠키를 Playwright 프로필로 복사"""

    chrome_profile = find_chrome_profile()
    if not chrome_profile:
        print("[ERROR] Chrome 프로필을 찾을 수 없습니다.")
        sys.exit(1)

    print(f"[INFO] Chrome 프로필: {chrome_profile}")

    # Chrome Cookies DB 복사 (원본 보호)
    cookies_db = chrome_profile / "Cookies"
    cookies_copy = Path.home() / ".flow-cookies-temp.db"

    try:
        shutil.copy2(cookies_db, cookies_copy)
    except PermissionError:
        print("[ERROR] Chrome을 먼저 닫아주세요! (Cookies 파일이 잠겨있음)")
        sys.exit(1)

    # SQLite에서 flow.team 쿠키 읽기
    conn = sqlite3.connect(str(cookies_copy))
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name, host_key, path, is_secure, expires_utc, is_httponly
            FROM cookies
            WHERE host_key LIKE '%flow.team%' OR host_key LIKE '%kakao%'
        """)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] 쿠키 읽기 실패: {e}")
        conn.close()
        cookies_copy.unlink(missing_ok=True)
        sys.exit(1)

    conn.close()
    cookies_copy.unlink(missing_ok=True)

    if not rows:
        print("[ERROR] flow.team 쿠키가 없습니다. Chrome에서 Flow.team에 로그인되어 있는지 확인하세요.")
        sys.exit(1)

    print(f"[INFO] flow.team/kakao 쿠키 {len(rows)}개 발견")
    print("[WARN] Chrome 쿠키는 암호화되어 있어서 값 복사는 안 됩니다.")
    print("[WARN] 대신 Chrome 프로필 전체를 Playwright용으로 복사합니다.")

    # Chrome 프로필 전체를 Playwright 프로필로 복사
    print(f"[INFO] Chrome 프로필 → Playwright 프로필 복사 중...")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # 필수 파일만 복사 (전체 복사하면 너무 큼)
    essential_files = ["Cookies", "Login Data", "Web Data", "Local State",
                       "Preferences", "Secure Preferences"]

    for fname in essential_files:
        src = chrome_profile / fname
        dst = PROFILE_DIR / "Default" / fname
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
                print(f"  복사: {fname}")
            except Exception as e:
                print(f"  건너뜀: {fname} ({e})")

    # Local Storage 복사
    ls_src = chrome_profile / "Local Storage"
    ls_dst = PROFILE_DIR / "Default" / "Local Storage"
    if ls_src.exists():
        if ls_dst.exists():
            shutil.rmtree(ls_dst)
        shutil.copytree(ls_src, ls_dst)
        print(f"  복사: Local Storage/")

    print(f"\n[DONE] Playwright 프로필 준비 완료: {PROFILE_DIR}")
    print("[WARN] Chrome 쿠키가 암호화되어 있어서 이 방법이 안 될 수 있습니다.")
    print("[WARN] 안 되면 Playwright 브라우저에서 직접 카카오 로그인이 필요합니다.")
    print("\n[TIP] 카카오 로그인 팝업이 안 열리면:")
    print("  1. Playwright 브라우저에서 accounts.kakao.com 직접 접속")
    print("  2. 카카오 ID/PW로 로그인")
    print("  3. flow.team으로 이동해서 '카카오 계정으로 로그인' 클릭")


if __name__ == "__main__":
    copy_cookies()
