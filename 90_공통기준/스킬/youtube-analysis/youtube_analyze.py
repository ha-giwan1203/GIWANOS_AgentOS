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
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent

# 캐시 정책
CACHE_TTL_DAYS = 7
CACHE_MAX_BYTES = 1 * 1024**3  # 1GB


def get_last_used(video_dir: Path) -> float:
    """LRU 판단용 최종 사용 시각. info.json → transcript.txt → 폴더 mtime fallback."""
    for pattern in ["*.info.json"]:
        candidates = list(video_dir.glob(pattern))
        if candidates:
            return candidates[0].stat().st_mtime
    transcript = video_dir / "transcript.txt"
    if transcript.exists():
        return transcript.stat().st_mtime
    return video_dir.stat().st_mtime


def get_dir_size(path: Path) -> int:
    """디렉토리 전체 크기 (bytes)."""
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def cleanup_cache(cache_root: Path):
    """캐시 TTL + 용량 상한 자동 정리. 실행 시작 시 호출."""
    if not cache_root.exists():
        return

    dirs = [d for d in cache_root.iterdir() if d.is_dir() and d.name != ".gitignore"]
    if not dirs:
        return

    now = time.time()
    ttl_seconds = CACHE_TTL_DAYS * 86400
    deleted_dirs = 0
    deleted_mp4s = 0

    # 1차: TTL 만료 폴더 삭제
    remaining = []
    for d in dirs:
        age = now - get_last_used(d)
        if age > ttl_seconds:
            shutil.rmtree(d)
            deleted_dirs += 1
        else:
            remaining.append(d)

    # 2차: 용량 상한 초과 시 mp4 우선 삭제 (오래된 순)
    total_size = sum(get_dir_size(d) for d in remaining)
    if total_size > CACHE_MAX_BYTES:
        remaining.sort(key=get_last_used)
        for d in remaining:
            if total_size <= CACHE_MAX_BYTES:
                break
            for mp4 in d.glob("*.mp4"):
                mp4_size = mp4.stat().st_size
                mp4.unlink()
                total_size -= mp4_size
                deleted_mp4s += 1

    # 3차: 여전히 초과 시 오래된 폴더 전체 삭제
    if total_size > CACHE_MAX_BYTES:
        remaining = [d for d in remaining if d.exists()]
        remaining.sort(key=get_last_used)
        for d in remaining:
            if total_size <= CACHE_MAX_BYTES:
                break
            dir_size = get_dir_size(d)
            shutil.rmtree(d)
            total_size -= dir_size
            deleted_dirs += 1

    # 로그
    if deleted_dirs > 0 or deleted_mp4s > 0:
        final_size_mb = total_size / (1024 * 1024)
        print(f"[캐시 정리] 폴더 {deleted_dirs}개 삭제 / mp4 {deleted_mp4s}개 삭제 / 잔여 {final_size_mb:.0f}MB")


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


def download_video(url: str, video_id: str, out_dir: Path) -> tuple[Path | None, dict]:
    """yt-dlp로 영상 다운로드 (480p). 실패/타임아웃 시 (None, {}) 반환."""
    video_path = out_dir / f"{video_id}.mp4"
    info_path = out_dir / f"{video_id}.info.json"

    if video_path.exists() and info_path.exists():
        print(f"[캐시 사용] {video_path}")
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        return video_path, info

    cmd = [
        "yt-dlp",
        "--js-runtimes", "node",
        "--remote-components", "ejs:github",
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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", timeout=120)
    except subprocess.TimeoutExpired:
        print("[다운로드 타임아웃] yt-dlp 120초 초과 — transcript-only 모드로 전환", file=sys.stderr)
        return None, {}

    if result.returncode != 0:
        print(f"[다운로드 실패] yt-dlp exit={result.returncode}", file=sys.stderr)
        if result.stderr:
            print(f"  stderr: {result.stderr[:300]}", file=sys.stderr)
        return None, {}

    if not info_path.exists():
        alt = out_dir / f"{video_id}.info.json"
        if not alt.exists():
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
                capture_output=True, text=True, timeout=15
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
        try:
            subprocess.run(cmd, capture_output=True, timeout=20)
        except subprocess.TimeoutExpired:
            print(f"[프레임 타임아웃] {ts}s 지점 스킵", file=sys.stderr)
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
    try:
        result = subprocess.run(
            [sys.executable, str(script), video_id, "--timestamps"],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"}, timeout=60
        )
    except subprocess.TimeoutExpired:
        print("[자막 추출 타임아웃] 60초 초과", file=sys.stderr)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("[자막 추출 타임아웃]\n")
        return transcript_path

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
                      frames: list[Path], transcript_path: Path,
                      download_status: str = "ok",
                      download_error: str = ""):
    """분석 매니페스트 생성 — Claude가 이 파일을 읽고 분석 시작"""
    frames_available = len(frames) > 0
    if download_status == "ok" and frames_available:
        analysis_mode = "full"
    elif transcript_path.exists() and transcript_path.stat().st_size > 50:
        analysis_mode = "transcript_only"
    else:
        analysis_mode = "failed"

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
        "download_status": download_status,
        "frames_available": frames_available,
        "analysis_mode": analysis_mode,
        "download_error": download_error,
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
    parser.add_argument("--no-download", action="store_true", default=True,
                        help="(기본값) 자막만 추출. yt-dlp YouTube hang 대응으로 기본 전환 (2026-04-12)")
    parser.add_argument("--force-download", action="store_true",
                        help="영상 다운로드+프레임 추출 강제. Node.js+EJS로 JS challenge 복구됨")
    parser.add_argument("--refresh", action="store_true", help="캐시 무시, 강제 재다운로드")
    args = parser.parse_args()

    # --force-download 시 no_download 해제
    if args.force_download:
        args.no_download = False

    # 캐시 자동 정리 (TTL 7일 + 1GB 상한)
    cleanup_cache(SCRIPT_DIR / "cache")

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
        print("\n[transcript-only 모드] 자막만 추출 (기본값)")
        generate_manifest(video_id, out_dir, {}, [], transcript_path,
                          download_status="skipped",
                          download_error="transcript-only default mode (yt-dlp YouTube hang 대응)")
        return

    # Step 2: 영상 다운로드
    video_path, info = download_video(args.url, video_id, out_dir)

    if video_path is None:
        # 다운로드 실패 → transcript-only fallback
        print("\n[transcript-only 모드] 다운로드 실패, 자막만으로 분석 계속")
        generate_manifest(video_id, out_dir, {}, [], transcript_path,
                          download_status="timeout" if not info else "error",
                          download_error="yt-dlp timeout or failure")
        return

    # Step 3: 프레임 추출
    frames = extract_frames(video_path, out_dir, info,
                            interval=args.interval, max_frames=args.max_frames)

    # Step 4: 매니페스트 생성
    generate_manifest(video_id, out_dir, info, frames, transcript_path)


if __name__ == "__main__":
    main()
