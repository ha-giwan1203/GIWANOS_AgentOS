# research: Claude Skills 생태계 벤치마킹 (B등급 2번)

작성일: 2026-03-31
목적: 커뮤니티 스킬 생태계 대비 우리 프로젝트 스킬 품질/범위 점검

---

## 1. 커뮤니티 생태계 현황 (2026.03 기준)

| 플랫폼 | 규모 |
|--------|------|
| SkillsMP (마켓플레이스) | 85,000+ 스킬 |
| awesome-claude-skills (GitHub) | 50+ 큐레이션 |
| Claude Marketplace | 150+ 스킬 |
| 한국어 커뮤니티 (GPTers, PyTorch 한국) | 활발 |

## 2. 우리 프로젝트 기존 스킬 vs 커뮤니티 비교

| 우리 스킬 | 커뮤니티 대응 | 차이점 |
|----------|-------------|-------|
| line-batch-management | 없음 (도메인 특화) | 우리만의 ERP 자동화, 커뮤니티에 없는 고유 스킬 |
| assembly-cost-settlement | 없음 (도메인 특화) | 조립비 정산 파이프라인, 완전 커스텀 |
| zdm-daily-inspection | 없음 (도메인 특화) | ZDM 시스템 연동, 완전 커스텀 |
| mes-production-upload | 없음 (도메인 특화) | MES 실적 업로드, 완전 커스텀 |
| xlsx/docx/pdf/pptx | 공식 스킬과 동일 | 이미 최신 버전 사용 중 |
| youtube-analysis | 커뮤니티에 유사 존재 | 우리 버전이 youtube_transcript.py 포함 |
| skill-creator | 공식 지원 없음 | 자체 하네스 포함, 고유 |

## 3. 커뮤니티에서 도입 검토할 만한 스킬

| 커뮤니티 스킬 | 용도 | 우리 적용 가능성 |
|-------------|------|----------------|
| obra/superpowers | brainstorm→write-plan→execute-plan 패턴 | 이미 Plan-First 워크플로우로 구현됨. 도입 불필요 |
| agent-browser | 웹 ERP 자동 입력 | 이미 line-batch-management가 ERP 브라우저 자동화 수행. 도입 불필요 |
| mcp-builder | MCP 서버 구축 가이드 | 향후 커스텀 MCP 필요 시 참고 가능. 현재 불필요 |
| Composio | 850+ SaaS 연동 | Gmail/Slack/Notion/Calendar는 이미 MCP로 연결. 추가 가치 낮음 |
| supermemory | 메모리 관리 | 이미 auto memory + MEMORY.md 체계 운영 중. 도입 불필요 |

## 4. 판정

**결론: 현재 스킬 체계는 커뮤니티 대비 충분하거나 오히려 도메인 특화로 앞서 있음.**

도입 필요 스킬: 없음 (현시점)
개선 여지:
1. 기존 스킬 메타데이터(description, trigger) 표준화 — 커뮤니티 SKILL.md 포맷 준수 확인
2. 스킬 버전 관리 체계 — 현재 v7, v9 등 수동 관리 → 체계화 여지
3. 스킬 성능 지표 — 실행 시간, 성공률, 토큰 사용량 추적 고려

## 5. 제안

이번 research 결론은 "도입 불필요, 내부 품질 개선에 집중".
별도 plan 없이 research로 종료 권장.

---

Sources:
- [awesome-claude-skills (travisvn)](https://github.com/travisvn/awesome-claude-skills)
- [Top 10 Claude Skills (Composio)](https://composio.dev/content/top-claude-skills)
- [Claude Skills 공식 문서](https://code.claude.com/docs/ko/skills)
- [SkillsMP 마켓플레이스](https://skillsmp.com/)
