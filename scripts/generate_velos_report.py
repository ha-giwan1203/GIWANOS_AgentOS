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
import json
import datetime
import sys
from typing import Dict, Any, List

ROOT = r"C:\giwanos"
REPORT_DIR = os.path.join(ROOT, "data", "reports")
HEALTH_LOG = os.path.join(ROOT, "data", "logs", "system_health.json")

def get_latest_snapshot() -> str:
    """최신 스냅샷 파일명 반환"""
    try:
        snap_dir = os.path.join(ROOT, "data", "snapshots")
        if not os.path.exists(snap_dir):
            return "스냅샷 디렉토리 없음"

        snaps = [f for f in os.listdir(snap_dir) if f.endswith(".zip")]
        if not snaps:
            return "스냅샷 없음"

        return max(snaps)
    except Exception as e:
        return f"스냅샷 조회 오류: {e}"

def get_memory_stats() -> Dict[str, Any]:
    """메모리 통계 수집"""
    try:
        from modules.core.memory_adapter import MemoryAdapter
        adapter = MemoryAdapter()
        return adapter.get_stats()
    except Exception as e:
        return {"error": str(e)}

def generate_report() -> Dict[str, Any]:
    """VELOS 시스템 보고서 생성"""
    try:
        # 보고서 디렉토리 생성
        os.makedirs(REPORT_DIR, exist_ok=True)

        # 타임스탬프 생성
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        report_path = os.path.join(REPORT_DIR, f"velos_report_{ts}.md")

        # 헬스 로그 읽기
        health_data = {}
        if os.path.exists(HEALTH_LOG):
            try:
                with open(HEALTH_LOG, "r", encoding="utf-8") as f:
                    health_data = json.load(f)
            except Exception as e:
                health_data = {"error": f"헬스 로그 읽기 실패: {e}"}
        else:
            health_data = {"error": "헬스 로그 파일 없음"}

        # 메모리 통계 수집
        memory_stats = get_memory_stats()

        # 최신 스냅샷 확인
        latest_snapshot = get_latest_snapshot()

        # Markdown 내용 생성
        md_content = [
            "# VELOS 시스템 보고서",
            f"생성 시각: {ts}",
            "",
            "## 📊 시스템 상태",
        ]

        # 헬스 데이터 추가
        if "error" not in health_data:
            # 시스템 무결성 정보
            system_integrity = health_data.get('system_integrity', {})
            data_integrity = health_data.get('data_integrity', {})

            md_content.extend([
                f"- autosave_runner_count: {system_integrity.get('autosave_runner_count', 'N/A')}",
                f"- autosave_runner_ok: {system_integrity.get('autosave_runner_ok', 'N/A')}",
                f"- system_integrity_ok: {system_integrity.get('integrity_ok', 'N/A')}",
                f"- data_integrity_ok: {data_integrity.get('data_integrity_ok', 'N/A')}",
            ])

            # 경고 및 노트 추가
            warnings = system_integrity.get('warnings', [])
            if warnings:
                md_content.append(f"- warnings: {', '.join(warnings)}")

            notes = system_integrity.get('notes', [])
            if notes:
                md_content.append(f"- notes: {', '.join(notes)}")
        else:
            md_content.append(f"- 헬스 로그 오류: {health_data['error']}")

        # 메모리 통계 추가
        md_content.extend([
            "",
            "## 💾 메모리 상태",
        ])

        if "error" not in memory_stats:
            md_content.extend([
                f"- Buffer Size: {memory_stats.get('buffer_size', 'N/A')}",
                f"- DB Records: {memory_stats.get('db_records', 'N/A')}",
                f"- JSON Records: {memory_stats.get('json_records', 'N/A')}",
            ])
        else:
            md_content.append(f"- 메모리 통계 오류: {memory_stats['error']}")

        # 스냅샷 정보 추가
        md_content.extend([
            "",
            "## 📁 스냅샷 정보",
            f"- 최신 스냅샷: {latest_snapshot}",
            "",
            "---",
            f"*생성 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "*VELOS 운영 철학 기반*"
        ])

        # 파일 저장
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        return {
            "success": True,
            "report_path": report_path,
            "filename": f"velos_report_{ts}.md",
            "health_data": health_data,
            "memory_stats": memory_stats,
            "latest_snapshot": latest_snapshot
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """메인 실행 함수"""
    print("=== VELOS Report Generator ===")

    result = generate_report()

    if result["success"]:
        print(f"✅ Report generated successfully")
        print(f"📁 Location: {result['report_path']}")
        print(f"📄 Filename: {result['filename']}")

        # 결과를 JSON으로 출력
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        print(f"❌ Report generation failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
