"""
validate_frames.py
supanova-deploy 스킬 — 프레임 산출물 검증 스크립트

사용법:
  python validate_frames.py <output_folder>
  예: python validate_frames.py ./supanova-deploy-output

검증 항목:
  1. 필수 폴더/파일 존재 (index.html, assets/, frames/)
  2. 프레임 파일 수 및 파일명 연속성
  3. index.html 내 절대경로 참조 여부
  4. frames/ 경로 참조가 상대경로인지 확인
"""

import os
import re
import sys


def validate(output_dir):
    results = []
    passed = True

    def check(condition, label, detail=""):
        nonlocal passed
        status = "PASS" if condition else "FAIL"
        if not condition:
            passed = False
        results.append(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
        return condition

    # 1. 필수 항목 존재
    index_path = os.path.join(output_dir, "index.html")
    assets_path = os.path.join(output_dir, "assets")
    frames_path = os.path.join(output_dir, "frames")

    check(os.path.isfile(index_path), "index.html 존재")
    check(os.path.isdir(assets_path), "assets/ 폴더 존재")
    frames_ok = check(os.path.isdir(frames_path), "frames/ 폴더 존재")

    # 2. 프레임 파일 검증
    if frames_ok:
        frame_files = sorted([
            f for f in os.listdir(frames_path)
            if f.lower().endswith(".webp")
        ])
        count = len(frame_files)
        check(count > 0, f"프레임 파일 수", f"{count}개")

        if count > 1:
            # 파일명 연속성 확인 (숫자 기반)
            nums = []
            for f in frame_files:
                m = re.search(r'(\d+)', f)
                if m:
                    nums.append(int(m.group(1)))
            if nums:
                expected = list(range(min(nums), min(nums) + len(nums)))
                check(
                    nums == expected,
                    "프레임 파일명 연속성",
                    f"첫={min(nums)}, 마지막={max(nums)}, 총={len(nums)}"
                )
    else:
        results.append("[SKIP] 프레임 파일 검증 — frames/ 없음")

    # 3. index.html 경로 검증
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        # 절대경로 참조 탐지
        abs_refs = re.findall(r'(?:src|href)=["\'](?:/[^"\']*|[A-Z]:[^"\']*)["\']', html)
        check(len(abs_refs) == 0, "절대경로 참조 없음",
              f"발견된 절대경로: {abs_refs[:3]}" if abs_refs else "")

        # frames/ 상대경로 참조 확인
        frames_refs = re.findall(r'frames/', html)
        check(len(frames_refs) > 0, "frames/ 경로 참조 존재",
              f"참조 수: {len(frames_refs)}")

    # 결과 출력
    print(f"\n=== supanova-deploy 산출물 검증: {output_dir} ===")
    for r in results:
        print(r)
    print(f"\n최종 판정: {'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python validate_frames.py <output_folder>")
        sys.exit(1)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
