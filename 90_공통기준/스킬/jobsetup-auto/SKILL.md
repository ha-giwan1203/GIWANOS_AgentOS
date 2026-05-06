---
name: jobsetup-auto
description: SmartMES 첫 서열 품번 자동 처리 (REST API v3.5). 작업자 배치 + 인증 + 잡셋업 17 검사항목 일괄. 첫 서열만 처리하면 나머지 자동 계승
trigger: "잡셋업 자동", "잡셋업 자동화", "잡셋업 입력 자동", "첫 서열 잡셋업", "작업자 배치 자동", "작업자 인증 자동"
grade: B
status: v3.5 (배치+인증+잡셋업 풀 자동화) - 세션143 작업자 배치/인증 통합
---

# SmartMES 잡셋업 자동 입력

> Step 1~9 절차 / spec 6종 / 안전 원칙 / 변경 이력은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## ⚠️ 자동화 책임
허용오차 내 정규분포 난수 입력. 사용자 본인 책임 운영. 잘못 저장 시 재입력+재저장으로 정정.
❌ NG 자동 체크 금지 (사람 판정만)

## 사용
```bash
/jobsetup-auto                      # 기본값 dry-run
/jobsetup-auto --commit             # 실 저장 (v1.0+)
/jobsetup-auto --process 1          # 첫 공정만
/jobsetup-auto --max-items 1        # 검사항목 1개만

# v3.x REST API 직접 (run_jobsetup.py)
python run_jobsetup.py --mode list-only             # default
python run_jobsetup.py --mode commit-all            # 17 검사항목 일괄
python run_jobsetup.py --auto-resolve-pno           # schedule API로 첫 서열 자동
python run_jobsetup.py --env prod                   # prod (env/config 필요)

# v3.4 (세션143): 작업자 인증 통합 - 새벽 자동화 미인증 문제 해결
python run_jobsetup.py --mode list-only --auto-resolve-pno --with-auth   # 인증 상태 점검
python run_jobsetup.py --mode dry-run  --auto-resolve-pno --with-auth    # 인증+잡셋업 페이로드 출력
python run_jobsetup.py --mode commit-all --auto-resolve-pno --with-auth  # 6공정 인증 + 17건 잡셋업

# v3.5 (세션143): 작업자 배치 통합 - 배치 미완료 시 자동 배치 (멱등 SKIP)
python run_jobsetup.py --mode list-only --auto-resolve-pno --with-assign --with-auth --shift D
python run_jobsetup.py --mode commit-all --auto-resolve-pno --with-assign --with-auth --shift D
# --shift: D(주간 01) / N(야간 02) / auto(시각 06~17 주간, 그 외 야간)
# --force-assign: 이미 배치돼있어도 강제 재배치 (사용 주의)
```

## 절차 (요약)
1. 모드 결정 + dry-run 가드
2. SmartMES 활성 또는 REST API endpoint 확인
3. 첫 서열 품번 (또는 schedule API `--auto-resolve-pno`) + regNo 자동 회수
4. **(v3.4 신규, --with-auth)** assign/list로 6공정 작업자 회수 → auth/cnfm/save.api로 인증 (이미 Y면 멱등 SKIP)
5. 잡셋업 list로 17 검사항목 회수
6. 스펙 6종 분류 → A형(정규분포 X1/X2/X3+OK) 또는 B형(OK만)
7. 저장 (commit 모드) 또는 화면 캡쳐 (dry-run)

## v3.4 + v3.5 통합 자동화 단계 (세션143 신규)

### 배경
새벽 자동화는 작업자 출근 전 실행. 잡셋업 데이터는 들어가지만 시스템상 wrkCertiYn=N 상태라 "저장 완료" 처리 안 됨. v3.3까지는 화면에 데이터만 보이고 그리드 미반영 → 사용자 재처리 필요.

### 정상 수동 순서 (사용자 확인, 세션143)
1. ERP 등록 → 작업자 배치(주간/야간 단위) → 작업자 인증(품번별) → 잡셋업

### v3.5 자동화 풀 흐름 (--with-assign --with-auth)
1. schedule API → 첫 서열 (pno/pnoRev/prdtRank/regNo/revNo) 자동 회수
2. **(--with-assign)** assign/list 현재 상태 점검 → 6공정 모두 wrkId 채워져있으면 SKIP, 아니면 assign-best/list로 추천 회수 → assign/save로 자동 배치
3. **(--with-auth)** assign/list → 6공정 wrkId 회수 → auth/cnfm/save.api 6건 호출. wrkCertiYn=Y면 SKIP
4. 잡셋업 list → save × 17건 → 정상 완료 처리

### 핵심 endpoint
- `POST /v2/prdt/schdl/list.api` (read-only) → 첫 서열 회수 [v3.3]
- `POST /v2/wrk/assign/list.api` (read-only) → 현재 배치 상태 [v3.4]
- `POST /v2/wrk/assign-best/list.api` (read-only) → 최적 배치 추천 [v3.5]. **shiftsCd "01"/"02" 필수**
- `POST /v2/wrk/assign/save.api` (state-modifying) → 배치 저장 [v3.5]. body는 List<WrkItem>
- `POST /v2/wrk/auth/cnfm/save.api` (state-modifying) → 인증 저장 [v3.4]
- `POST /v2/checksheet/check-result/jobsetup/{list,save}.api` → 잡셋업 [v3.0]

### shiftsCd 매핑
- `01` = 주간 (`--shift D`)
- `02` = 야간 (`--shift N`)
- `auto` = 06:00~17:59 주간, 그 외 야간

### 안전 가드
- `--with-assign` `--with-auth` 미사용 시 v3.3과 100% 동일 흐름 (회귀 위험 0)
- 배치 멱등성: 6공정 모두 wrkId 채워져있으면 SKIP (사용자 수동 배치 절대 덮어쓰기 안 함)
- 인증 멱등성: 이미 wrkCertiYn=Y인 공정은 SKIP
- `--force-assign`만 명시 시 강제 재배치 (사용 주의)
- commit-all에서 배치 실패 → exit 6, 인증 fail_count > 0 → exit 5 (잡셋업 진입 차단)

## verify
- list-only 응답 = done 17/17
- commit-all 후 SmartMES 화면 [40][60][91]×2[120][180][200]×5[210]×2[220][360][390][410] OK
- jsonl 결과: `state/run_v34_<YYYYMMDD_HHMMSS>.json` (v3.4) 또는 `run_v22_*` (v3.3 이하)

## 분포 정책 (핵심)
- 정규분포 `random.gauss`, σ=오차/3 (±3σ ≈ 99.7% 허용범위)
- 시드 미고정 (매일 다른 값)
- 셋 동일값 회피 1회 재추첨
- ❌ 균등분포 / 동일 시드 고정 금지

## 실패 시
- SmartMES 미실행 / 1번 품번 없음 / 매칭률 < 50% / 저장 후 그리드 미반영 → FAIL
- 되돌리기: 재실행 자체가 자동 롤백 (덮어쓰기)
- 상세 → MANUAL.md "안전 원칙" + "되돌리기"
