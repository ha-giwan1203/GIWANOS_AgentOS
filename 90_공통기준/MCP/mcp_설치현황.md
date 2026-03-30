# MCP 설치 현황

최종 업데이트: 2026-03-30

---

## 설치된 MCP 목록

| MCP | 패키지 | 용도 | API 키 | 설치일 |
|-----|--------|------|--------|--------|
| telegram | plugin (Claude 공식) | Telegram 봇 연동, 알림 수신 | BOT_TOKEN (.claude/settings.json) | 2026-03-28 |
| context7 | `@upstash/context7-mcp` | 라이브러리 최신 공식 문서 실시간 참조 | 불필요 | 2026-03-30 |
| sequential-thinking | `@modelcontextprotocol/server-sequential-thinking` | 복잡한 문제 단계별 사고 강제 | 불필요 | 2026-03-30 |
| Gmail | plugin (Claude 공식) | Gmail 읽기/초안 작성 | OAuth | - |
| Google Calendar | plugin (Claude 공식) | 일정 관리 | OAuth | - |
| Notion | plugin (Claude 공식) | 현황판 업데이트 | OAuth | - |
| Slack | plugin (Claude 공식) | 완료 보고, 알림 | OAuth | - |
| Google Drive | plugin (Claude 공식) | 파일 검색·참조 보조 | OAuth | - |
| Claude in Chrome | plugin (Claude 공식) | 브라우저 탭 읽기·조작 | 불필요 | - |

---

## 설정 파일 위치

| 파일 | 경로 | 내용 |
|------|------|------|
| 로컬 MCP 설정 | `~/.claude.json` (프로젝트별) | context7, sequential-thinking 등록 |
| 전역 설정 | `~/.claude/settings.json` | Telegram BOT_TOKEN, 플러그인 활성화 |

---

## 실무 활용 프롬프트

### Context7 (최신 문서 참조)
```
use context7, openpyxl 최신 문법으로 수식 보존하며 셀 값 읽는 코드 짜줘
use context7, pandas 최신 버전 기준으로 groupby + agg 예시 작성해줘
```

### Sequential Thinking (단계별 분석)
```
sequential thinking으로 이 정산 차이 원인 단계별로 추적해줘
sequential thinking 사용해서 라인배치 오류 원인 단계별로 분석해줘
```

### 두 MCP 조합
```
파이어크롤로 데이터 수집 후, sequential thinking으로 단계별 분석해서 보고서 만들어줘
```

---

## 미설치 (검토 대상)

| MCP | 용도 | 비고 |
|-----|------|------|
| Playwright | 브라우저 직접 제어 (클릭·로그인) | Claude in Chrome으로 유사 기능 보유 |
| Firecrawl | 웹 대량 크롤링 → CSV/Excel | API 키 필요, 무료 2,000회 |
