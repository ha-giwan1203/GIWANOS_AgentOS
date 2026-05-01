# 잡셋업 — pywinauto 마이그레이션 계획

> 상위 plan: `C:\Users\User\.claude\plans\wiggly-gliding-sundae.md`
> 사전 평가: `PLAN_API_FEASIBILITY.md` (시나리오 3 확정)
> PoC 검증: 2026-05-01 17:53 KST
> 상태: **PoC 성공 → 본 마이그레이션 plan 확정**

## Context

생산계획 하이브리드(API 직호출) 동일 패턴은 SmartMES 잡셋업에 이식 불가 (시나리오 3, 별도 plan 참조). 차선책으로 `pywinauto` UIA backend 마이그레이션을 PoC 검증한 결과, **컨트롤 12/12 식별 + 메뉴 진입 + ComboBox 3건 선택 + Edit 3건 입력 + CheckBox 3건 toggle 모두 동작**. 좌표·numpad 시뮬레이션 의존성 0%로 전환 가능.

## PoC 실측 결과 (2026-05-01)

### 식별된 컨트롤 12/12 (auto_id 기반)

| 기능 | auto_id | 타입 | 호출 방식 |
|------|---------|------|----------|
| 메뉴 [J] 잡셋업 | `btnMenuJobSetup` | Button | `click_input()` |
| 메뉴 [E] 종료 | `btnExit` | Button | `click_input()` |
| 제품 dropdown | `cbSchedule` | ComboBox | `click_input()` + `type_keys("{DOWN}{ENTER}")` |
| 공정 dropdown | `cbProcess` | ComboBox | 동일 |
| 검사항목 dropdown | `cbJobSetup` | ComboBox | 동일 |
| X1/X2/X3 입력 | `txtX1` `txtX2` `txtX3` | Edit | `set_edit_text(f"{v:.2f}")` |
| X1/X2/X3 OK | `chkOkX1` `chkOkX2` `chkOkX3` | CheckBox | `toggle()` (state==0 일 때만) |
| 저장 | `btnSave` | Button | `click_input()` |

추가 식별됨 (v1.x용): X1/X2/X3 NG 체크박스 `chkNgX1~3`, 문제점/조치내용 dropdown `cbMainAbnml` `cbMidAbnml` `cbSubAbnml` `cbMainAction` `cbMidAction` `cbSubAction`, numpad 12개 (사용 불필요)

### PoC 검증 시나리오 (실제 화면 결과)

```
PoC: --mode select-only (실수로 enter-only까지 진행됨, 저장 0)
화면 결과:
  제품      = 1.RSP3SC0646_A                          (cbSchedule)
  공정      = [40] 베어링 부시 조립                   (cbProcess)
  검사항목  = 스플 베어링 부시 "0"점 MASTER GAGE      (cbJobSetup)
  X1=0.05 OK / X2=0.04 OK / X3=0.04 OK
  결과     = OK                                       (스펙 0±0.05 자동 판정)
```

### 기존 좌표 자동화 vs pywinauto 비교

| 항목 | 기존 (`run_jobsetup.py`) | pywinauto 마이그레이션 |
|------|------------------------|----------------------|
| 해상도 의존 | 1920×1080 강제 (`check_resolution`) | 무관 (auto_id 기반) |
| 창 위치 의존 | 절대 좌표 | 무관 (컨트롤 rect 자동) |
| numpad 시퀀스 | 클릭 13~15회/필드 | `set_edit_text()` 1회 |
| OCR 필요 (검사항목별 스펙) | v1.x | v1.x (별개 문제) |
| 다중 모니터 | 풀스크린 1번 모니터 | 무관 |
| 코드 복잡도 | 좌표 dict 24개 + SCALE 변환 | auto_id 12개 |
| 실패 진단 | 좌표 어긋날 시 침묵 실패 | `wait("exists", timeout=3)` 명시 실패 |

## 마이그레이션 범위

### Phase 1 — 본체 교체 (수일)
1. `run_jobsetup.py` → `run_jobsetup_v2.py` 신규 (기존은 fallback 유지)
2. PoC 스크립트 `scripts/poc_pywinauto.py` 의 컨트롤 매핑·선택 로직을 본체 함수로 승격
3. 모드 매핑:
   - 기존 `--dry-run` → v2 `--mode enter-only` (입력만, 저장 0)
   - 기존 `--commit` → v2 `--mode commit` (저장 포함)
4. 안전 가드 신규:
   - `wait("exists", timeout=3)` 미발견 시 즉시 fail (좌표 침묵 실패 방지)
   - 입력값 read-back 검증: `set_edit_text` 후 `texts()` 재조회로 확인
   - 저장 직전 컨트롤 12/12 재 probe (운영 환경 변경 감지)

### Phase 2 — chain 활성 (사용자 결정 후)
1. SKILL.md `status: v2.0` 갱신
2. `/d0-plan` SP3M3 morning 종료 후 hand-off 자동 진행 활성
3. 기존 좌표 본체는 `run_jobsetup_legacy.py` 보존 (긴급 fallback)

### Phase 3 — v1.x 확장 (검증 후)
1. 다중 검사항목 자동 순회 (`cbJobSetup` 항목 enum)
2. 다중 공정 순회 (`cbProcess` 항목 enum)
3. 검사항목별 스펙 OCR 또는 마스터 데이터 매핑

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `90_공통기준/스킬/jobsetup-auto/scripts/inspect_smartmes.py` | UIA tree dump (검증·디버그용) |
| `90_공통기준/스킬/jobsetup-auto/scripts/poc_pywinauto.py` | PoC 본체 (컨트롤 12/12 매핑 검증) |
| `90_공통기준/스킬/jobsetup-auto/state/inspect_uia_20260501_*.txt` | 컨트롤 트리 dump 원본 |
| (신규) `90_공통기준/스킬/jobsetup-auto/run_jobsetup_v2.py` | 본체 v2 (Phase 1 산출물) |
| `90_공통기준/스킬/jobsetup-auto/run_jobsetup.py` | 기존 좌표 본체 (legacy로 보존) |
| `90_공통기준/스킬/jobsetup-auto/SKILL.md` | 정책·등급 (Phase 2에서 갱신) |

## 안전 가드

- **dry-run 보존**: v2 기본값 `--mode probe` (식별만, 클릭 0건)
- **단계별 명시 모드**: `probe` → `select-only` → `enter-only` → `commit`. 한 단계씩 검증 후 다음 단계
- **입력값 read-back 필수**: `set_edit_text("0.05")` 후 `txt.texts()` 가 `["0.05"]` 인지 확인. 불일치 시 즉시 fail
- **저장 직전 12/12 재 probe**: 운영 환경에서 SmartMES 업데이트로 컨트롤 ID 변경 시 침묵 실패 차단
- **NG 자동 체크 금지**: `chkNgX1~3` 자동 toggle 절대 안 함 (NG는 사람 판정만)
- **저장 버튼 idempotency 미보장**: 1회 호출 후 `lblMsg` 재읽기로 결과 확인. 2회 호출 금지

## 검증 방법

### Phase 1 검증 (Phase 2 활성 전)
1. `python run_jobsetup_v2.py --mode probe` → 12/12 식별 PASS 필수
2. `python run_jobsetup_v2.py --mode select-only` → 화면 캡처로 제품/공정/검사항목 정확히 첫 항목 선택 확인
3. `python run_jobsetup_v2.py --mode enter-only` → X1/X2/X3 값 표시 + OK 체크 + 결과 OK 확인. **저장 미클릭**
4. `python run_jobsetup_v2.py --mode commit` (사용자 직접 트리거 1회) → 저장 후 `lblMsg` 메시지 확인. 다음 검사항목으로 전환 확인
5. v1 좌표 본체와 결과 동등성: 같은 시각 같은 첫 서열에 대해 v1·v2 각각 1회 dry-run 후 입력 필드 값 비교

### Phase 2 활성 조건
- Phase 1 검증 4단계 모두 PASS
- 사용자 1회 직접 commit 결과 확인
- chain 활성 후 첫 morning 1회 사람 입회 모니터링

### 회귀 시나리오 (Phase 1에서 사전 점검)
- SmartMES 재기동 후 PID 변경 → `connect(process=...)` 재해결 동작 확인
- 두 번째 모니터로 창 이동 → 좌표 무관 동작 확인
- 1366×768 등 다른 해상도 → 좌표 무관 동작 확인
- mesclient.exe 메뉴 진입 직후 잡셋업 컨트롤 로딩 지연 → `wait("exists", timeout=3)` 가 충분한지 확인 (필요 시 5초로 상향)

## 사용자 결정 필요

- Phase 1 본체 작성을 **즉시 진행할지** (auto mode 가능) vs **다음 세션으로 이월할지**
- Phase 2 chain 활성 시점 (Phase 1 PASS 후 다음 morning?)
- legacy 본체 보존 기간 (영구? 1개월 후 archive?)
