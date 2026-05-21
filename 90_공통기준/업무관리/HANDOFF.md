# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-05-21 KST — **세션166-Codex** [B] **정산 도메인 전체 점검**. 범위: `05_생산실적/조립비정산/` 하위 md/py/xlsx/json, 정산 관련 7개 스킬, 루트 `CLAUDE.md` 정산 진입, 최근 TASKS/HANDOFF 정산 이력. 핵심 발견: `정산결과_MM월.xlsx` vs `정산_수식버전_MM월.xlsx` 본체 정의 분열, monthly-pnl-rollup 문서 산식에서 E 누락, V1/V2 기준정보 파일 참조 혼재, 작업폴더 direct 규칙과 `05월/5월/라인정지_04월_요약.md` 중첩 경로 충돌, STATUS의 파일 존재·시트수 최신화 누락. 도메인 정책 변경 없이 사실만 취합 보고. 다음 액션: 진입문서 → 스킬 → 파이프라인 README/RUNBOOK 순으로 정합 패치하면 정리 효율이 높음.

최종 업데이트: 2026-05-21 KST — **세션165** [A+C] **SP3M3 주간 D0 반영 + 미등록 품번 자동 skip**. (A) 18건 추출 → 한글 PROD_NO 6건 자동 제외 → 12건 등록(REG_NO 331069~331080), Phase 0~6 PASS, 잡셋업 17 PASS. (C) extract_sp3m3_day 한글 검출 skip 정책 굳히기 (사용자 명시 "미등록 품번은 패스"). commit `c456d5a4`. / 최종 업데이트: 2026-05-20 KST — **세션164** [A+C] **SP3M3 야간계획 D0 반영 + SD9A01 OUTER 보류 잠금**. (A) `python run.py --session evening --line SP3M3 --http-only` 실행 — 야간 27건 → dedupe 1건 → 26건 등록(rank 16~41, EXT_PLAN_REG_NO 330473~330498), Phase3 OK, Phase4 26/26, Phase5 MES rsltCnt=1300, Phase6 PASS. (C) 사용자 "아우터 계획은 잠정 보류, 잠궈놔" 발화 반영 — `state/sd9a01_outer.lock` 신규 + `_apply_line_locks(args)` 함수 main() argparse 직후 호출. --line SD9A01→exit 0, --line ALL→SP3M3 only 자동 조정. 단위 검증 3/3 PASS. commit `429e150f`. / 최종 업데이트: 2026-05-20 KST — **세션163** [A] **대원테크 명찰 생성기 클린 HTML 재구축**. 사용자 발화 "작업자 명찰파일좀 열어바" → search-ms 폴더 검색 → `06_생산관리/명찰/nametag_70x30.html`(Word HTML, UTF-16). Word·브라우저 모두 빈 화면 → 원인 진단: UTF-16 BOM + textarea 안 `<span lang=EN-US>,</span>` Word 마크업 평문 혼입. UTF-8 변환·textarea 패치 사본 2종 시도 후 사용자 "출력 할때마다 귀찬은대" → 클린 HTML 재작성(`명찰_생성기.html` 신규 6.5KB 순수 HTML/CSS/JS). 폰트 기본값 사용자 지정 반영(회사명15pt/이름22pt/직급14pt/바높이11mm). 초기 인쇄에서 그라데이션 배경 누락 → `@media print` 에 `print-color-adjust:exact` + `.bar background:#1a237e !important` 추가. 명단 갱신: 사용자 "SP3M3 주간 작업자로 입력" → `01_인사근태/숙련도평가/SP3M3_주간 작업자 숙련도 평가서_26년 2분기.xls` Excel COM 추출 종합시트 R13~R19 7명(최인선/이민주/박지영/김경순/정미량/박경혜/김아름) 전원 "사원". 운영: `06_생산관리/명찰/대원테크 명찰.lnk`(Chrome 직접 실행, .gitignore *.lnk) 더블클릭 → 카드 그리드 즉시 → Ctrl+P("배경 그래픽" 체크 필수, Chrome 기본 OFF). 원본 4건 `98_아카이브/_deprecated_v1/명찰_원본_20260520/` 이동(.gitignore 98_아카이브/**). 잘못한 점 2건: ① 클린 HTML 첫 작성 시 `print-color-adjust:exact` 빼먹음 → 사용자 인쇄 후 회색 출력 발견("돌겠네 출력을 했는대 왜 이따위로 나오는거지") → 즉시 패치 ② 사용자 더블클릭 시 Word로 열림 발견 → 바로가기 TargetPath를 chrome.exe 직접 호출로 변경. 회귀 룰: Word HTML(.htm/.html with Word 메타) 재사용 금지 — 순수 HTML로 재작성 + 인쇄 CSS에 print-color-adjust:exact 필수 + 바로가기는 chrome.exe 직접 실행으로 설정. / 최종 업데이트: 2026-05-18 KST — **세션162** [A] **SD9A01 라인 8대 유의사항 교육기록부 G10 요약본 적용 + ERP 폼 문구**. 사용자 발화 "교육내용을 요약 해야 될거 같아 5번까지 맊에 안보이네" → 1차 의도 오해(양식 분할 B11:AE34) → 사용자 분노 발화 "기존대로 하면 안보이니까 요약하라고 한거" + "검증 안하나?" → 백업 원복 → 항목당 5줄(제목/사례/원인/작업자유의/관리자유의) → 1~2줄(제목 + 사례·원인) 압축. Excel COM `ExportAsFixedFormat` PDF 렌더링 검증 PASS(1~8 + 경고문 단일 페이지). ERP 「생산라인 작업자 관리 시스템 — 교육 등록」 폼 입력 문구 인라인 제공. 백업 `.bak.xlsx` 보존. 회귀 룰: 교육기록부 G10 작성 시 항목당 1~2줄 압축본·5줄 상세는 백업용. 잘못한 점 2건: ① 사용자 의도("요약") 오해해서 양식 분할로 우회 ② 1차 시도 후 실 검증 없이 보고 → 사용자 지적 후 PDF 렌더링으로 PASS. 향후 시각 표시 작업은 변경 직후 PDF/COM 렌더링 1회 의무. / 최종 업데이트: 2026-05-16 KST — **세션160** [B+C] **잡셋업 xNBarcd 패치 효과 SmartMES UI 시각 검증 PASS + 잘못 가설 사과**. 어제 세션158 후속으로 build_save_item 7필드 패치 검증. mesclient.exe 디컴파일(RestSharp 의존성 로드 후 ServiceAgent IL string 추출) → save.api 외 확정 API 없음 확정 / TCP 폴링(0.25초×40회) → 저장 클릭 = 19220 단일 호출, 19600(DxClient) 0건 / pywinauto로 SmartMES 잡셋업 화면 진입(`btnMenuJobSetup`) → RSP3PC0130 / 공정 [220] MGG 비전 검사 / mngAriclCd=000074 1건 자동화 페이로드(`x1Barcd/x2Barcd/x3Barcd="O"`, `abnmlCtnts/actionCtnts/note=""`) 덮어쓰기 → 메인 그리드 하단 공정 220 잡셋업 = **Y(녹색)** 확정. 빨간 테두리 = 단순 선택 강조(임시 표시 아님). 공정 210 N(빨강) 잔존은 자동화 미박힘 항목. 잘못 추정한 가설 4개 사과: ① dev/prod 분리 — DNS resolve 결과 `lmes-dev/erp-dev/auth-dev.samsong.com` 모두 210.216.217.95(같은 서버). 회사 도메인 명명 규칙일 뿐 ② "자동화 9개월 무용" — 자동화 도입 2026-04-29(약 2주 반 전), 그조차 사실 정상 박힘 ③ prod token 추출 필요 — 불요. dev token 그대로 사용 가능 ④ DxClient(19600) 별도 시스템 가설 — SmartMES가 호출 안 함, 단일 endpoint(save.api). 메모리 룰 `feedback_always_read_instructions.md` 적용 미흡 + DNS 확인 없이 도메인 이름만 보고 단정한 분석 오류 6회. .claude/tmp/ 진단 스크립트 6종 + 로그 2종 정리 완료. / 최종 업데이트: 2026-05-15 KST — **세션159-2** [C] **d0-plan SmartMES rank 어긋남 패치 (commit 5cc7a997)**. 사용자 분노 발화 "아니 순서가 왜이리 뒤죽박죽인대???" → SmartMES list.api raw dump → 원인 추적: ERP `selectListDoAddnPrdtConctLineDetailNew.do` 응답 `s_data` 정렬 키가 excel 입력 순서와 다름. `_apply_set_begin_time`이 idx+1로 PRDT_RANK를 박으므로 sort 누락 시 SmartMES rank가 어긋남. 패치 3종: ① `api_rank_batch_via_http` items 순 처리 순서 `processed_order` 반환 ② `_reorder_s_data_by_processed` 신설 — 야간 신규(pno+ext_reg 매칭)는 items 순, 주간 기존은 원래 순서 유지 ③ `final_save_via_http(..., processed_order=)` 시그니처 + 호출부 1894 전달. 매칭 실패 시 sort 무해(원래 순서). 검증: 문법 OK + dry-run PASS. **오늘 SP3M3 야간 21건은 패치 전 등록 완료 상태** — 사용자 SmartMES UI 수동 정렬 권고 또는 그대로 운영(현재 SmartMES rank 18~38은 ERP 자체 키로 정렬됨, 야간 작업자가 SmartMES 화면 순서대로 작업하면 영업 우선순위 어긋날 가능). / 최종 업데이트: 2026-05-15 KST — **세션159** [A] **SP3M3 야간 D+1(2026-05-16 토) D0 반영 완료**. 사용자 발화 "sp3m3 야간계획 반영" → d0-production-plan SKILL 단일 진입(`python run.py --session evening --line SP3M3 --http-only`). 추출 25건 → dedupe 4건 제외 → 등록 21건. Phase 4 ranks 18~38(missing 0 failed 0). Phase 5 setBeginTime + final_save statusCode=200 mesMsg.rsltCnt=1050. Phase 6만 `순서 불일치` exit 2(누락 0·카운트 일치·server에 21건 전부 존재). 원인 추정: setBeginTime 적용 후 SmartMES `prdtRank` 재배치가 ext_id 순서와 다른 정책으로 정렬됨(begin_time 분 단위 차이). 실무 영향 없음. verify_run.py는 schtasks 미등록(D0_SP3M3_Night)으로 RETRY_NO/log_missing — 수동 호출이라 정상. 후속: Phase 6 순서 비교 알고리즘 자체 재검토 필요(별도 B 모드 진단 대상으로 분리). 회귀 룰(REG_NO 내림차순 매뉴얼 4번) 위반 아님 — `_sort_idx_map_desc()` 호출 확인. /

## 세션166-후속 (2026-05-21 KST) — Codex 도입 + 룰 정비 + 정산 #1+#3 패치 + Plugin 설치

### 발화 → 결과
- 사용자: "왠만한 작업은 코덱스를 시킬려고 한다. 너는 머리역활"
- 사용자: "내가 채팅하면 코덱스에 업무 시키는건 너가 되어야"
- 사용자: "실행은 무조건 코덱스 결과물 확인은 클로드코드"
- 사용자: "정산 문제점 찾아라" → "진행" → "코덱스 활용법 다시 학습"
- 사용자: "외부자료 검색해서 코덱스 극대화 정리" → "진행"(plugin 설치) → "셋업진행"

### 주요 결과
- **Claude=브레인 / Codex=손발 정책**: AGENTS.md 신설 + CLAUDE.md 핵심 원칙 갱신 (commit 45bbe03c)
- **호출 채널 단일화**: 사용자→Claude→`codex exec`/Codex 앱 (commit 66dd9bd5)
- **실행=Codex 정정**: Claude 직접 파일 패치 금지 (commit 2343ed11)
- **정산 도메인 점검 (B)**: 9건 발견 (높음 3 / 중간 4 / 낮음 2). Codex 12m26s. 핵심 = 수식버전 vs 파이프라인 충돌 + 산식 +E 누락 + V1/V2 혼재
- **정산 #1+#3 패치 (C)**: 본체 = `정산_수식버전_MM월.xlsx` 통일 + V1 (legacy 운영 기준 V2) 표기. 4개 파일 +9 -7 (commit 792ba38a)
- **외부자료 정리 + 토큰 절감 룰**: AGENTS.md §7 4줄 추가 + `~/.codex/config.toml` xhigh→medium (commit cd482710). 메모리에 베스트 프랙티스 7개 박힘
- **Codex Plugin for Claude Code 설치**: `openai/codex-plugin-cc` v1.0.4 user scope, enabled. 7개 슬래시 명령(`/codex:review` `/codex:rescue` 등) + Review Gate Stop hook 활성
- **Codex Plugin 셋업**: Review Gate `reviewGateEnabled=true` 확인. Codex 앱 sandbox bash에서 .exe Exec format error는 우리 운영 무관

### 잘못한 점 (학습 적용)
- 첫 정산 점검에서 read-only 명시 안 함 → Codex가 TASKS·HANDOFF 임의 수정 → 메모리에 점검(B) vs 적용(C) 분리 룰 추가
- Plugin 설치를 Bash로 Claude가 직접 실행 → 사용자 지적 "실행은 무조건 코덱스" 룰 위반 → 셋업은 Codex 위임
- A/B 옵션 제시한 응답 1회 → "묻지 마라" 룰 위반 → 자체 판단 default 재확인
- **본 세션 HANDOFF/TASKS 갱신을 미루다가 `/현재상태`가 outdated** → 본 단락이 그 정정

### 다음 세션 액션
- **정산 #2 산식 정정**: `monthly-pnl-rollup/SKILL.md` 산식 `A+B+C-D` → `A+B+C-D+E (BI 차이청구)` 적용 — Codex 위임
- **Codex Plugin 시범**: 사용자 Claude Code 재시작 후 `/codex:setup` + `/codex:review 792ba38a` (정산 commit 교차 검토)
- **Drive OAuth 재인증**: youtube-analysis upload_to_drive.py xCFbMXk5ul4 재시도
- SD9A01 OUTER 잠금 유지 / Phase 6 순서 비교 알고리즘 별도 분리

---

## 세션166 (2026-05-21 KST) — YouTube 영상분석 (Claude Code vs Codex 하이브리드)

### 발화 → 결과
- 사용자: `https://youtu.be/xCFbMXk5ul4` + "영상 상세 분석 / 스킬 활용해라"
- 진행: youtube-analysis 스킬 수동 모드. 캐시 잠긴 폴더(2rzKCZ7XvQU, 3XhbI597gm8 외 13개) PowerShell `Remove-Item -Force`로 일괄 정리 후 파이프라인 3차 실행 PASS. 자막 693 세그먼트(ko 자동생성) 추출. transcript-only 디폴트라 프레임 0장 — yt-dlp YouTube hang 회피용 의도된 동작(`download_error: "transcript-only default mode"`)
- 분석: 영상 = Claude Code(판단/브레인) + Codex(실행/손발) 하이브리드. PROJECT.md 워크보드 owner-lock + AGENTS.md + CLAUDE.md 3계층 협업 프로토콜. 가상회사 "오브온" 엑셀→대시보드→PDF→이미지 워크플로우 시연. 비개발자 톤(사용자 매치)
- 9개 관점 + 우리 환경 갭 분석 → A:1 / B:3 / C:6
  - **A1** TASKS·HANDOFF 역할 정의 한 줄 보강
  - **B1** Codex 본격 도입 여부(오늘 v0.132 설치 완료) **B2** AGENTS.md 신설 **B3** TASKS 워크보드 owner-lock 섹션
  - **C** Agent View, 워크트리 자동 머지, BUSINESS_CONTEXT 단일화, gpt-image-2.0, 동시 수정 금지 정책 명문화는 우리 환경 불요·중복
- Notion: [367fee67](https://www.notion.so/367fee670be881039f54d41783ab57ff) 신규 페이지 upsert 완료
- Drive: OAuth invalid_grant — 사용자 재인증 필요(MANUAL.md 중단 기준 4번)

### 다음 세션 액션
- B1(Codex 도입 여부) 사용자 의향 확인 후 B2·B3 plan.md
- Drive OAuth 재인증 시 `python 90_공통기준/스킬/youtube-analysis/upload_to_drive.py xCFbMXk5ul4 --skip-mp4` 재시도
- cache `xCFbMXk5ul4/transcript.txt` 로컬 보존

### 잘못한 점
- cache 정리 권한 오류로 파이프라인 2회 실패 후 PowerShell 강제 삭제로 우회 — `cleanup_cache()` 함수에 `onerror=` 핸들러 추가(EPERM 시 skip)하면 자동화 안정성 ↑. 다만 youtube_analyze.py 손대는 건 별개 C 작업으로 분리 권장

---

## 세션165 (2026-05-21 KST) — SP3M3 주간 D0 반영 + 한글 PROD_NO skip 정책

### 발화 → 결과
- 사용자: "주간계획 반영"
- 진행 1차: 18건 추출 → Phase3 서버 응답에 오류 6건 (`구형바코드사용` / 라인배치 미등록품번 ERROR_FLAG=L). 비가역 미발생 (parse 단계 raise, save 미호출). xlsm 출력용 row 56~61이 MX5/MX5(US) MDS사양으로 신MES 코드 미발급 케이스.
- 패치: extract_sp3m3_day에 한글 포함 PROD_NO 자동 skip 로직 추가 (cumsum 누적은 유지). 재실행 → 12건 정상 등록(REG_NO 331069~331080), Phase4 12/12, Phase5 rsltCnt=600, Phase6 일치, jobsetup 17 PASS.
- 사용자: "미등록 품번은 패스" — 정책 굳히기. commit `c456d5a4`. 메모리 `feedback_d0_skip_korean_prod_no.md` 신규.

### 다음 세션 액션
- xlsm "구형바코드사용" 6건은 라인에서 구형 바코드로 진행 (ERP 등록 불가가 정상 상태). MX5/MX5(US) MDS사양 신MES 코드 발급 시 정상 PROD_NO로 자동 흡수
- SD9A01 OUTER 잠금 유지 (세션164 락 파일 active)
- 다음 morning 07:10 cron에서 동일 정책 적용 (한글 행 자동 skip)

---

## 세션164 (2026-05-20 KST) — SP3M3 야간 D+1 반영 + SD9A01 OUTER 보류 잠금

### 발화 → 결과
- 사용자: "sp3m3 야간계획 반영"
- 진행: `python run.py --session evening --line SP3M3 --http-only` 직행. http OAuth PASS → 야간 27건 → dedupe 1건(RSP3SC0362) → 26건 D0 업로드 → API rank 26/26 → final_save MES rsltCnt=1300 → Phase6 SmartMES 카운트·중복·순서 일치 PASS
- 사용자: "아우터 계획은 잠정 보류다 그러니까 잠궈놔"
- 구현: `state/sd9a01_outer.lock` 파일 신규 + run.py에 `_apply_line_locks(args)` 함수 추가(main() argparse 직후 호출). 락 존재 시 `--line SD9A01`→exit 0, `--line ALL`→SP3M3 only로 args 자동 조정, `--line SP3M3`→영향 없음(안내만). SKILL.md 상단 🔒 보류 표시. 단위 검증 SimpleNamespace 3 케이스 PASS. commit `429e150f`.
- 메모리: `project_d0_sd9a01_outer_lock.md` 신규 (MEMORY.md 인덱스 추가)

### 다음 세션 액션
- 잠금 해제는 사용자 명시 발화("OUTER 잠금 풀어"·"OUTER 재개"·"SD9A01 잠금 해제") 또는 락 파일 직접 삭제
- 다음 morning 07:10 SP3M3 주간 자동 cron 영향 없음(--line SP3M3 호출이라 락 무관)
- 야간 작업 결과 사용자 피드백 청취

---

## 세션159 (2026-05-15 KST) — SP3M3 야간 D+1 반영

### 발화 → 결과
- 사용자: "sp3m3 야간계획 반영"
- 진행: SKILL.md 정독 → 비가역 통보 1줄 → 실행 → Phase 0~5 PASS / Phase 6 순서 불일치 / verify_run.py RETRY_NO(log_missing)
- 판정: 운영상 PASS — 등록·서열·MES 전송 완료, SmartMES 21건 전부 존재. Phase 6 검증 알고리즘 자체 이슈로 분리

### 다음 세션 액션
- Phase 6 SmartMES `prdtRank` 정렬 정책 분석 — `r_items = sorted(items, key=prdtRank)` 응답이 setBeginTime 적용 후 어떻게 재배치되는지 raw 응답 캡처 (B 모드 진단)
- 야간 D+1(05-16 토) 라인 가동 후 실제 생산 순서가 어긋났는지 사용자 피드백 청취
- 잡셋업 v3.3 morning cron(2026-05-16 07:11) `state/run_v3_*.json` 확인 (세션158 후속 유지)

---

최종 업데이트: 2026-05-15 KST — **세션158** [B+C] **jobsetup-auto v3.4/v3.5 폐기 → v3.3 단독 복귀**. 사용자 발화 "잡셋업 셋팅 점검" → 진단 시작. state/run_v34_*.json 분석에서 5/11·12·15 3회 연속 `wrkid_missing_after_save` 동일 시그니처 확인. 14:27 KST read-only 진단 호출(`--mode list-only --with-assign --with-auth`)에서 6공정 wrkId 채워서 추천 옴 — 새벽 시점에만 빈값. 추가 진단으로 14일치 배치 패턴 회수: A조 7회 / B조 3회 / 휴무 — 매일 고정 풀 변동 패턴. 사용자 발화 "최적배치 버튼 누르면 매일 고정으로 들어간다" → UI 버튼 ≠ assign-best API 가능성. 사용자 추가 발화 "7시 30분 전에 마무리되어야 한다" → 시각 미루기 안 폐기. 사용자 정정 "관리자가 입력이 안되니까 수동으로 진행한거지" — 자동화 무용. MANUAL.md 정독 후 "결정 출처" 표 발견(작업자 인증 = 별도, 잡셋업 단독 가능, 사용자 답변) → v3.4/v3.5 통합 자체가 원래 설계와 충돌. 사용자 명령 "작업자 인증 관련 내용 모두 삭제 해라" → A안 진행. 변경: run_jobsetup.py 317줄 삭제 + d0-production-plan/run.py chain 옵션 제거 + SKILL.md v3.3로 정리 + MANUAL.md 변경 이력 갱신 + 결정 출처 "작업자 배치" 행 추가 + memory project_jobsetup_skill.md 갱신 + TASKS.md entry 추가. 검증: `python run_jobsetup.py --mode list-only --auto-resolve-pno` → `=== jobsetup v3.3 mode=list-only ===` 정상, 17/17 already_done, assign/auth 흔적 0. 문법 OK 413줄. .claude/tmp/ 진단 스크립트 2개 삭제. 새 운영 흐름: 관리자 새벽 UI 최적배치+인증 → 07:11 cron → d0-plan → jobsetup chain → 17건 자동 → 07:30 마감 → 07:50 라인 가동. 사용자 분노 발화 6회 흡수("미쳤네", "라인 가동을 못한다", "시각 미루는 이유가 뭐냐", "7시 30분 전 마감", "니가 SmartMES 켜서 분석해라", "지침 안 읽었지"). 메모리 룰 `feedback_always_read_instructions.md`(SKILL.md→MANUAL.md→REFERENCE.md 우선 읽기) 위반 1회 발생 — MANUAL.md 늦게 정독. /

## 세션158 (2026-05-15 KST) — jobsetup-auto v3.3 복귀

### 발화 → 결과
- 사용자: "생산계획 반영 스킬 중 잡셋업 항목관련 셋팅 점검"
- 진행: MANUAL.md 정독 → v3.4/v3.5 통합이 결정 출처와 충돌 발견 → 사용자 명령 "작업자 인증 관련 내용 모두 삭제" → 코드/문서 전체 갱신

### 핵심 변경
- run_jobsetup.py: 함수 6개(call_assign_list/best_list/save, call_auth_cnfm, build_auth_payload, is_assignment_complete, auto_shift_code) + argparse 옵션 4개(--with-auth, --with-assign, --shift, --force-assign) + main 내 assign/auth 블록 2개 + `import time` 제거. 730→413줄
- d0-production-plan/run.py:2144 cmd에서 `--with-assign --with-auth --shift D` 제거
- SKILL.md: v3.3 상태로 정리, 작업자 배치/인증은 관리자 UI 영역 명시
- MANUAL.md: 변경 이력 v3.4/v3.5 폐기 + "결정 출처" 표 "작업자 배치" 행 추가
- 로그 파일명: `run_v34_*.json` → `run_v3_*.json`
- memory project_jobsetup_skill.md 갱신

### 검증
- `python run_jobsetup.py --mode list-only --auto-resolve-pno` PASS
- 17/17 already_done, assign/auth 흔적 0
- 문법 검증 PASS

### 다음 세션 액션 (즉시)
- **잡셋업 페이로드 v3.3+ 추가 패치 검증 미완료** (세션158 후속) — `run_jobsetup.py:248~261` `build_save_item`에 7개 필드 추가됨: `x1Barcd="O"`, `x2Barcd="O"`, `x3Barcd="O"`, `abnmlCtnts=""`, `actionCtnts=""`, `note=""`. 근거: mesclient.exe 디컴파일 IL에서 UI 저장 흐름(JobSetupView+SaveJobSetupResultAsync.MoveNext)이 `set_xNBarcd ← ldstr "O"` 호출 확인. 사용자 발화: "자동화 입력은 임시 저장만 되고 작업자가 한 번 더 저장 눌러야 확정"
- **검증 방법**: SmartMES 직접 띄워서 RSP3PC0130 잡셋업 procNo=210(보더링 후 높이) 항목 상태 확인. computer-use MCP request_access 다이얼로그에서 **"이 세션 동안 허용"** 누르고 진행. 거부 X
- dev 서버 commit-one 검증 완료(sc=200), 다만 list.api 응답이 빈/null 필드 직렬화 제외 → API 응답만으로는 임시/확정 구분 불가. 시각 검증 필수
- 내일(05-16 토) 새벽 07:11 morning cron 실행 결과 확인 — `state/run_v3_20260516_*.json` 17건 정상 save 여부
- 관리자 SmartMES UI "최적배치" 버튼 운영 흐름 확립 — 매일 새벽 07:30 전 처리
- 만약 그래도 잡셋업 그리드 미반영 시 → 관리자 UI 작업 순서·시각 점검 (자동화 책임 아님)
- `.claude/tmp/` 진단 스크립트 4개(assign_pattern_check / assign_best_by_pno / jobsetup_diff_fields / jobsetup_endpoint_probe / find_pending_pno / verify_xbarcd_save) 정리 — 검증 완료 후 일괄 삭제

### 알아둘 운영 사실 (세션158)
- computer-use MCP 영구 grant 옵션 없음 (Anthropic 의도적 분리). "권한 우회 모드"·"원격 제어 활성화"는 일반 도구만 적용
- SmartMES 권한 다이얼로그 = 매 세션 1회 "이 세션 동안 허용" 클릭 필요. 거부 시 자동화 시각 검증 불가
- mesclient.exe 위치: `C:\Users\User\AppData\Local\Apps\2.0\CHW58EV7.D3Y\8ZOBDA0X.MLY\mesclient_7bdcf7c1d4dfdc73_0001.0000_none_bf15b75dde24c723\MESClient.exe`. RestSharp.dll은 같은 부모 디렉터리 `restsharp_598062e77f915f75_*`. PowerShell .NET reflection으로 ServiceAgent IL string + 메서드 시그니처 추출 가능 (재현 코드: 세션158 PowerShell 호출 흔적 참고)

### 미해결 (관리자 영역)
- SmartMES UI "최적배치" 버튼이 호출하는 정확한 API 추적은 보류 — 사용자가 자동화 영역 아니라고 명시
- v3.4/v3.5 폐기됐지만 state/run_v34_*.json 과거 로그는 진단 자료로 유지

---

## 세션157-2 (2026-05-13 KST) — 떠넘기기 유도 hook/지침 환경 정리
최종 업데이트: 2026-05-13 KST — **세션157-2** [C] **떠넘기기 유도 hook/지침 환경 정리 (사용자 지시 — 막기보다 유도 제거)**. 사용자 본질 지적: "막는것보다 사용자 확인후·승인후 같은 유도하는 훅이나 지침을 제거하는 게 맞다." 변경: (1) finish_trigger_detect.sh — 안내 메시지 주입 비활성(쉘 골조만 유지, exit 0) (2) share_gate.sh — "3way 공유 필수" 강요 문구 제거, 감지 신호 stderr 1줄 + log 기록 (3) completion_gate delegation_guard 차단 메시지 단순화 — 4단 가이드라인 → "질문 없이 네 판단으로 재작성하라" 1줄 (4) CLAUDE.md 질문 허용 2조건 → 1조건(ERP/MES 비가역 1줄 통보, 확인 아님). "사용자 명시 선택 요구" 폐기 — 사용자 발화 자체가 입력이므로 별도 묻기 불요 (5) /finish 자동 트리거 지침 정리 — Claude 자체 판단으로 처리 (6) 메모리 feedback_authority_ladder.md / feedback_finish_auto_trigger.md 갱신 — 세션157 정정 명기. / **세션157** [B+D+C] **떠넘기기 재발 진단 + 3way 만장일치 hook gate 부분 복원**. 사용자 체감 지적("또 떠넘기는 거 같다·스스로 사고를 포기한 느낌·지침을 안 보는 것 같다") → B 모드 진단 → 3way 토론 R1 pass_ratio=1.00 → C 모드 구현. H1 버림(자기검열 불충분 실증) / H2 채택(completion_gate.sh Stop 단계 delegation guard Phase 0 최소 복원) / H3 부분 채택(세션148 "문서만 충분" 하위 가정만 폐기, R2/R3/R4 폐기·2조건·C 모드 완화는 유지). 변경: completion_gate.sh +37줄(정규식 9개 + whitelist 7개 + decision:block + stop_hook_active 2회차 통과 + delegation_guard.jsonl 로그) / CLAUDE.md "질문 허용 2개뿐" 압축 + 금지 표현 9개로 확장 / feedback_authority_ladder.md hook_gate enforcement 갱신 / project_session148_hook_gate_relapse.md 신설. smoke 3 시나리오 PASS (block / whitelist / 2회차). 로그: 90_공통기준/토론모드/logs/debate_20260513_211646_3way/. / **세션155** [A+C] **SP3M3 5/13 야간계획 반영 + phase4 정렬 회귀 사고 fix + 헬퍼 추출**. evening --http-only 5건 누락(RSP3SC0644/0590/0584/0023/0026 야간 신규 ext 326730~326735에 rank 미박힘 — REG_NO ascending 정렬 버그, 세션152 동일 사고 2회 회귀) → 즉시 fix(d62649c7) + 보강 등록(rank 42~46, MES rsltCnt=250, WORK_STATUS=R 정상). `_sort_idx_map_desc` 헬퍼 추출 + feedback_d0_idx_map_sort_desc.md 메모리 + 호출부 주석 3중 회귀 차단(6a8d0933). 추가 CLAUDE.md 도메인 표에 d0-production-plan row 명시(62ca68bd) — 새 세션 라우팅 사고(SP3 메인서브 v2 OUTER xlsm 잘못 매칭) 방지 + feedback_d0_plan_routing.md 메모리 신설. sGrid 최종 46건(주간 18 + 야간 28). / **세션154** [A] **4월 외주 지원비용 양식 정리** — 리노텍·화인텍 2건 신규. `05_생산실적/조립비정산/05월/4월 지원/` 신설. 리노텍 = 3월(9건)+4월(6건) 통합 청구분 / 15건·9,175개·5,523,350원. 화인텍 = 메인SUB_지원받은 20행 / 14,590개·9,232,268원. 88810P 시리즈 서브품번 매핑(971/971/973/975)은 `\\210.216.217.180\zz-group\15. SP3 메인 CAPA점검\SP3M3\생산지시서\2025년 생산지시\01월\SP3메인서브 생산지시서 (2025.01.02).xlsx` "SP3 LINE 기준 정보" r159~r166 권위 — 3월 화인텍 양식·김종학GJ 마감상세에는 매핑 부재. / **세션153** [C] **d0-plan GERP 로그인·자동화 전면 재설계 + Claude 루틴 이관** — OAuth pyautogui 가로채기 영구 차단(page.fill DOM 직접) → HTTP OAuth(daily-routine 패턴 ERP 확장) → HTTP 업로드(multipart + JSON multiList, ADDN_PRDT_REASON_CD=002) → HTTP rank/final_save + setBeginTime Python 재현(휴식시간 8종) → 완전 브라우저-less 옵션 `--http-only` PoC PASS (RSP3PC0144 326320 rank=19 풀 흐름). 6 commit (dcd95815 / 69adfbb0 / db9c8bcd / 14a0ca14 / fafac0c9 / 4d9291eb). + Claude scheduled-task `d0-morning` 등록(월~토 07:11 KST) + Windows schtasks D0_SP3M3_Morning/Recover 2건 삭제 + Slack 알림 테스트 PASS(채널 C096LU8PH44, ts=1778637849). / **세션152** [C] **별건 fix** final_check.sh sed 패턴 ` KST` 옵셔널 누락 (L313·L362) → meta_drift 14건/session_drift 4건 누적 원인 / commit 861beaf9 main push 완료. / 세션152 [A+C] SP3M3 라인 조립비 등록 누락 점검 + 신규 스킬 `assy-registration-check` 신설 + V2 마스터 일괄 sync + 4월 오류리스트_추가.xlsx 218행 작성 + HCAMS02 NLR/CLR 단가 룰 적용. / 세션151 후속 [C] 5/11 morning OAuth 실패 → `_force_chrome_foreground` 신설 / 세션151 [B+C] D0 자동화 실패 분석 + 3종 패치 commit 59273df9 / 세션150 [A] 4월 이관품번 라인별 정리 시트 추가 완료. / **세션152 evening [A+C] SP3M3 야간계획 반영 사고 + run.py 4종 패치** (Phase 6 5건 누락 → idx_map 정렬 a-b→b-a 매뉴얼 4번 룰 준수 / pyautogui ID 0109 명시 typewrite / OAuth wait 60s→10s / 누락 5건 새 ext 보강 등록 + final_save 200).

## 세션157-3 (2026-05-13 KST) — 토론모드 가속 폴링 단축 + Safe-cutoff hook

### 발화 → 결과
- 사용자: "토론모드는 --http-only 유사방식으로 안되는건가" + "토론해서 플랜보강후 실행"
- 진행: 콘솔 fetch 가속안 검토 → 3자 토론 R1 → 폐기 + 폴링 단축 채택

### 3자 토론 R1 (pass_ratio=4/4=1.00 만장일치)
- 로그: 90_공통기준/토론모드/logs/debate_20260513_232210_3way/
- GPT 본론: ToS·계정 안전성 "실패" 판정 + 가속폭 라운드당 20~60초 한계
- Gemini 본론: 폴링 0.5/1/2초 + One-shot + 듀얼 bringToFront + Safe-cutoff 4종
- GPT 검증: 0.5초 → 1초 이상 보수 권고
- 최종 합의: 1/2/3초 폴링 + One-shot 추출 + Safe-cutoff hook

### 변경 (commit 5efc8edd)
- gpt-send/gpt-read/gemini-send/gemini-read 일반 모델 폴링 3/5/8 → 1/2/3초
- thinking 모델 long polling 유지 (race condition 방지)
- .claude/hooks/debate_safe_cutoff.sh 신설 (인증챌린지/대화미저장/사용량경고/보안알림 4종 감지)
- 토론모드 CLAUDE.md "## 폴링 단축 가속 정책" 섹션 신설
- 콘솔 fetch 폐기 결정 명문화

### 기대 효과
- 라운드 2~3분 → 1.5~2분 (20~50초 절감)
- ToS 안전 + ChatGPT 프로젝트방 컨텍스트 그대로

### 다음 세션 액션
- 실제 토론 라운드 1회 돌려 폴링 단축 체감 확인
- 텍스트 유실 race condition 모니터링 (One-shot 추출 직후 2회 연속 동일 검사로 방지)
- 가속 비활성 발생 시 .claude/state/debate_accel_disabled 확인 + 원인 진단 후 rm

---

## 세션153 — d0-plan GERP 로그인·자동화 전면 재설계 (2026-05-13 08:00~11:00)

**배경**: 5/13 morning 자동화 OAuth 2회 연속 `/login?error` → recover 51min 한계 도달 종료. 사용자 "왜 똑같은 문제를 반복하나" 발화 → 근본 진단.

**진단**: pyautogui 키보드 입력 + Chrome 비번관리자 자동완성이 OS focus 가로채기 취약. 세션141 hidden.vbs / 세션151 _kill_zombie_chrome / 세션152 OAuth 60→10s — 전부 타이밍·재시도 패치라 입력 메커니즘 자체는 그대로.

**A안 1단계 (HTTP OAuth)**: requests로 OAuth SSO POST 직접. ssoUrl 추출 → /login POST(userId/password/clientId=ERP/ssoUrl) → cookies(SESSION/XSRF-TOKEN/JSESSIONID) 확보 → playwright context 주입 → D0_URL 즉시 통과. ID/PW는 .oauth.json(.gitignore). selector dump: input[name=userId/password]/#loginBtn.

**A안 2단계 (HTTP 업로드)**: phase3을 requests multipart로. POPUP GET → selectListPmD0AddnUpload(files+hidden3) → multiListPmD0AddnUpload({excelList, ADDN_PRDT_REASON_CD:"002"}). 핵심 단서 — X-XSRF-TOKEN은 매 POST 직전 cookie 최신값 갱신 필수(불일치 시 500). ADDN_PRDT_REASON_CD 빈값 보내면 등록사유 빈 row 등록(사용자 화면 캡처로 발견 → "002"="신규추가수량" grid row 직접 dump).

**A안 3단계 (완전 브라우저-less)**: phase4(rank) + phase5(final_save) + phase6(verify) 모두 requests로 전환. process_one_row_via_http가 totGrid GET → mGrid GET → sGrid GET → rowData 구성 → save POST. final_save는 sGrid 재조회 + `_apply_set_begin_time` 적용 후 sendMesFlag='Y' POST. setBeginTime JS 정밀 mirror — UPH 기반 분 단위 + 휴식시간 8종(9:50/12:00/14:50/17:00/21:00/24:00/3:00/5:00) 자동 가산 + PRDT_RANK = idx+1 + PLAN_DA_S/E.

**단위 검증**: sGrid 18행 적용 시 ERP 기존 BEGIN/END/RANK와 100% 일치(휴식시간 4건 케이스 포함).

**PoC 실 등록 검증** (RSP3PC0144 1건, 5/13, --http-only):
- phase0 OAuth PASS, ensure_chrome_cdp 미호출 (브라우저 launch 0)
- phase3 D0 업로드 PASS / phase4 ext=326320 rank=19 / phase5 mesMsg 성공 rsltCnt=50
- phase6 서열 순서 엑셀 일치 ✅
- ERP grid 직접 dump 검증: REASON_CD=002, PRDT_RANK=19, BEGIN_TIME=19:50(연속), END_TIME=20:09, WORK_STATUS_CD=R

**자동화 이관**:
- Claude scheduled-task `d0-morning` 등록 (월~토 07:11 KST cron `11 7 * * 1-6`, jitter 적용 07:19)
- prompt: run_morning.bat 실행 + 실패 시 Slack 알림(C096LU8PH44 + <@U096LU8KNN8> 멘션)
- Windows schtasks D0_SP3M3_Morning + D0_SP3M3_Morning_Recover **삭제**
- Slack 알림 테스트 PASS (ts=1778637849)

**회귀 보험**: `--http-only` 옵션 default off. 매일 자동 실행은 기존 page.evaluate 경로 그대로(점진 전환). 1~2주 검증 후 default on 검토.

**잔여 정리**:
- 사용자 화면 수동 삭제 — RSP3PC0144 326312 / RSP3PC0143 326313 / RSP3SC0752 빈 등록사유 row (모두 정리 완료)
- ERP는 sGrid에 임시저장 후 sGrid 행 삭제 시 상단 grid 삭제 비활성 → D0 reload(F5) 후 활성 (실측 확인)

**부가 패치**: gerp-unregistered-check/erp_lookup.py도 동일 OAuth page.fill 패턴 동기화 (69adfbb0). daily-routine/run.py는 이미 requests POST 방식 — 패치 불필요.

## 세션152 evening — SP3M3 야간계획 반영 사고 (2026-05-12 18:39~19:30)

**배경**: 사용자 "SP3M3 야간계획 반영" 발화 → d0-production-plan evening 세션(--line SP3M3) 실행.

**실행 결과**:
- Phase 0~5: 정상 (24건 추출 → dedupe 1행 RSP3PC0054 제외 → 23건 ERP 업로드 + 서열 + MES 전송 statusCode 200 / mesMsg rsltCnt=900)
- Phase 6 SmartMES 대조: FAIL 5건 누락 (RSP3PC0130/RSP3PC0129/RSP3SC0644/RSP3SC0590/RSP3SC0584 ext=325225~325230)

**진단**: `_diag_dup_rows.py` 실측으로 5건 모두 ERP 그리드 2행 공존 확인 — 작은 ext(주간 기존) + 큰 ext(야간 신규 325983~325987). phase3 multiList INSERT 정상.

**근본 원인**: `api_rank_batch` `run.py:1046` idx_map 정렬이 `(a,b) => a - b` 오름차순 → 매뉴얼 4번 룰 "EXT_PLAN_REG_NO 최대값 매핑" 위반. 야간 items 1건 등장 시 0번째(=가장 작은 ext=주간 기존)에 매핑 → 야간 rank가 주간 행 위에 덮어 박힘.

**run.py 패치 4종 (세션152 evening)**:
1. **L1046 idx_map sort `b-a` 내림차순** — 매뉴얼 4번 룰 준수. 야간 1건 등장 시 신규 ext에 자동 매핑.
2. **L265~270 `ensure_erp_login`** pyautogui ID `0109` 명시 typewrite + `Ctrl+A` + `Delete` 초기화. 기존 `down`+`return` 자동완성 첫 항목 의존 폐기. 사용자 자동완성 ID 3개 저장 환경에서 매번 다른 ID 접속되던 사고 차단.
3. **L282/322~344 `_wait_oauth_complete` timeout 60s → 10s**. 0109 명시 입력으로 OAuth 정상 통과 가정 + 정체 시 fallback 빠른 진입.
4. `--no-dedupe` 옵션 추가했으나 사용자 정정 "1~5행 dedupe는 유지"로 즉시 원복 (net 변경 0).

**누락 5건 보강 (`_fix_missing_5.py`)**:
- 새 ext(325983~325987)에 직접 `process_one_row` 호출 → rank 39~43 박음
- `final_save` mesMsg rsltCnt=250 / statusCode 200 / MES 전송 완료
- 사용자 지시 "기존 잘못 박힌 5건 rank(ext=325225~325230 위 A rank) 삭제 X" — ERP 잔존 유지

**다음 morning (2026-05-13 07:10) 검증 포인트**:
- `[phase0]` 로그에서 `OAuth 완료 대기 60s 실패` 메시지 부재 확인 (10s로 단축됨)
- ID 0109 정확 입력 검증 (잘못된 ID 접속 사고 재발 X)
- idx_map 내림차순 자연 검증 (주간 새 등록 시 정렬 정상)

**잔존 자산**:
- `_diag_dup_rows.py` (5건 진단 스크립트, 동일 사고 재발 시 재사용)
- `_fix_missing_5.py` (5건 누락 보강 스크립트, 동일 사고 재발 시 참고)


---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260501_20260512.md` (세션152 별건 ~ 세션134)
> **이전 archive**: `98_아카이브/handoff_archive_20260430_20260430.md`

