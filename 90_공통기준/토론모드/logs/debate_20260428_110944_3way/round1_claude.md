# Round 1 — Claude 독자 답안 (양측 본론 수령 전 선행 작성, 2026-04-28 KST 20:09)

> 의제: `cut -c` 동일 패턴 다른 hook 사용처 검토 (세션119 잔존 별건)
> 작성 시점: GPT/Gemini 본론 수령 전

---

## 실물 점검 결과 (grep 4건)

| # | 파일·라인 | 패턴 | 입력 출처 | 멀티바이트 위험 |
|---|----------|------|----------|----------------|
| 1 | `commit_gate.sh:24,26,28` | `\| sha1sum/md5sum/cksum \| cut -c1-16` | hex digest 16자 fingerprint 추출 | **0 (ASCII hex 한정)** |
| 2 | `evidence_gate.sh:72,74,76` | 동일 fingerprint 추출 | hex digest | **0 (ASCII hex 한정)** |
| 3 | `smoke_test.sh:51` | `\| sha1sum \| cut -c1-16` | hex digest | **0 (ASCII hex 한정)** |
| 4 | `generate_agents_guide.sh:101` | `\| cut -c1-60` | SKILL.md `description:` 필드 (한국어 가능) | **위험 ↑ (실측 깨짐 확인)** |

## 실측 깨짐 증거 (의제 4번)

```
auto-fix              bytes:60 깨짐 발생 — 끝 byte가 한글 3바이트 경계에 걸려 � 출력
chomul-module-partno  bytes:60 깨짐 발생
d0-production-plan    bytes:60 깨짐 발생
```

영향 위치: `90_공통기준/업무관리/AGENTS_GUIDE.md` skill 목록 표 "설명" 컬럼.

## 결론 1줄

**의제 1건만 수정** — `generate_agents_guide.sh:101` `cut -c1-60` → mode_c_log.sh v2와 동일 Python codepoint slice 패턴 (`${PY_CMD:-python}` fallback + `.strip()` + UTF-8 binary mode). 나머지 3건(commit_gate / evidence_gate / smoke_test)은 hex digest ASCII 한정으로 깨짐 위험 0 → 수정 불필요.

## 주장 (라벨 포함)

1. **commit_gate / evidence_gate / smoke_test의 cut -c1-16은 sha1sum/md5sum/cksum 출력에 적용** — 라벨: 실증됨
   - 증거: 셋 모두 패턴이 `printf '%s' "$raw" | sha1sum | cut -c1-16` 형태. sha1sum은 16진수 40자 hex 문자열만 출력
   - ref: `commit_gate.sh:24-28`, `evidence_gate.sh:72-76`, `smoke_test.sh:51`

2. **hex digest는 ASCII 한정이라 byte-mode cut도 안전** — 라벨: 실증됨
   - 증거: hex 1글자 = 1바이트 (`0-9a-f`). cut -c1-16은 byte도 char도 동일 결과
   - 결론: 수정 불필요. 현 상태 유지

3. **generate_agents_guide.sh:101의 cut -c1-60은 한국어 description 절단 — 깨짐 발생** — 라벨: 실증됨
   - 증거: 5개 SKILL.md 샘플 중 3개에서 60 byte 경계 절단 시 `�` (replacement char) 발생 (실측)
   - 영향: AGENTS_GUIDE.md 가독성 손상 (표 한 셀 끝부분 깨짐). 데이터 무결성 영향 0 (참조 정보)

4. **수정안: mode_c_log.sh v2와 동일 패턴 적용** — 라벨: 실증됨 (선례)
   - `cut -c1-60` → `"${PY_CMD:-python}" -c "import sys; data=sys.stdin.buffer.read().decode('utf-8',errors='replace'); sys.stdout.buffer.write(data.strip()[:60].encode('utf-8'))"`
   - mode_c_log.sh v2에서 검증 PASS한 패턴 그대로 차용 (코드 정합성)
   - 추가 일감: 1줄 변경

## 반대 안 예상 약점

- **약점 A (GPT 예상)**: "Python 호출 비용. AGENTS_GUIDE.md 자동 갱신 시 SKILL 개수만큼 (~30건) Python 프로세스 spawn → 누적 지연"
  - 반박: 30 × 50ms = 1.5초. AGENTS_GUIDE 갱신은 자주 일어나지 않음 (hook 신설/삭제 시만). 수용 가능
- **약점 B (Gemini 예상)**: "다른 SKILL 메타데이터(name·grade)도 동일 위험? 본 의제 범위 확장 필요?"
  - 반박: 검토 결과 `name`은 디렉터리명(영어), `grade`는 enum(`gate/advisory/measurement` 영어). 한국어 입력 가능 필드는 `description`만. 범위 확장 불필요
- **약점 C (양측 예상)**: "본 의제는 cosmetic. mode_c_log v2와 묶지 않고 별건으로 분리한 이유가 정합 — 합의 즉시 반영 vs 별건 후속 처리?"
  - 반박: 별건 분리는 토론 부하 분산용. 본 라운드에서 합의되면 즉시 처리. 별건 유지가 별 이득 없음 → 즉시 반영 권고

## 착수·완료·검증 조건

- 착수: 본 plan 합의 후 모드 C 진입 → `generate_agents_guide.sh:101` 1줄 변경
- 완료: cut -c1-60 → Python codepoint slice (mode_c_log.sh v2 동일 패턴)
- 검증: AGENTS_GUIDE.md 자동 갱신 1회 실행 → skill 표 "설명" 컬럼 한글 깨짐 부재 확인

## 메타 self-declare

- claude_delta: 양측 답변 수령 후 재계산
- issue_class: **B (시스템 수정 — generate_agents_guide.sh)** → skip_65=false
- round_count: 1 / max_rounds: 3
- 통합 처리: 단일 의제 (4건 중 위험 1건만)
