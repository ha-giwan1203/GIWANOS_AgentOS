# /daily — 매일 반복 업무 통합 실행

> ZDM 일상점검 + MES 생산실적 업로드를 한 번에 처리한다.

## 사용법
```
/daily              # 미입력 날짜 자동 감지 → 전부 처리
/daily 04           # 4일만 처리
/daily 01-04        # 1일~4일 범위 처리
/daily --zdm-only   # 일상점검만
/daily --mes-only   # 생산실적만
```

## 인수
- `$ARGUMENTS` — 날짜(일) 또는 범위 (선택). 미지정 시 자동 감지. `--zdm-only` / `--mes-only` 단독 실행 옵션.

## 실행 순서

### Phase 0: 환경 준비
1. 현재 날짜/시간 확인 (`TZ=Asia/Seoul date`)
2. 대상 월 결정 (기본: 이번 달)
3. CDP 브라우저 상태 확인
   - `curl -s http://localhost:9222/json/version` → 응답 없으면 자동 시작
   ```
   start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" \
     --remote-debugging-port=9222 \
     "--user-data-dir=C:\Users\User\.flow-chrome-debug" \
     --no-first-run --no-default-browser-check
   ```
   - 3초 대기 후 재확인
4. **incident 사전 점검 (advisory)**
   ```bash
   python .claude/hooks/incident_repair.py --json --limit 5
   ```
   - **응답 시 필터링**: 출력 중 `ts` 필드가 당일(KST `date +%Y-%m-%d`) 시작인 항목만 인용 (Claude가 JSON 보고 자체 필터). incident_repair.py가 이미 unresolved만 반환.
   - 결과 인용 후 ZDM/MES 작업 진행. 차단 없음. (incident_quote.md 규칙 참조)

### Phase 1: 날짜 자동 감지
인수 미지정 시:

**ZDM 감지:**
- `/api/daily-inspection` → SP3M3 19개 점검표 → 첫 번째 점검표의 records 조회
- 이번 달 1일~어제까지 중 OK 기록이 없는 날짜 = 대상
- 당일은 제외

**MES 감지:**
- BI 파일에서 이번 달 날짜 목록 추출
- MES API로 날짜별 대원테크 데이터 조회
- BI에는 있고 MES에 없는 날짜 = 대상
- 당일은 제외

날짜 범위 지정 시:
- 해당 범위만 처리 (감지 생략)

### Phase 2: ZDM 일상점검 (--mes-only 아닐 때)
대상 날짜별 순차 실행:
1. ZDM 시스템 접속 확인 (`http://ax.samsong.com:34010/`)
2. 도메인 SKILL.md 참조: `90_공통기준/스킬/zdm-daily-inspection/SKILL.md`
3. SP3M3 19개 점검표 × 75항목 × 대상 날짜 수
4. 각 항목 POST → check_result="OK"
5. 기존 입력 건 자동 스킵
6. 검증: records 재조회 → 75건/일 확인

### Phase 3: MES 생산실적 업로드 (--zdm-only 아닐 때)
대상 날짜별 순차 실행:
1. BI 파일 갱신 (Z드라이브 → 로컬 복사)
2. 도메인 SKILL.md 참조: `90_공통기준/스킬/production-result-upload/SKILL.md`
3. MES 세션 확인 → auth-dev 리다이렉트 시 자동 로그인 (pyautogui)
4. iframe 동적 탐지 + 생산실적 페이지 로드
5. 날짜별: BI 추출 → 중복 확인 → SaveExcelData.do API 전송
6. 검증: MES 재조회 → 건수 + 생산량 합계 BI 대조

### Phase 4: 결과 보고
```
=== /daily 실행 결과 (YYYY-MM-DD) ===

■ ZDM 일상점검
  대상: 4/4(토)
  결과: 75/75건 OK — PASS

■ MES 생산실적
  대상: 4/4(토)
  BI 추출: 10건, 19,159ea
  MES 검증: 10건, 19,159ea — PASS

■ 미처리
  (없음)
```

### Phase 5: CDP 정리
- MES/ZDM 작업 완료 후 CDP 브라우저 종료 (선택)
- 종료 방식: `cdp.send("Browser.close")` (taskkill 금지)

## 전제 조건
- Python 3.12 + playwright + openpyxl + pyautogui
- Chrome 설치 (CDP 디버깅 포트 9222)
- Z드라이브 접근 (BI 파일 갱신용, 없으면 로컬 fallback)

## 참조 스킬
- ZDM: `90_공통기준/스킬/zdm-daily-inspection/SKILL.md`
- MES: `90_공통기준/스킬/production-result-upload/SKILL.md`

## 주의사항
- 당일 데이터는 기본 제외 (명시 지정 시만 포함)
- BI 생산량이 0인 날짜는 미가동으로 판단 → MES 업로드 스킵
- MES 로그인 실패 시 Phase 3 건너뛰고 Phase 4에서 미처리로 보고
- ZDM/MES 어느 한쪽 실패해도 나머지는 계속 진행
