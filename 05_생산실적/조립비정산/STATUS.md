# 조립비 정산 진행 현황 (2026-04-06 step5 버그수정 최신화 / 2026-04-23 세션98 전역 점검 — 도메인 내용 변경 없음)

## 현재 상태
- 운영 파일: 정산결과_03월.xlsx (04월 폴더, 기준정보 재생성 후 재실행)
- 파이프라인: run_settlement_pipeline.py (Step 1~8 전체 자동화)
- 입력 데이터: 04월/실적데이터/G-ERP 3월실적.xlsx, 구ERP 3월 실적.xlsx (2026-04-04 입수)
- 기준정보: 관리DB(02월)에서 재생성 + GERP 3월 신규품번 추가 (2026-04-06)
- 스킬: `/settlement MM` 원스텝 실행 가능 (setup_month → step1~8 → 검증)
- 오류리스트: 04월/오류리스트_03월.xlsx (391건, 이관품번 78건 제외 = 313건 실질)

## 파이프라인 수정 이력
1. 구ERP 합산 버그 수정 — step7에서 구ERP 주간+야간 합산 누락 → 총수량 컬럼 추가
2. SD9A01 야간 30% 수정 — "추가" 행에 기준단가 100% 적용하던 것을 30%로 수정
3. 단가비교 컬럼 추가 — step7에서 전 라인 시트에 GERP단가/단가차이/단가비고 자동 생성
4. PYTHONUTF8=1 인코딩 문제 해결
5. **(2026-03-27)** step4 동일품번-동일단가 중복 제거
6. **(2026-03-27)** step2 GERP 원본금액 피벗 추가 — day_amt_pivot/night_amt_pivot
7. **(2026-03-27)** step5 GERP 원본금액 필드 추가 — gerp_orig_day_amt/gerp_orig_ngt_amt
8. **(2026-03-27)** step7 야간 표시 개선 — 주간수량=정상-추가, 야간금액=기본+가산
9. **(2026-03-27)** step7 상세시트 가독성 — 0→하이픈, 실적없는행 숨김, 그룹헤더 병합
10. **(2026-03-27)** SD9A01/SP3M3 구ERP 주야간 분리 표시 복원
11. **(2026-03-27)** SP3M3 야간 RSP 모듈품번 역변환
12. **(2026-03-27)** 결과 3컬럼화 — 수량차/금액차/유형 (GERP누락/기준누락/다중단가/단가차이/수량차이/정산차이)
13. **(2026-03-27)** 조립품번 파이프라인 추가 — step2 GERP조립품번 lookup, step4 기준정보 조립품번, step5 매핑(기준우선), step7 전라인 표시
14. **(2026-03-27)** GERP 단가 다중단가 지원 — (라인,품번)→단가set, 기준단가 매칭 표시
15. **(2026-03-27)** SP3M3 구ERP 전체업체 피벗 변경 — 모듈품번(MO) 매칭 불가 → all_day/all_night 사용
16. **(2026-03-27)** SP3M3 구ERP 야간 = GERP 야간 동일 적용 — 구ERP에 야간 데이터 없음, 비교는 주간만
17. **(2026-03-27)** 유형 분류 추가 — G실적누락/구실적누락 유형 추가
18. **(2026-03-27 2차)** 집계시트 구ERP 비교 섹션 확장 — 주야 분리 14컬럼 (GERP주간/야간/합계, 구ERP주간/야간/합계, 차이)
19. **(2026-03-27 2차)** 01_차이분석 시트 전면 개선 — 유형분류(G실적누락/구실적누락/기준누락/다중단가/단가+수량/단가차이/수량차이/정산차이) + 수량차/금액차 분리 + 라인별 소계 + 주야 qty/amt 분리

## 3월 정산 결과 — 04월 폴더 최신본 (2026-04-06, 기준정보 재생성 후 재실행)
| 라인 | GERP정산 | 구ERP정산 | GERP-구ERP차이 | 비고 |
|------|---------|---------|--------------|------|
| SD9A01 | 109,117,529 | 98,616,848 | +10,500,681 | |
| SP3M3 | 80,304,519 | 68,446,923 | +11,857,596 | 구ERP야간=GERP야간 적용 |
| WAMAS01 | 38,266,302 | 34,837,802 | +3,428,500 | |
| WABAS01 | 11,921,269 | 11,474,381 | +446,888 | |
| ANAAS04 | 3,976,580 | 2,594,070 | +1,382,510 | |
| DRAAS11 | 1,551,188 | 1,000,984 | +550,204 | |
| WASAS01 | 314,800 | 328,832 | -14,032 | |
| HCAMS02 | 13,148,898 | 10,872,512 | +2,276,386 | |
| HASMS02 | 1,709,640 | 1,709,460 | +180 | |
| ISAMS03 | 727,446 | 341,341 | +386,105 | |
| **합계** | **261,038,171** | **230,223,153** | **+30,815,018** | |

### 데이터 검증 (2026-04-06, 기준정보 재생성 후)
- Step6 검증: **PASS** (CRITICAL 0 / WARNING 0 / INFO 2)
- GERP 원본금액 정합성: PASS
- 오류리스트: 391건 (이관품번 78건 제외 = 313건 실질)
- 산출물: 정산결과_03월.xlsx (14시트) + 오류리스트_03월.xlsx (391건)
- 변경: 기준정보 관리DB 기반 재생성 (다중단가 269건 보존) + X9000/X9500 이관품번 삭제

## 기준정보 재생성 이력 (2026-04-06)
- 원인: 이전 기준정보가 (라인,품번) 2키 max단가로 다중단가 파괴 → 관리DB에서 완전 재생성
- 소스: 조립비_관리DB_02월_20260311.xlsx (유일 원본)
- 방법: 관리DB 10개 라인 → 기준정보 형식 변환 + GERP 3월 신규품번 추가 + X9000/X9500 삭제
- 결과: 16,524행, 다중단가 269건 완전 보존
- 검증: 10개 라인 다중단가 수 관리DB 대비 일치/초과 확인
- 파괴된 파일 백업: 기준정보_라인별정리_최종_V1_20260316_damaged_20260406.xlsx

## 차이 478,596원 원인 확정
| 라인 | 차이 | 원인 | 판정 |
|------|------|------|------|
| ANAAS04 | +444,312 | 28개 AR계열 품번: 기준단가 47원 vs GERP단가 23원 | 확인필요 |
| ANAAS04 | +19,215 | 10개 품번: 동일품번 다중단가(23/20원) → 기준단가 23원 적용 | 정상 (다중단가) |
| WAMAS01 | +15,069 | 3개 품번: 기준단가 32원 vs GERP단가 16원 | 확인필요 |

## 해결된 이슈
- ~~HCAMS02 수량 2배~~ → 기준정보 중복 행 제거로 해결 (+490,028 → 0)
- ~~WABAS01 단가=0 56건~~ → 실적 있는 건 3건(511ea), 금액 영향 없음
- ~~구ERP Sheet2 미반영~~ → 대원테크 행 없음, 영향 없음

## 발견된 핵심 규칙 (GERP SD9A01 야간)
- GERP "추가"(야간) 행의 단가는 기본단가의 30%로 이미 입력됨
- 정산 계산: "추가" 행 = 기준단가 × 0.3 × 수량

## SP3M3 야간 RSP 역변환 현황 (2026-03-27)
- 매핑 소스: 1차 모듈품번(221건) + 2차 라인배정(+83건) = 총 304건
- 변환 성공: 55건(24,565개)
- **미매칭 4건(6,462개)**: RSP3SC0291(837), RSP3SC0292(1,391), RSP3SC0293(934), RSP3SC0294(3,300)
- 미매칭 원인: 모듈품번 갱신으로 두 매핑 파일 모두 미등록
- 미매칭 처리: GERP 원본금액 그대로 야간금액 적용 (역추적 포기)
- SP3M3 정산 vs GERP원본: **-24원** (반올림 오차, 사실상 일치)
- 조치: SP3M3_모듈품번_최신.xlsx에 해당 RSP 추가 시 정상 매칭으로 자동 전환

## GERP vs 구ERP 차이 원인 요약 (2026-03-27)
| 라인 | 차이 | 주요 원인 |
|------|------|---------|
| SD9A01 | +23,919,219 | 야간 계산방식 구조차이 (GERP 100%+30% vs 구ERP 30%만) +21,005,169 + 주간수량 차이 +2,914,050 |
| SP3M3 | +7,665,704 | 구ERP 주간qty 더 많음 (20,044개) + 단가차이 품번 |
| WAMAS01 | +2,338,315 | 수량차이 +49,121개 + 단가차이 품번(32원 vs 16원) |
| ANAAS04 | +1,656,557 | 수량차이 +52,946개 + 단가차이 품번(47원 vs 23원) |
| HCAMS02 | +1,457,704 | 수량차이 +16,042개 |

## 문서 동기화 이력

| 일자 | 내용 | commit |
|------|------|--------|
| 2026-03-28 | 데이터사전 v1.0 동기화 완료 — 기준정보 파일명 수정, §5 Step5 items 필드 19개 추가, pipeline_contract.md GERP col11 + LineItem 4필드 추가, CLAUDE.md col 오기 수정 (col12→col11), step4 RSP dead code 사실 명시 | 484f81d7 |

## 하네스 Evaluator 1회차 검증 결과 (2026-03-30)

| 항목 | 결과 |
|------|------|
| 실행일 | 2026-03-30, 소요 54.9초 |
| Generator Step 6 판정 | FAIL (SP3M3 야간 RSP 미매칭 170원 불일치) |
| Evaluator 외부 판정 | **PASS 94점** |
| 판정 차이 이유 | RSP 미매칭 4건은 STATUS.md 등록 Known Exception — 비즈니스 규칙상 GERP 원본금액 사용이 맞음. Evaluator는 감점 처리 |
| 의의 | 하네스 Evaluator 도입 첫 실검증. Generator 내부 FAIL을 Evaluator가 Known Exception 반영해 PASS로 재판정 — 오판정 방지 효과 확인 |

> Step 6 FAIL 2레벨 분리 완료 (2026-03-30, commit aed19a12): CRITICAL/WARNING 분리, KNOWN_EXCEPTIONS 레지스트리, overall 3단계(FAIL/WARNING/PASS). GPT 로직 PASS 판정.
> 다음: step7_보고서.py에 WARNING 항목 별도 섹션 추가

## step5 매핑 버그 수정 (2026-04-06, fb81d7a5)

| 버그 | 수정 내용 | 효과 |
|------|----------|------|
| 미매핑 품번 구ERP 조회 누락 | unprocessed loop에 ep_t.get() 추가 | 구실적누락 152→74건 |
| 다중단가 2번째행 GERP누락 오분류 | is_first_gerp 플래그, non-first skip | GERP누락 143→72건 |
| SP3M3 야간 ERP측 미가산 | elif SP3M3 분기, e_ngt=g_ngt 적용 | SP3M3 +11.3M→+5.4M |
| 비SD9A01 야간 변수 미초기화 | else 분기 e_ngt=0 추가 | 변수 잔류 해소 |

- **수정 전**: 에러 388건, 차이 +25.6M
- **수정 후**: 에러 190건, 차이 +7.2M (SD9A01 -2,613원 거의 완벽)
- **사용자 확인**: 남은 +7.2M은 원천 데이터 불일치 (파이프라인 버그 아님)
- GPT 3라운드 공동작업 완료

## 남은 작업
- ANAAS04/WAMAS01 단가 차이 실무 확인 (기준정보 47원 vs GERP 23원)
- SP3M3 미매칭 RSP 4건 → 모듈품번 파일 갱신 후 재실행 (RSP3SC0291~0294)
- SD9A01/SP3M3 구ERP 주간수량 차이 원인 확인
- 정산DB 반영 (정산결과 → 조립비_관리DB 업데이트)
- 미매핑 품번 54건 검토
- ~~Step 6 FAIL 분리 설계~~ → **완료** (commit aed19a12, GPT PASS)
- ~~step7 WARNING 별도 섹션 추가~~ → **완료** (commit 34b04828, GPT PASS)

## 스킬화 완료 (2026-04-05)
- setup_month.py: 월 전환 자동화 (폴더 생성 + 파일 복사 + config 패치)
- step8_오류리스트.py: 오류리스트 자동 생성 (파이프라인 통합)
- `/settlement MM`: 슬래시 명령 원스텝 실행
- SKILL.md: assembly-cost-settlement 스킬 문서

## NotebookLM 도메인 지식 연결 (2026-04-17 세션56)

| 항목 | 값 |
|------|-----|
| 노트북 URL | https://notebooklm.google.com/notebook/dfb82a61-81b4-4e2d-8ed0-a70a5c7d0b9c |
| 노트북명 | 조립비정산_대원테크 |
| 소스 파일 | [notebooklm_source_조립비정산_v1.txt](06_스킬문서/notebooklm_source_조립비정산_v1.txt) — 9개 .md 병합본 (2,164줄) |
| 질의 에이전트 | `settlement-domain-expert` ([.claude/agents/settlement-domain-expert.md](../../.claude/agents/settlement-domain-expert.md)) |
| 권위 서열 | 저장소 원본 > NotebookLM 응답 (불일치 시 저장소 우선) |
| 파일럿 정확성 | 세션56 도메인 테스트 3건 PASS (야간계산식·SP3M3 주간수량·Known Exception 7건) |
| 역할 분리 | settlement-validator=실물검증(xlsx 대조) / settlement-domain-expert=도메인지식(NotebookLM 질의) |

### 재접속 절차
1. 세션 재시작 후 `mcp__notebooklm-mcp__get_health` → `authenticated=true` 확인
2. 만료 시 `setup_auth` 재실행 (최초 127초)
3. 사용: `Agent(subagent_type="settlement-domain-expert", prompt="{도메인 질문}")`

### Known Issue: MCP 좀비 Chrome (세션57 확인 · 2026-04-17)
**증상**: `ask_question` 호출 즉시 실패 — `browserType.launchPersistentContext: Target page, context or browser has been closed` / `exitCode=21`. `get_health`는 `authenticated=true` 반환하나 실제 질의 불가.

**원인**: 이전 세션의 `setup_auth` 종료 후 MCP Chrome 프로세스(메인 + crashpad-handler + gpu-process 3개)가 살아남아 `%LOCALAPPDATA%\notebooklm-mcp\Data\chrome_profile\lockfile` 점유. Playwright persistentContext가 프로필 획득 불가.

**식별 명령**:
```powershell
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like '*notebooklm-mcp*' } | Select-Object ProcessId, CommandLine"
```

**복구 절차**:
1. 식별된 PID 전부 `taskkill //F //PID {pid1} //PID {pid2} //PID {pid3}`
2. `cleanup_data(confirm=true, preserve_library=true)` — `library.json` 보존됨
3. `setup_auth(show_browser=true)` — 기존 쿠키 복구되면 사용자 로그인 없이 157초 내 자동 재인증 (Google SSO 토큰 재활용)
4. `ask_question` 재시도 → 성공 시 27~30초 응답

**후속 자동화 후보 (TASKS.md 안건)**: stop hook 또는 세션 시작 훅에서 notebooklm-mcp 프로필 사용 Chrome 좀비 탐지·정리 루틴 추가 검토.
