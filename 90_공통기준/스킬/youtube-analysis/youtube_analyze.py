"""
YouTube 영상 분석 파이프라인
Usage: python youtube_analyze.py <URL> [--interval N] [--max-frames N]

영상 다운로드 → 프레임 추출 → 자막 추출 → 분석 준비물 생성
Claude가 Read 도구로 프레임 이미지를 직접 보고 자막과 통합 분석하는 구조.
"""

import sys
import os
import re
import io
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent

# ffmpeg PATH 자동 탐지 (winget 설치 시 세션에 즉시 반영 안 됨)
_FFMPEG_WINGET = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
for _pkg in _FFMPEG_WINGET.glob("Gyan.FFmpeg*"):
    _bin = list(_pkg.glob("**/bin/ffmpeg.exe"))
    if _bin:
        _ffmpeg_dir = str(_bin[0].parent)
        if _ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        break


def extract_video_id(url_or_id: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"유효한 YouTube URL/ID 아님: {url_or_id}")


def get_output_dir(video_id: str) -> Path:
    """분석 결과 저장 폴더"""
    out = SCRIPT_DIR / "cache" / video_id
    out.mkdir(parents=True, exist_ok=True)
    return out


def download_video(url: str, video_id: str, out_dir: Path) -> tuple[Path, dict]:
    """yt-dlp로 영상 다운로드 (480p). 챕터 정보 포함 info.json도 저장."""
    video_path = out_dir / f"{video_id}.mp4"
    info_path = out_dir / f"{video_id}.info.json"

    if video_path.exists() and info_path.exists():
        print(f"[캐시 사용] {video_path}")
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        return video_path, info

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "--merge-output-format", "mp4",
        "-o", str(video_path),
        "--write-info-json",
        "--no-playlist",
        "--quiet",
        "--progress",
        url,
    ]
    print(f"[다운로드] {url} → 480p mp4 ...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"ERROR: yt-dlp 실패\n{result.stderr}", file=sys.stderr)
        sys.exit(10)

    if not info_path.exists():
        # info.json 경로가 다를 수 있음
        alt = out_dir / f"{video_id}.info.json"
        if not alt.exists():
            # fallback: 빈 info
            info = {}
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(info, f)
        else:
            info_path = alt

    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    print(f"[다운로드 완료] {video_path} ({video_path.stat().st_size // 1024 // 1024}MB)")
    return video_path, info


def extract_frames(video_path: Path, out_dir: Path, info: dict,
                   interval: int = 30, max_frames: int = 15) -> list[Path]:
    """ffmpeg로 프레임 추출. 챕터 기준 우선(긴 챕터 보강), 없으면 일정 간격."""
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    # 기존 프레임이 있으면 캐시 사용
    existing = sorted(frames_dir.glob("frame_*.jpg"))
    if existing:
        print(f"[캐시 사용] 프레임 {len(existing)}장")
        return existing

    chapters = info.get("chapters", [])
    timestamps = []

    if chapters:
        # 챕터 시작 시점 + 중간 + 긴 챕터(90초 초과) 내부 추가 샘플
        for ch in chapters:
            start = ch.get("start_time", 0)
            end = ch.get("end_time", start + 60)
            chapter_len = end - start
            timestamps.append(start + 2)  # 챕터 시작 2초 후
            if chapter_len > 90:
                # 긴 챕터: 3등분 지점에 추가 샘플
                third = chapter_len / 3
                timestamps.append(start + third)
                timestamps.append(start + third * 2)
            elif chapter_len > 30:
                # 보통 챕터: 중간 1장 추가
                timestamps.append((start + end) / 2)
        print(f"[프레임] 챕터 기준 (긴 챕터 보강) {len(timestamps)}개 시점")
    else:
        # 영상 길이 확인
        duration = info.get("duration", 0)
        if duration == 0:
            # ffprobe로 길이 확인
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
                capture_output=True, text=True
            )
            duration = float(probe.stdout.strip()) if probe.stdout.strip() else 600

        timestamps = list(range(5, int(duration), interval))
        print(f"[프레임] {interval}초 간격, {len(timestamps)}개 시점")

    # 최대 프레임 수 제한
    if len(timestamps) > max_frames:
        step = len(timestamps) / max_frames
        timestamps = [timestamps[int(i * step)] for i in range(max_frames)]

    frames = []
    for i, ts in enumerate(timestamps):
        frame_path = frames_dir / f"frame_{i:03d}_{int(ts)}s.jpg"
        cmd = [
            "ffmpeg", "-ss", str(ts), "-i", str(video_path),
            "-frames:v", "1", "-q:v", "2",
            "-y", "-loglevel", "error",
            str(frame_path)
        ]
        subprocess.run(cmd, capture_output=True)
        if frame_path.exists():
            frames.append(frame_path)

    print(f"[프레임 추출 완료] {len(frames)}장 → {frames_dir}")
    return frames


def extract_transcript(video_id: str, out_dir: Path) -> Path:
    """자막 추출 (기존 youtube_transcript.py 활용)"""
    transcript_path = out_dir / "transcript.txt"

    if transcript_path.exists():
        print(f"[캐시 사용] {transcript_path}")
        return transcript_path

    script = SCRIPT_DIR / "youtube_transcript.py"
    result = subprocess.run(
        [sys.executable, str(script), video_id, "--timestamps"],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"}
    )

    if result.returncode == 0:
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        print(f"[자막 추출 완료] {transcript_path}")
    else:
        print(f"[자막 추출 실패] exit={result.returncode}: {result.stderr}", file=sys.stderr)
        # 빈 파일이라도 생성
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("[자막 추출 실패]\n")

    return transcript_path


def generate_manifest(video_id: str, out_dir: Path, info: dict,
                      frames: list[Path], transcript_path: Path):
    """분석 매니페스트 생성 — Claude가 이 파일을 읽고 분석 시작"""
    manifest = {
        "video_id": video_id,
        "title": info.get("title", "알 수 없음"),
        "channel": info.get("channel", info.get("uploader", "알 수 없음")),
        "duration": info.get("duration", 0),
        "upload_date": info.get("upload_date", ""),
        "view_count": info.get("view_count", 0),
        "chapters": info.get("chapters", []),
        "transcript_path": str(transcript_path),
        "frames": [str(f) for f in frames],
        "frames_dir": str(out_dir / "frames"),
        "analysis_guide": (
            "1. transcript.txt를 읽어 전체 내용 파악\n"
            "2. frames/ 폴더의 이미지를 Read 도구로 열어 시각 정보(코드, UI, 설정 화면 등) 확인\n"
            "3. 자막+프레임 교차 분석으로 핵심 내용 추출\n"
            "4. 9관점 분석 + A/B/C 판정"
        )
    }

    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[분석 준비 완료]")
    print(f"  영상: {manifest['title']}")
    print(f"  채널: {manifest['channel']}")
    print(f"  길이: {manifest['duration']}초")
    print(f"  프레임: {len(frames)}장")
    print(f"  매니페스트: {manifest_path}")
    print(f"{'='*60}")
    print(f"\n다음 단계: Claude가 manifest.json을 Read → 프레임 이미지 분석 → 통합 출력")

    return manifest_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="YouTube 영상 프레임+자막 분석 파이프라인")
    parser.add_argument("url", help="YouTube URL 또는 Video ID")
    parser.add_argument("--interval", type=int, default=30, help="프레임 추출 간격(초), 챕터 없을 때 사용 (기본: 30)")
    parser.add_argument("--max-frames", type=int, default=15, help="최대 프레임 수 (기본: 15)")
    parser.add_argument("--no-download", action="store_true", help="다운로드/프레임 생략, 자막만 추출")
    parser.add_argument("--refresh", action="store_true", help="캐시 무시, 강제 재다운로드")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    out_dir = get_output_dir(video_id)

    # --refresh 시 캐시 삭제
    if args.refresh and out_dir.exists():
        shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"[캐시 삭제] {out_dir}")

    print(f"[영상 ID] {video_id}")
    print(f"[출력 폴더] {out_dir}")

    # Step 1: 자막 추출
    transcript_path = extract_transcript(video_id, out_dir)

    if args.no_download:
        print("\n[--no-download] 자막만 추출 완료")
        print(f"자막 경로: {transcript_path}")
        return

    # Step 2: 영상 다운로드
    video_path, info = download_video(args.url, video_id, out_dir)

    # Step 3: 프레임 추출
    frames = extract_frames(video_path, out_dir, info,
                            interval=args.interval, max_frames=args.max_frames)

    # Step 4: 매니페스트 생성
    generate_manifest(video_id, out_dir, info, frames, transcript_path)


if __name__ == "__main__":
    main()
