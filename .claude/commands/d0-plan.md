# /d0-plan — ERP D0추가생산지시 자동화 (SP3M3 + SD9A01)

> 스킬 원본: `90_공통기준/스킬/d0-production-plan/SKILL.md`

## 자연어 트리거 (자동 매칭)

다음 표현 나오면 **다른 탐색/도구 사용 전에 반드시 이 스킬로 위임**:
- "SP3M3 주간/야간 (계획) 반영/등록/올려/업로드"
- "SD9A01/아우터/OUTER (계획) 반영/등록"
- "D0 (추가생산지시) 반영/등록/올려/업로드"
- "생산계획 반영/등록/올려/업로드"
- "생산지시 반영/등록"

**금지**: Excel 파일 직접 열기, 모니터 전환, ERPSet Client(javaw.exe) 조작, computer-use로 마우스/키보드 조작.

## ⚠ incident 사전 점검 (advisory)

D0/OAuth/evidence_gate 미해결 건이 있으면 D0 흐름 진입 전 인용:
```bash
python .claude/hooks/incident_repair.py --json --limit 5
```
- **응답 시 필터링**: 출력 중 `classification_reason`이 `evidence_missing` / `auth_diag` / `oauth` / `D0` 이거나 `hook`이 `evidence_gate` / `scheduler` 인 항목만 인용 (Claude가 JSON 보고 자체 필터).
- 결과 인용 후 첨부 파일 가드로 진행. 차단 없음, 자동 수정 금지. (incident_quote.md 규칙 참조)

## ⛔ 첨부 파일 가드 (필수, 자동 실행 차단)

> 배경: 2026-04-27 사고 — 사용자가 중복 정리한 xlsx를 첨부했는데 스킬이 그걸 무시하고 Z 드라이브 원본(중복 포함)을 자동 추출 → ERP+MES에 중복 등록 발생. MES는 삭제 불가라 정정 어려움.

사용자 메시지에 **xlsx/xlsm 파일 첨부**(`@경로` 또는 시스템 첨부)가 있으면:
1. **스킬 자동 실행 금지** (Z 드라이브 자동 탐색 진행 금지)
2. 사용자에게 **명시적 확인 필수**:
   - (A) 첨부 파일을 사용 → `python run.py --xlsx "<첨부경로>" --line <SP3M3|SD9A01> --target-date <yyyy-mm-dd>`
   - (B) Z 드라이브 원본 자동 탐색 사용 → 통상 `--session` 모드
3. 사용자 답변 받은 후에만 진행. **추정해서 어느 한쪽 자동 선택 금지**.

판정 우선순위: **첨부 파일 존재 = 사용자 의도 우선** → 자동 실행보다 무조건 확인 먼저.

## 사용법

```
/d0-plan                            # 현재 시간대로 세션 자동 판정
/d0-plan --session evening          # 저녁 세션 (SP3M3 야간 + SD9A01 OUTER)
/d0-plan --session morning          # 아침 세션 (SP3M3 주간 3600 컷)
/d0-plan --dry-run                  # 추출+엑셀 생성까지만, 서버 저장 안 함
/d0-plan --line SP3M3               # SP3M3만
/d0-plan --line SD9A01               # SD9A01만 (저녁 세션)
/d0-plan --target-date 2026-04-24   # 파일명 날짜 명시
/d0-plan --session morning --no-jobsetup       # SP3M3 morning + 잡셋업 자동 실행 끄기
/d0-plan --session morning --jobsetup-dry-run  # SP3M3 morning + 잡셋업 dry-run으로
```

## 인수

- `$ARGUMENTS` — 옵션 조합 (session/line/dry-run/target-date)

## 실행 순서

1. 현재 날짜/시간 확인 (`date "+%Y-%m-%d %A %H:%M KST"`)
2. 세션 판정 (auto 시 06~10시=morning, 15~22시=evening)
3. 스킬 실행:
   ```bash
   cd "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/d0-production-plan"
   python run.py --session <session> [--line <line>] [--dry-run] [--target-date <yyyy-mm-dd>]
   ```
4. 결과 보고: 라인별 업로드/서열 배치 건수, MES 전송 결과, SmartMES 검증 결과
5. **잡셋업 자동 실행** (조건: `session=morning` AND `line ⊇ SP3M3` AND `--dry-run` 아님 AND `--no-jobsetup` 아님 AND SmartMES 검증 PASS):
   - **사용자 확인 없이 즉시** `/jobsetup-auto --commit` 자동 호출 (사용자 답변 2026-04-29: "계획 반영 완료 판정 후 바로 실행되는 구조")
   - 1줄 인지 라인만 출력: `[auto] SP3M3 D0 morning PASS → /jobsetup-auto --commit 자동 실행 (약 2분, SmartMES 화면 점유)`
   - 잡셋업 스킬 자체 가드:
     - SmartMES (mesclient.exe) 미실행 → 자체 fail-fast + jsonl 알림
     - 좌표 캘리브레이션 실패(해상도 변경 의심) → fail-fast
     - 스펙 매칭 실패율 > 50% → 부분 처리 + 알림
   - 잡셋업 결과 jsonl: `90_공통기준/스킬/jobsetup-auto/state/run_<YYYYMMDD>.json` 자동 기록
   - **끄기**: `/d0-plan --session morning --no-jobsetup`
   - **dry-run**: `/d0-plan --session morning --jobsetup-dry-run` (→ `/jobsetup-auto --dry-run` 호출)
   - 잡셋업 자동화는 별도 스킬 책임 — 본 d0-plan 본체 동작에 영향 없음.

## 선결 조건

- Chrome CDP 9223 (스킬이 없으면 자동 기동)
- ERP OAuth 자동 로그인 (저장 자격증명 0109)
- Z 드라이브 접근 (`\\210.216.217.180\zz-group`)
- Python 의존성: pyautogui, playwright, openpyxl

## 안전 원칙

- 실 저장 전 dry-run 권장 (처음 실행 시)
- OUTER(SD9A01)/주간은 실운영 추가 검증 후 활성화 권장
- 중복 저장 방지: 같은 EXT_PLAN_REG_NO는 rank_batch에서 자동 스킵
- 실패 3회 누적 시 최종 저장 보류
