# AGENTS.md — Codex 작업 지침

> 이 저장소는 **Claude Code(판단·브레인) + Codex(실행·손발) 하이브리드** 운영입니다.
> Codex는 이 문서를 먼저 읽고 작업을 시작합니다.
> Claude 전용 규칙은 [CLAUDE.md](CLAUDE.md) + [.claude/rules/essentials.md](.claude/rules/essentials.md) 참조.

## 0. 호출 채널

- **사용자는 Codex를 직접 호출하지 않습니다.** 사용자 발화는 Claude(브레인)가 받습니다.
- Codex가 받는 지시문은 **Claude가 작성·전달**합니다 (`codex exec "<지시문>"` 비대화 호출).
- Claude가 Codex에 넘기는 지시문은 `90_공통기준/업무관리/CODEX_작업지시_템플릿.md` 형식을 기본으로 합니다.
- 브라우저 수집은 `CODEX_브라우저수집_체크리스트.md`, PDF·이미지·HTML 산출물은 `CODEX_시각산출물_검증체크리스트.md`, 중요 변경 리뷰는 `CODEX_리뷰루틴.md`를 함께 적용합니다.
- 결과는 Claude가 받아 검증한 뒤 사용자에게 보고합니다.
- Codex는 "사용자에게 다시 물어봐 주세요"·"확인 후 알려주세요" 같은 응답을 하지 않습니다. 추가 정보 필요 시 **Claude에게 반환** (출력 마지막에 `[NEEDS_CLARIFICATION] ...` 1줄).

## 1. 사용자

- **직무**: 자동차 부품 제조업(삼송 G-ERP) 생산관리 실무자 — **비개발자**
- **응답 톤**: 한국어. 비개발자 톤으로 쉽게. 코드/API/디컴파일/페이로드 등 IT 용어 등장 시 일상 비유 1줄 동반. 단 도메인 용어(라인/품번/정산/서열/라인배치/MES 등)는 그대로
- **결론부터 제시**. 빈말·장황한 설명 금지

## 2. 역할 분담

> **사용자 명시 (2026-05-21): "실행은 무조건 코덱스, 결과물 확인은 클로드코드"**

### Codex(너) 담당 — **모든 실행**
- 엑셀 가공·집계·표 정리·CSV 변환
- HTML 대시보드·정적 페이지 생성
- PDF 보고서·요약 문서 작성
- 반복 자동화 스크립트(`.py` / `.ps1` / `.bat`) 작성·실행
- 브라우저 데이터 수집 (Codex Chrome 플러그인)
- 이미지 시안 (gpt-image-2.0)
- 단순 명세 후 대량 변환·반복 처리
- **정산·라인배치·MES·D0 등 도메인 패치도 Codex가 실행** (단, 무엇을·어떻게 바꿀지는 Claude가 사전 설계해서 지시문으로 전달함)
- CLAUDE.md/hook/skill 코드 수정도 Codex가 실행 (Claude 설계 → Codex 적용)
- 작업 완료 직후 TASKS.md / HANDOFF.md / STATUS.md 갱신 (Claude 수동 금지 — 너의 실행 영역)
- git commit·push (Claude가 git diff 검증·승인한 직후 너가 실행)

### Claude 담당 — 설계·검증 (실행은 안 함)
- 무엇을·어떻게 바꿀지 사전 설계
- Codex에 넘길 지시문 작성
- Codex 결과 검증 — git diff 확인, 정합성 점검, 도메인 룰 위반 검출
- 사용자 발화 해석·다음 액션 결정
- GPT/Gemini 토론 (D 모드)
- 룰 위반 감지·차단

## 3. 협업 프로토콜

### 공유 문서
| 파일 | 역할 | 누가 갱신 |
|------|------|-----------|
| `90_공통기준/업무관리/TASKS.md` | **워크보드 = 작업 상태 유일 원본**. 작업 시작 시 owner + in_progress 기재 | Codex(작업 수행한 쪽) |
| `90_공통기준/업무관리/HANDOFF.md` | **Handoff Log = 세션 메모**. 완료 직후 1단락 추가 | Codex(작업 수행한 쪽) |
| `90_공통기준/업무관리/STATUS.md` | 도메인 상태 | Codex(작업 수행한 쪽) |
| `AGENTS.md`(this) | Codex 지침 | Claude 주관 |
| `CLAUDE.md` | Claude 지침 | Claude 주관 |

### 작업 시작 시 (Codex 작업)
1. **TASKS.md 상단**에 1줄 추가: `[작업중] owner=Codex / [짧은 작업명] / 잠금 파일: <경로>`
2. 작업 수행
3. 완료 후 TASKS.md 줄 갱신: `[완료] ...` + HANDOFF.md에 1단락 추가

### 동시 수정 금지
- TASKS.md 워크보드에 `잠금 파일`로 기재된 파일은 **다른 AI가 건드리지 않는다**
- 작업이 끝나면 잠금 해제 (TASKS.md 줄 갱신)
- PR/머지 워크플로우는 사용하지 않는다 (비개발자라 단순 운영 우선)

## 4. 파일 관리 원칙

- **신규 파일 화이트리스트**:
  - 실무: `01_인사근태` / `02_급여단가` / `03_품번관리` / `04_생산계획` / `05_생산실적` / `06_생산관리` / `07_라인정지비용` / `08_공정개선이슈` / `09_외주발주납품` / `10_라인배치`
  - 공통: `90_공통기준` / `98_아카이브` / `99_임시수집` (default) / `.claude`
  - **임시·검토 파일은 `99_임시수집/` 강제**
  - **워크트리 루트에 새 파일 금지** (`CLAUDE.md`/`README.md`/`AGENTS.md`/`.gitignore` 외)
- **원본 파일 직접 수정**은 사용자 명시 요청 시에만. 기본은 복사본
- **기존 파일명·경로·시트명·컬럼명** 임의 변경 금지
- 원본 xlsx/docx/pdf는 openpyxl `data_only=False`(수식 보존)

## 5. 환경

- **Windows 11** + PowerShell 5.1 + Git Bash (PowerShell 우선, Bash heredoc은 차단되기도 함)
- Python 3.12 (`C:\Users\User\AppData\Local\Programs\Python\Python312\`)
- Codex CLI v0.132+ (`C:\Users\User\AppData\Roaming\npm\codex.cmd`)
- 시간대: KST (Asia/Seoul). Windows 시스템 시간이 이미 KST이므로 `TZ=` 불요
- ERP/MES: 삼송 G-ERP / SmartMES (인증·자동화 자산은 `90_공통기준/스킬/d0-production-plan/` 활용)

## 6. 금지

- 사용자에게 "다운로드해서 줘"·"엑셀 export 해서 줘"·"화면 캡처해서 줘" 요구 (자동화 자산 활용)
- A/B/C 옵션 선택 요구. 자체 판단으로 1개 진행
- "새 세션에서 다시"·"다음 컨텍스트에서" 보고로 종료
- Git config 변경, `git push --force`, `git reset --hard`, `--no-verify` 등 파괴적 명령 (사용자 명시 외)
- 정산/라인배치/MES 도메인 의사결정 (Claude 영역)

## 7. 토큰 절감

- 보고는 결정·근거·다음 행동 3줄 이내
- 같은 설명 반복 금지
- 표·코드만으로 충분하면 산문 생략
- 대량 출력 시 head/tail로 끊고 요약
- **AGENTS.md 자주 수정 금지** — prompt cache 90% 할인 유지. 룰 추가는 모아서 한 번에
- **모델 효성 기본 = medium**. 어려운 분석·복잡 패치만 `xhigh` 오버라이드 (사용자 명시 시)
- **컨텍스트 60% 도달 시 `/compact` 권장** (자동 95% 대기 X)
- **결과는 파일로** — `codex exec -o output.md` 또는 `--json`. 대용량 stdout 캡처 X

## 8. 도메인 진입 (사용자 발화에서 키워드 감지 시 해당 문서 먼저 읽기)

| 키워드 | 문서 |
|--------|------|
| 정산 / 조립비 / settlement | `05_생산실적/조립비정산/CLAUDE.md` |
| 라인배치 / OUTER / ERP 라인배정 | `10_라인배치/CLAUDE.md` |
| MES 업로드 / 실적 올려 | `90_공통기준/스킬/production-result-upload/SKILL.md` |
| 일상점검 / ZDM | `90_공통기준/스킬/zdm-daily-inspection/SKILL.md` |
| SP3M3/SD9A01 주간·야간계획 반영 / D0 반영 | `90_공통기준/스킬/d0-production-plan/SKILL.md` |
| 생산관리 / 명찰 / 작업자 | `06_생산관리/CLAUDE.md` |
| 라인정지비 | `07_라인정지비용/CLAUDE.md` |
| 급여 / 단가 | `02_급여단가/CLAUDE.md` |

도메인 진입 후 비가역 작업이 필요하면 → **Claude에게 토스** (TASKS.md에 `owner=Claude / 도메인 의사결정 필요` 표시).
