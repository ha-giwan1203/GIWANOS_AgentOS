# Round 1 — GPT 판정

의제: AGENTS_GUIDE hooks 파서 버그 수정 플랜 검증

판정: **조건부 통과**

## 보강 제안 3건 (전부 채택)

1. **PY_CMD fallback** — 하드코딩 `python3` 대신 doctor_lite.sh 선례 사용
   - `PY_CMD="python"; command -v python3 >/dev/null 2>&1 && PY_CMD="python3"`
   - 실증 근거: `doctor_lite.sh:10-11`

2. **헤더 문구 수정** — `"settings.local.json 기준"` → `"settings.json+settings.local.json 기준"`
   - 플랜이 team+local union을 읽으므로 표기 정합

3. **settings 부재 경고 1줄** — 둘 다 없으면 `[WARN] settings files missing` stderr
   - "정상 0"과 "환경 깨짐 0" 구분 보강

## 별건 분리 (합의)

- README 계층별 훅 테이블 파싱 → M5 후보
- SETTINGS dead assignment → 별건
- helper `--op hooks_total` 초소형 op → 지금 불필요

## 하네스

- 채택 3건: 실증됨(doctor_lite 선례 + union 표기 + 원인 은닉 방지)
- 버림 3건: 별건 분리 동의

## 분류 판정

A 분류 (명백한 버그 수정). 3자 승격 불필요 — GPT도 동의.
