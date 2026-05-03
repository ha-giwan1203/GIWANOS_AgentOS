# jobsetup-auto — MANUAL

> Step 1~9 절차 / spec 패턴 / 안전 원칙 / 변경 이력. SKILL.md는 호출 트리거 + 80줄 요약.

## ⚠️ 자동화 책임 경고
SmartMES 잡셋업 화면의 실측 측정값을 **허용오차 내 정규분포 난수로 대체**합니다.
- 자동차 부품 첫 셋업 검사 데이터 자동 생성에 해당
- 사내 품질/감사 정책상 허용 범위인지 사용자 본인 책임 운영
- 잘못 저장 시 재입력 → 재저장으로 정정 (실측 확인 2026-04-30, 별도 삭제 API 불필요)
- ❌ v0.3까지의 무인 자동 실행 약속은 미검증 가정 — v1.0 baseline은 단일 케이스 dry-run만 보장
- 끄려면 (chain 활성 후): `/d0-plan --session morning --no-jobsetup` 또는 `--jobsetup-dry-run`

## 결정 출처
| 항목 | 결정 | 근거 |
|------|------|------|
| 트리거 | `/d0-plan` SP3M3 morning 끝 + 슬래시 단독 | 사용자 답변 (하이브리드) |
| 첫 서열 = 제품 1번 | 가정 OK | SmartMES가 서열 정렬 1번부터 노출 |
| 공정 범위 | 첫 서열 모든 공정 자동 순회 | 사용자 답변 |
| 검사항목 | 각 공정 N개(N≥1) 모두 | 사용자 명시 |
| 측정값 | 정규분포 난수 (`random.gauss`, σ=오차/3, 시드 미고정) | 사용자 답변 |
| OK/NG | OK 자동 체크 (NG 안 씀) | 사용자 답변 |
| 자동화 경로 | SmartMES UI computer-use → REST API 직호출 (v3.0) | API 미공개였으나 dnSpy 디컴파일로 확정 |
| 작업자 인증 | 별도 (잡셋업 단독 가능) | 사용자 답변 |
| 저장 단위 | 첫 실행 관찰 후 확정 | 사용자 답변 "모름" |
| dry-run 기본 | 항상 기본값 | 위험도 차단 |

## 사용법
```
/jobsetup-auto                      # 기본값 dry-run (저장 미클릭)
/jobsetup-auto --dry-run            # 명시적 dry-run
/jobsetup-auto --commit             # 실 저장 (v1.0+)
/jobsetup-auto --process 1          # 첫 공정만 (디버깅)
/jobsetup-auto --max-items 1        # 검사항목 1개만 (디버깅)
```

## 선결 조건

### v3.x (REST API 직호출)
- 사내 네트워크 (LMES dev: `lmes-dev.samsong.com:19220` / prod: 사용자 제공)
- Python 3 + `requests`
- env 설정 (v3.2+):
  - **dev (default)**: 설정 0 — 내장 DEV_DEFAULT
  - **prod**: 환경변수 `JOBSETUP_MES_SERVER` + `JOBSETUP_MES_TOKEN`, 또는 `config.json` `prod` 섹션 (template: `config.example.json`). 미설정 시 abort
- prod commit 시 사용자 입회 stderr 경고 자동

### legacy (v1/v2.x UI fallback)
- SmartMES (mesclient.exe) 실행 + 로그인
- `[J] 잡셋업` 메뉴 진입 (작업자 인증 별도)
- 제품 드롭다운에 첫 서열(1번) 노출 (= D0 반영 끝나서 SmartMES 동기화 완료)
- computer-use MCP `mesclient.exe` 권한
- 화면 해상도 변동 없음 (좌표 의존)

## 실행 절차 (Step 1~9)

### Step 1 — 모드 결정
- 인자 파싱: `--dry-run` (기본) / `--commit`
- 디버그: `--process N`, `--max-items M`
- commit 모드는 dry-run 1회 이상 PASS 후 허용 (state 검사)

### Step 2 — SmartMES 활성 확인
- `request_access(["mesclient.exe"])` 호출
- 스크린샷 → SmartMES 메인 + `[J] 잡셋업` 메뉴 가시성
- 미활성: 안내 후 종료
- `[J] 잡셋업` 클릭 → 화면 진입

### Step 3 — 제품 드롭다운 1번 선택
- 제품 드롭다운 좌표 캘리브레이션
- 클릭 → 첫 항목(1.<품번>_<suffix>) 선택
- 우측 상품명 노출 확인 (예: `RETRACTOR SP3 SLL CLR MECHANISM MODULE`) → 로그

### Step 4 — 공정 드롭다운 N 추출
- 공정 드롭다운 클릭 → 펼침 → zoom 캡쳐 → 항목 수 N
- 1번~N번 루프 시작

### Step 5 — 각 공정 검사항목 M 추출
- 공정 i 선택 (i = 1..N)
- 검사항목 드롭다운 → zoom 캡쳐 → M 카운트
- M=0 → 스킵 (검사항목 없는 공정)
- M≥1 → 1번~M번 루프

### Step 6 — 스펙 셀 텍스트 + 검사항목 분류 (6종 패턴)

> 2026-04-29 SmartMES 잡셋업 화면 분석 (1.RSP3SC0383_A) 결과. 원본: `state/screen_analysis_20260429.md`.

- 검사항목 j 선택 → 그리드 좌측 "스펙" 컬럼 zoom → 텍스트

**(A) 측정값형 — X1/X2/X3 난수 + OK 체크**

| 코드 | 패턴 | 예시 | 정규식 | 처리 |
|------|------|------|-------|------|
| **A1** 대칭 | `<중심> ± <오차>` | `0 ± 0.05` | `^([-+]?\d+(?:\.\d+)?)\s*[±]\s*(\d+(?:\.\d+)?)$` | min=중심-오차, max=중심+오차 |
| **A2** 비대칭+단위 | `<중심> +<상한><단위>, -<하한><단위>` | `10.5 +0.1mm, -0.3mm` | A2 정규식 | min=중심-하한, max=중심+상한 |
| **A3** 복합 비대칭 | A2가 2회+ (다부품 동시) | `스크류 C : 0 +0.45, -1.0mm 스크류 D : 0 +0.3, -2.0mm` | A2 multi-match | **두 패턴 교집합** = 좁은 [min, max] |

**(B) OK/NG 체크형 — X1/X2/X3 비우고 OK만**

| 코드 | 시그널 | 예시 |
|------|-------|------|
| **B1** | `OK/NG`, `[자동]` | `불량/양품 확인될것 (OK/NG)` |
| **B2** | `없을 것`, `상태`, `청결`, `주기` | `이물 없을 것` |
| **B3** | `OK/NG 마스터`, `확인 될 것` | `불량/양품 확인 될 것 (OK/NG 마스터)` |
| **B4** | `NG 확인`, `불량 제품` | `불량 제품 GAP NG 확인` |

**통합 분류 룰** (안전 fallback):
1. A1/A2/A3 정규식 매칭 → (A)
2. 그 외 정성적 텍스트 → (B) (OK 체크만)

매칭 실패 = (A) 미매칭이면 무조건 (B). 임의 추정값 입력 금지.

### Step 7 — 검사항목 분류별 입력

**Step 7-A: 측정값형**

> **분포**: 정규분포(`random.gauss`) 채택. 균등분포 X.
> 이유: 실제 측정값은 중심값 근처 정규분포가 자연. 균등은 품질 감사 통계 부자연.
> 사용자 샘플 (2026-04-29): [40] 0.04/0.05/0.05, [210] 10.5/10.4/10.4, [390] 0.2/0.3/0.3 — 모두 중심 근처.

```python
import random, time

def gen_measure(center, lo, hi, decimals):
    """정규분포로 측정값. ±3σ가 [lo, hi] 안."""
    half_range = min(center - lo, hi - center)
    sigma = half_range / 3.0   # ±3σ ≈ 99.7%
    while True:
        v = random.gauss(center, sigma)
        if lo <= v <= hi:
            return round(v, decimals)

random.seed()  # 시드 미고정 = 매일 다른 값
center = (lo + hi) / 2
v1, v2, v3 = (gen_measure(center, lo, hi, decimals) for _ in range(3))

# 셋 동일값 회피
if v1 == v2 == v3:
    v3 = gen_measure(center, lo, hi, decimals)
```

**핵심 정책**:
- ✅ 매일 다른 값 (시드 미고정)
- ✅ 중심값 근처 (σ=오차/3, ±3σ가 허용범위)
- ✅ 소수점 자릿수 = 스펙과 동일
- ✅ 셋 동일값 회피 (1회 재추첨)
- ❌ 균등분포 사용 금지
- ❌ 동일 시드 고정 금지

**입력**:
- 화면 우측 X1 클릭 → 숫자 입력 → v1
- X2 → v2, X3 → v3
- X1/X2/X3 OK 체크박스 (3개 모두)
- 결과 컬럼 OK 자동 표시 확인
- 우하단 "결과" 박스 OK 종합 확인

**Step 7-B: OK/NG 체크형**
- X1/X2/X3 입력칸 비움
- X1/X2/X3 OK 체크박스 (3개 모두)
- 결과 컬럼 3개 OK 표시 확인
- 우하단 "결과" 박스 OK 종합 확인

### Step 8 — 저장 시점 (첫 실행 학습)
- 후보 정책 3종:
  - (a) 검사항목 단위
  - (b) 공정 단위 (M개 끝나면 1회)
  - (c) 일괄 (N × ΣM 끝나고 1회)
- dry-run: 저장 클릭 X, 화면 캡쳐만
- commit: 결정된 정책으로 저장
- 저장 후 그리드 행 추가 확인

### Step 9 — 종료 보고
- 결과 요약: 제품 / 공정 N개 / 검사항목 M개 / 총 입력 행 / 저장 모드 / 실패 N건
- 결과 JSON: `90_공통기준/스킬/jobsetup-auto/state/run_<YYYYMMDD_HHMMSS>.json`

## 첫 실행 학습 항목
| 학습 항목 | 확정 상태 | 반영 위치 |
|----------|----------|----------|
| ~~제품/공정/검사항목 좌표~~ | ✅ v0.2 (1456×819) | `state/screen_analysis_20260429.md` |
| ~~공정 항목 N~~ | ✅ N=11 (1.RSP3SC0383_A) | 동상 |
| ~~공정당 검사항목 M~~ | ✅ 1~5개, 평균 1.5, 총 17 | 동상 |
| ~~스펙 텍스트 패턴~~ | ✅ 6종 (A1/A2/A3 + B1/B2/B3/B4) | Step 6 |
| 저장 단위 정책 | ⚠ 첫 dry-run 관찰 | Step 8 |
| ~~작업자 인증~~ | ✅ 단독 저장 가능 | Step 2 |
| ~~R5 롤백~~ | ✅ 재입력+재저장 | "되돌리기" |

## 안전 원칙
- **dry-run 기본값** (단독 호출 시): `--commit` 없이 저장 X
- **commit 가드**: dry-run PASS 1회+ + 사용자 명시 `--commit` 모두 충족 (단 `/d0-plan` hand-off는 예외)
- ~~무인 실행 금지~~ → **무인 자동 실행 허용** (`/d0-plan` SP3M3 morning hand-off 한정)
- **fail-fast 가드** (무인 시 필수):
  - SmartMES 미실행 → 종료 + jsonl 알림
  - 좌표 캘리브레이션 실패 → 종료
  - 스펙 매칭 실패율 > 50% → 부분 처리 후 종료 + 알림
  - 저장 후 빨간 에러 → 즉시 중단
- **단일 책임**: 첫 서열 1품번만 (2번째 이후 별도 호출)
- **스펙 매칭 실패 시 스킵** — 임의 추정값 X
- **부분 실패 허용**: 처리한 만큼 결과 JSON 기록
- **R5 롤백**: 재실행이 자동 덮어쓰기 = 자동 롤백

## 실패 조건
| 조건 | 판정 |
|------|------|
| SmartMES (mesclient.exe) 미실행 | FAIL |
| 제품 드롭다운 1번 항목 없음 | FAIL — D0 미완 의심 |
| 공정 드롭다운 N=0 | FAIL — 마스터 이상 |
| 스펙 매칭 실패율 > 50% | FAIL — 정규식 학습 부족 |
| 저장 후 그리드 행 추가 X | FAIL — 작업자 인증 거부 의심 |
| 좌표 캘리브레이션 실패 | FAIL |

## 중단 기준
- dry-run 화면 캡쳐 예상과 다름 → 즉시 중단 + 사용자 확인
- 저장 후 SmartMES 에러 다이얼로그 → 즉시 중단
- 좌표 클릭이 의도치 않은 위치(예: 종료) → 즉시 중단

## 검증 방법

### 1차 — dry-run
1. SmartMES `[J] 잡셋업` 진입
2. `/jobsetup-auto --dry-run`
3. 동작 시각 확인:
   - 제품 1번 ✓
   - 공정 N개 순회 ✓
   - 검사항목 M개 ✓
   - X1/X2/X3 허용오차 내 ✓
   - OK 체크 ✓
   - 저장 미클릭 ✓
4. 사용자 확인: "X1/X2/X3 허용범위 안인가? OK 체크 정확한가?"

### 2차 — commit 1건
1. dry-run PASS
2. `/jobsetup-auto --commit --max-items 1`
3. SmartMES 새로고침 → 정상 등록 확인
4. 정상이면 `--max-items` 제거하고 전체 commit 활성

### 3차 — 매일 아침 자동
1. `/d0-plan --session morning` SP3M3 분기 끝
2. hand-off 프롬프트에서 `dry` 또는 `y`
3. 사용자는 SmartMES 옆에서 시각 확인
4. 이상 발생 → 모드 E 진입 (자동화 중단 + 잔존 행 수동 삭제)

## 되돌리기
> 잡셋업은 같은 (제품/공정/검사항목)에 **재입력 → 재저장하면 정정** (별도 삭제 절차 X).

| 범위 | 방법 |
|------|------|
| 잘못 저장 1건 | 동일 검사항목 올바른 값 재입력 → 저장 (덮어쓰기) |
| 전체 일자 롤백 | `/jobsetup-auto --commit` 재실행 |
| 자동 롤백 | 별도 호출 X — 재실행 자체가 롤백 |

## 변경 이력
| 일자 | 버전 | 내용 |
|------|------|------|
| 2026-04-29 | v0.1 | 초기 (dry-run 전용) |
| 2026-04-29 | v0.1.1 | 검사항목 2종 분기 (A 측정값형 / B OK/NG형) |
| 2026-04-29 | v0.1.2 | R5 롤백 확정 (재입력+재저장) |
| 2026-04-29 | v0.2 | 선행 분석 — 1.RSP3SC0383_A 11공정 17항목 + 좌표 + 스펙 6종 |
| 2026-04-29 | v0.2.1 | 분포 강화 (균등 → 정규분포). 시드 미고정. 동일값 회피 |
| 2026-04-29 | v0.3 | 무인 자동 (사용자 확인 단계 제거). fail-fast 4종. `--no-jobsetup`/`--jobsetup-dry-run` |
| 2026-04-30 | v1.0 baseline | 결정적 결함 발견 + 실측 재설계. 정상 입력=numpad 시퀀스, 음수=`-` 키. 무인 chain 미구현. 매일 1번 품번 변경. 1456→1920 스케일 1.319. 단일 케이스만 보장 |
| 2026-05-02 | v3.0 | REST API 직호출 (UI 폐지). dnSpy 디컴파일로 endpoint+token+헤더 확보. POST `/v2/checksheet/check-result/jobsetup/save.api` + 헤더 7개 + JobSetupItem JSON. 17건/30초 |
| 2026-05-02 | v3.2 | config 외부화 + `--env dev|prod` 3순위 fallback (env → config.json → DEV_DEFAULT). config.example.json + .gitignore |
| 2026-05-02 | v3.3 | schedule API (POST `/v2/prdt/schdl/list.api`) dnSpy 추출. resolve_first_sequence + `--auto-resolve-pno` cross-check |

## 관련 문서
- 상위 plan: `C:\Users\User\.claude\plans\splendid-roaming-quilt.md`
- 트리거: `.claude/commands/d0-plan.md` (Step 4 다음)
- 모드 C: `.claude/rules/essentials.md`
- spec 마스터: `state/screen_analysis_20260429.md`, `state/schedule_api_spec_20260502.md`
- 외부 모델/운영: `.claude/rules/essentials.md`
