# 📘 VELOS 기억 기반 판단 시스템

이 시스템은 GPT-5 기반 VELOS 마스터 루프에서 **저장된 기억 (메모리 및 회고)** 을 불러와,
판단에 자동 반영하는 자율형 인공지능 루프입니다.

---

## 📁 주요 경로 구성

| 경로 | 설명 |
|------|------|
| `scripts/run_giwanos_master_loop.py` | 마스터 루프 메인. 판단 실행, 메모리 기록 포함 |
| `modules/core/memory_reader.py` | 기억 요약 및 회고 불러오기 모듈 |
| `data/memory/learning_memory.json` | 사용자 및 시스템 판단 기록 저장소 |
| `data/reflections/reflection_memory_*.json` | GPT 판단 회고 자동 생성 저장소 |
| `data/reports/learning_summary.json` | 최근 판단 흐름 요약 |
| `interface/velos_dashboard.py` | Streamlit 대시보드 (Memory / 판단 / 루프 실행 포함) |

---

## 🧠 기억 반영 흐름

1. `memory_reader.py`에서 `read_memory_context()` 실행
2. 최근 사용자 명령 + 시스템 회고 요약을 context로 생성
3. 마스터 루프 판단 시, `context + user_request` 형태로 GPT에 전달
4. 판단 결과 및 사용된 기억은 `learning_memory.json`에 기록됨

---

## 🧪 테스트 명령어

```bash
# 가상환경 활성화 후 VELOS 루프 실행
cd C:/giwanos
.\venv\Scripts\activate
python scripts/run_giwanos_master_loop.py
