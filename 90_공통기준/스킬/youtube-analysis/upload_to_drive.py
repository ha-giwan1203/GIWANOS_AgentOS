"""
영상분석 결과 Google Drive 업로드
Usage: python upload_to_drive.py <video_id>

cache/{video_id}/ 폴더 내 파일을 Drive '영상분석/raw/{video_id}/' 에 업로드.
첫 실행 시 OAuth 인증 필요 (브라우저 팝업).

사전 준비:
1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID 생성 (Desktop 앱)
2. credentials.json 을 이 스크립트와 같은 폴더에 저장
3. Drive API 활성화
"""

import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCRIPT_DIR = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDS_PATH = SCRIPT_DIR / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "token.json"
DRIVE_ROOT_NAME = "영상분석"
DRIVE_RAW_NAME = "raw"


def get_service():
    """Drive API 서비스 인스턴스 반환. 첫 실행 시 OAuth 인증."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                print(f"[오류] {CREDS_PATH} 없음. Google Cloud Console에서 OAuth 클라이언트 ID 다운로드 필요.", file=sys.stderr)
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=18080, open_browser=False)  # 브라우저 자동 열기 비활성화
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def find_or_create_folder(service, name: str, parent_id: str = None) -> str:
    """폴더 검색, 없으면 생성. 폴더 ID 반환."""
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"[Drive 폴더 생성] {name}")
    return folder["id"]


def upload_file(service, local_path: Path, parent_id: str) -> str:
    """파일 업로드. 기존 파일 있으면 업데이트. 파일 ID 반환."""
    name = local_path.name
    q = f"name='{name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=q, spaces="drive", fields="files(id)").execute()
    existing = results.get("files", [])

    mime = "application/octet-stream"
    if name.endswith(".json"):
        mime = "application/json"
    elif name.endswith(".txt"):
        mime = "text/plain"
    elif name.endswith(".mp4"):
        mime = "video/mp4"
    elif name.endswith(".jpg"):
        mime = "image/jpeg"

    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)

    if existing:
        file = service.files().update(fileId=existing[0]["id"], media_body=media).execute()
    else:
        metadata = {"name": name, "parents": [parent_id]}
        file = service.files().create(body=metadata, media_body=media, fields="id").execute()

    return file["id"]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="영상분석 캐시 → Drive 업로드")
    parser.add_argument("video_id", help="업로드할 video_id")
    parser.add_argument("--skip-mp4", action="store_true", help="mp4 파일 제외 (용량 절약)")
    args = parser.parse_args()

    cache_dir = SCRIPT_DIR / "cache" / args.video_id
    if not cache_dir.exists():
        print(f"[오류] 캐시 폴더 없음: {cache_dir}", file=sys.stderr)
        sys.exit(1)

    service = get_service()

    # 폴더 구조: 영상분석/raw/{video_id}/
    root_id = find_or_create_folder(service, DRIVE_ROOT_NAME)
    raw_id = find_or_create_folder(service, DRIVE_RAW_NAME, root_id)
    video_folder_id = find_or_create_folder(service, args.video_id, raw_id)

    # 파일 업로드
    uploaded = 0
    skipped = 0
    for f in sorted(cache_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.name == ".gitignore":
            continue
        if args.skip_mp4 and f.suffix == ".mp4":
            skipped += 1
            continue

        # frames/ 하위는 frames 폴더 생성
        if f.parent.name == "frames":
            frames_folder_id = find_or_create_folder(service, "frames", video_folder_id)
            upload_file(service, f, frames_folder_id)
        else:
            upload_file(service, f, video_folder_id)
        uploaded += 1

    # Drive 폴더 URL
    folder_url = f"https://drive.google.com/drive/folders/{video_folder_id}"
    print(f"\n[Drive 업로드 완료] {uploaded}개 파일 / {skipped}개 스킵")
    print(f"[Drive 폴더] {folder_url}")

    # 결과 JSON 출력 (Claude가 파싱용)
    result = {"video_id": args.video_id, "folder_id": video_folder_id, "folder_url": folder_url, "uploaded": uploaded, "skipped": skipped}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
