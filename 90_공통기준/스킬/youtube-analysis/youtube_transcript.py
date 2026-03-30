"""
YouTube 자막 자동 추출 스크립트
Usage: python youtube_transcript.py <YouTube_URL_or_ID> [--timestamps]
"""

import sys
import re
import io
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

# Windows 터미널 인코딩 문제 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def extract_video_id(url_or_id: str) -> str:
    """YouTube URL 또는 ID에서 video ID 추출"""
    patterns = [
        r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"유효한 YouTube URL 또는 ID가 아닙니다: {url_or_id}")


def fetch_transcript(video_id: str) -> tuple:
    """자막 가져오기 — 한국어 우선, 자동생성 한국어, 영어 순"""
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)

    priority = [
        (["ko"], False),   # 수동 한국어
        (["ko"], True),    # 자동생성 한국어
        (["en"], False),   # 수동 영어
        (["en"], True),    # 자동생성 영어
    ]

    for langs, generated_only in priority:
        try:
            if generated_only:
                transcript = transcript_list.find_generated_transcript(langs)
            else:
                transcript = transcript_list.find_manually_created_transcript(langs)
            fetched = transcript.fetch()
            label = f"{transcript.language_code} ({'자동생성' if transcript.is_generated else '수동'})"
            return fetched, label
        except Exception:
            continue

    # 마지막 수단: 첫 번째 사용 가능한 자막
    for transcript in transcript_list:
        fetched = transcript.fetch()
        label = f"{transcript.language_code} (폴백)"
        return fetched, label

    raise NoTranscriptFound(video_id, [], None)


def format_transcript(entries, include_timestamps: bool = False) -> str:
    """자막 항목을 텍스트로 변환"""
    lines = []
    for entry in entries:
        # v1.2.4: entry는 Snippet 객체일 수 있음
        if hasattr(entry, "text"):
            text = entry.text.strip()
            start = entry.start
        else:
            text = entry.get("text", "").strip()
            start = entry.get("start", 0)

        if not text:
            continue

        if include_timestamps:
            minutes = int(start // 60)
            seconds = int(start % 60)
            lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("사용법: python youtube_transcript.py <YouTube_URL_or_ID> [--timestamps]", file=sys.stderr)
        sys.exit(1)

    url_or_id = sys.argv[1]
    include_timestamps = "--timestamps" in sys.argv

    try:
        video_id = extract_video_id(url_or_id)
        entries, lang_info = fetch_transcript(video_id)
        transcript_text = format_transcript(entries, include_timestamps)

        print(f"[자막 언어: {lang_info}]")
        print(f"[총 {len(entries)}개 세그먼트]")
        print("---")
        print(transcript_text)

    except TranscriptsDisabled:
        print("ERROR: 이 영상은 자막이 비활성화되어 있습니다.", file=sys.stderr)
        sys.exit(2)
    except NoTranscriptFound:
        print("ERROR: 사용 가능한 자막을 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(3)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"ERROR: 예상치 못한 오류 — {e}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
