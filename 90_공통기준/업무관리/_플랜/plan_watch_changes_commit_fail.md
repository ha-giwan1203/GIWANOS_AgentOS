# plan: watch_changes.py Git 커밋 실패 수정

작성일: 2026-03-31
GPT 승인: 확인됨 (공동작업방 응답 기준)

---

## 수정 대상

파일: `90_공통기준/업무관리/auto_commit_config.yaml`

| 항목 | 현재값 | 변경값 | 근거 |
|------|--------|--------|------|
| `branch` | `"업무리스트"` | `"main"` | 실제 브랜치가 처음부터 main이었음 (PR #8 이후 한 번도 성공 없음) |
| `push_on_commit` | `false` | `true` | 공동작업 기준이 Git main 실물 반영이므로 push 없으면 운영 원칙 충돌 |

---

## 적용 순서

- [x] Step 1: research_watch_changes_commit_fail.md 작성 완료
- [x] Step 2: GPT 방향 확정 (branch: main, push_on_commit: true)
- [x] Step 3: auto_commit_config.yaml 2줄 수정 (branch, push_on_commit)
- [x] Step 4: git add / commit / push — 커밋 f0a62cba (2026-03-31)
- [ ] Step 5: watch_changes.py 다음 debounce 사이클 대기 (30분 idle 후 자동)
- [ ] Step 6: 다음 Slack AutoBot 알림에서 [Git 커밋 실패] 없음 확인 (운영 검증)

---

## 제약

- 수정 대상: auto_commit_config.yaml 2줄만
- 나머지 설정(allowlist, blocklist, commit rules 등) 변경 금지
- watch_changes.py / commit_docs.py 코드 수정 없음

---

## 검증 기준

PASS: 다음 배치에서 Slack AutoBot에 [Git 커밋 실패] 알림 없음
FAIL: 여전히 실패 알림 발생 → 브랜치 확인, push 오류 로그 재분석
