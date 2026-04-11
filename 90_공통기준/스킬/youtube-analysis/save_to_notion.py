"""
영상분석 결과 Notion DB 저장 헬퍼
Usage: Claude가 분석 완료 후 이 모듈을 import하여 호출

직접 실행은 지원하지 않음 — Claude MCP(notion-create-pages, notion-search)로 저장.
이 파일은 저장에 필요한 데이터 구조와 upsert 로직을 정의한다.
"""

# Notion DB 정보
NOTION_DB_DATA_SOURCE_ID = "20920532-0e23-4ddd-97b1-1264b54adb77"

# 저장 데이터 구조 (Claude가 분석 후 이 형식으로 채워서 MCP 호출)
SAVE_TEMPLATE = {
    "제목": "",           # 영상 제목
    "영상 URL": "",       # YouTube URL
    "video_id": "",       # 영상 ID
    "채널": "",           # 채널명
    "date:분석일:start": "",  # ISO-8601 날짜 (예: 2026-04-11)
    "date:분석일:is_datetime": 0,
    "분석 방식": "local",  # local / gemini / hybrid
    "자막 유무": "__YES__",  # __YES__ 또는 __NO__
    "등급 요약": "",       # 예: "A 2건 / B 1건 / C 3건"
    "핵심 주제": "[]",     # JSON array 예: '["Claude Code", "hooks"]'
    "Drive 링크": "",      # Drive 폴더 URL (있으면)
    "요약": "",            # 3~5줄 핵심 요약
}

# Notion 본문 템플릿
PAGE_CONTENT_TEMPLATE = """## 요약
{summary}

## 핵심 화면
{key_frames}

## 적용 포인트
{action_points}

## 원본 링크
- YouTube: {youtube_url}
- Drive: {drive_url}
"""


def build_properties(manifest: dict, analysis: dict) -> dict:
    """manifest.json + 분석 결과에서 Notion 속성 딕셔너리 생성"""
    import datetime
    today = datetime.date.today().isoformat()

    return {
        "제목": manifest.get("title", "알 수 없음"),
        "영상 URL": f"https://youtube.com/watch?v={manifest.get('video_id', '')}",
        "video_id": manifest.get("video_id", ""),
        "채널": manifest.get("channel", ""),
        "date:분석일:start": today,
        "date:분석일:is_datetime": 0,
        "분석 방식": analysis.get("method", "local"),
        "자막 유무": "__YES__" if analysis.get("has_transcript", True) else "__NO__",
        "등급 요약": analysis.get("grade_summary", ""),
        "핵심 주제": str(analysis.get("tags", [])),
        "Drive 링크": analysis.get("drive_url", ""),
        "요약": analysis.get("summary", ""),
    }


def build_content(analysis: dict) -> str:
    """Notion 본문 생성"""
    return PAGE_CONTENT_TEMPLATE.format(
        summary=analysis.get("summary", ""),
        key_frames=analysis.get("key_frames_md", "(프레임 없음)"),
        action_points=analysis.get("action_points", ""),
        youtube_url=analysis.get("youtube_url", ""),
        drive_url=analysis.get("drive_url", "없음"),
    )
