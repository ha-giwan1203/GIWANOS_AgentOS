---
name: jobsetup-auto
description: SmartMES 첫 서열 품번의 잡셋업 17 검사항목 자동 입력 (REST API v3.3). 작업자 배치/인증은 별도 — 관리자가 SmartMES UI에서 처리한 뒤 본 자동화 호출
trigger: "잡셋업 자동", "잡셋업 자동화", "잡셋업 입력 자동", "첫 서열 잡셋업"
grade: B
status: v3.3 (잡셋업 17 검사항목 자동 입력 단독). v3.4/v3.5(작업자 배치+인증 통합)는 폐기 — MANUAL.md 결정 출처(작업자 인증 별도)와 충돌
---

# SmartMES 잡셋업 자동 입력

> Step 1~9 절차 / spec 6종 / 안전 원칙 / 변경 이력은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## ⚠️ 자동화 책임
허용오차 내 정규분포 난수 입력. 사용자 본인 책임 운영. 잘못 저장 시 재입력+재저장으로 정정.
❌ NG 자동 체크 금지 (사람 판정만)

## 선결 조건 (관리자 수동 작업)
본 자동화는 **잡셋업 17 검사항목 입력만** 담당한다. 다음은 관리자가 SmartMES UI에서 사전 처리:
1. 작업자 배치 (UI "최적배치" 버튼 → 매일 고정 6명 자동 박힘)
2. 작업자 인증 (공정별 wrkCertiYn=Y 확인)

위 두 단계가 끝나지 않은 상태에서 본 자동화를 호출하면 잡셋업 데이터는 저장되지만 그리드 미반영(미완료) 처리될 수 있다.

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
```

## 절차 (요약)
1. 모드 결정 + dry-run 가드
2. SmartMES 활성 또는 REST API endpoint 확인
3. 첫 서열 품번 (또는 schedule API `--auto-resolve-pno`) + regNo 자동 회수
4. 잡셋업 list로 17 검사항목 회수
5. 스펙 6종 분류 → A형(정규분포 X1/X2/X3+OK) 또는 B형(OK만)
6. 저장 (commit 모드) 또는 화면 캡쳐 (dry-run)

### 핵심 endpoint
- `POST /v2/prdt/schdl/list.api` (read-only) → 첫 서열 회수 [v3.3]
- `POST /v2/checksheet/check-result/jobsetup/{list,save}.api` → 잡셋업 [v3.0]

## verify
- list-only 응답 = done 17/17
- commit-all 후 SmartMES 화면 [40][60][91]×2[120][180][200]×5[210]×2[220][360][390][410] OK
- jsonl 결과: `state/run_v3_<YYYYMMDD_HHMMSS>.json`

## 분포 정책 (핵심)
- 정규분포 `random.gauss`, σ=오차/3 (±3σ ≈ 99.7% 허용범위)
- 시드 미고정 (매일 다른 값)
- 셋 동일값 회피 1회 재추첨
- ❌ 균등분포 / 동일 시드 고정 금지

## 실패 시
- SmartMES 미실행 / 1번 품번 없음 / 매칭률 < 50% / 저장 후 그리드 미반영 → FAIL
- 그리드 미반영 = 관리자 작업자 배치/인증 미선행 의심 → SmartMES UI 확인
- 되돌리기: 재실행 자체가 자동 롤백 (덮어쓰기)
- 상세 → MANUAL.md "안전 원칙" + "되돌리기"

## v3.4/v3.5 폐기 사유 (2026-05-15)
- v3.4: `--with-auth` 작업자 인증 통합 시도
- v3.5: `--with-assign` 작업자 배치 통합 시도
- 새벽 자동화 호출 시점(07:11)에 작업자 마스터 풀이 비어있어 assign-best API가 빈 wrkId 추천 반환 → assign/save 200 가짜 성공 → wrkId 미반영 → ABORT (5/11·12·15 3회 연속 실패)
- 근본: MANUAL.md 결정 출처상 "작업자 인증 = 별도 (잡셋업 단독 가능)"가 사용자 답변이며, v3.4/v3.5의 통합 자체가 원래 설계와 충돌
- 해법: v3.3 단독 동작으로 복귀. 작업자 배치/인증은 관리자가 SmartMES UI "최적배치" 버튼으로 매일 새벽 처리
