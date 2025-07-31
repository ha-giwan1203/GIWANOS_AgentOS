# GIWANOS 세 방 환경 통합 체크리스트

다음 항목을 세 방(C:/giwanos) 환경에서 실행 전 반드시 검증하세요.

1. **환경 변수 (.env)**
   - [ ] `C:/giwanos/config/.env`에 `OPENAI_API_KEY`가 정확히 설정되어 있는가

2. **판단 규칙**
   - [ ] `C:/giwanos/config/judgment_rules.json` 파일이 존재하며 올바른 JSON 형식인가

3. **마스터 루프 실행**
   - [ ] `C:/giwanos/run_giwanos_master_loop.py` 파일이 최신 버전으로 덮어써졌는가
   - [ ] `Cloud` 호출 없이 `python run_giwanos_master_loop.py` 실행 시 정상 완료되는가

4. **로그 파일**
   - [ ] `C:/giwanos/logs/master_loop.log`에 실행 기록이 남았는가
   - [ ] `C:/giwanos/logs/streamlit.log`에 대시보드 접근 기록이 남았는가

5. **보고서 생성 및 전송**
   - [ ] `C:/giwanos/data/reports/weekly_report_YYYYMMDD.pdf`가 생성되었는가
   - [ ] 이메일 전송이 정상적으로 수행되었는가

6. **GitHub 통합**
   - [ ] `C:/giwanos/github_release_bundle/`에 릴리즈 파일이 준비되었는가
   - [ ] `git_sync.py`로 자동 커밋·푸시가 정상 동작하는가

7. **Notion 연동**
   - [ ] `C:/giwanos/notion_integration/` 폴더에 업로드 스크립트가 있는가
   - [ ] 회고 파일(`reflection_YYYYMMDD.md`)이 Notion에 올라가는가

8. **대시보드**
   - [ ] `C:/giwanos/interface/status_dashboard.py`가 최신 버전인가
   - [ ] `streamlit run status_dashboard.py` 실행 시 오류 없이 화면이 표시되는가

