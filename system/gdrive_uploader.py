import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import pickle
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_zip_to_drive(zip_path, drive_folder_id=None, log_file="gdrive_backup_log.json"):
    service = get_service()
    file_metadata = {'name': os.path.basename(zip_path)}
    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]
    media = MediaFileUpload(zip_path, mimetype='application/zip')
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"✅ 업로드 완료: {zip_path} → Google Drive ID: {uploaded.get('id')}")

    log = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            log = json.load(f)

    log.append({
        "file": os.path.basename(zip_path),
        "uploaded_at": datetime.now().isoformat(),
        "drive_id": uploaded.get('id')
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    upload_zip_to_drive("backups/giwanos_backup_20250719_233000.zip")
