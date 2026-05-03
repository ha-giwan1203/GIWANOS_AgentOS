---
name: jobsetup-auto
description: SmartMES 잡셋업 첫 서열 품번 자동 입력 (REST API v3.x). 17 검사항목/30초. 첫 서열만 등록하면 나머지 자동 계승
trigger: "잡셋업 자동", "잡셋업 자동화", "잡셋업 입력 자동", "첫 서열 잡셋업"
grade: B
status: v3.3 (REST API + auto-resolve-pno) — UI 자동화 폐지 완료
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
```

## 절차 (요약)
1. 모드 결정 + dry-run 가드
2. SmartMES 활성 또는 REST API endpoint 확인
3. 첫 서열 품번 (또는 schedule API `--auto-resolve-pno`)
4. 공정 N 순회 + 각 공정 검사항목 M 처리
5. 스펙 6종 분류 → A형(정규분포 X1/X2/X3+OK) 또는 B형(OK만)
6. 저장 (commit 모드) 또는 화면 캡쳐 (dry-run)

## verify
- list-only 응답 = done 17/17
- commit-all 후 SmartMES 화면 [40][60][91]×2[120][180][200]×5[210]×2[220][360][390][410] OK
- jsonl 결과: `state/run_<YYYYMMDD_HHMMSS>.json`

## 분포 정책 (핵심)
- 정규분포 `random.gauss`, σ=오차/3 (±3σ ≈ 99.7% 허용범위)
- 시드 미고정 (매일 다른 값)
- 셋 동일값 회피 1회 재추첨
- ❌ 균등분포 / 동일 시드 고정 금지

## 실패 시
- SmartMES 미실행 / 1번 품번 없음 / 매칭률 < 50% / 저장 후 그리드 미반영 → FAIL
- 되돌리기: 재실행 자체가 자동 롤백 (덮어쓰기)
- 상세 → MANUAL.md "안전 원칙" + "되돌리기"
