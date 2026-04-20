# Round 1 — GPT 응답 (2026-04-20)

**URL**: https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/c/69e57ef4-dd70-83e8-9458-dca5d85f01db
**응답 길이**: 2483자

## 본론 답변

### 1. 근본 원인 진단 (대체로 맞음)
- 핵심은 surrogate escape가 아니라 **네이티브 Windows Python에 POSIX 경로(/c/...)를 넘긴 것이 1차 원인**
- Cygwin 문서: Windows 프로그램은 POSIX 경로 해석 불가 → cygpath 필요
- Python Windows 경로 규칙: 절대경로 판단에 드라이브+루트 요구
- `/c/Users/...` exists False 설명은 정합
- **CP949 단정은 환경 종속성 있음** — "쉘 인라인 전개 과정에서 locale/code page 경유로 한글 경로 깨짐" 정도로 표현 완화 권고
- UTF-8 mode의 surrogateescape는 표준 입출력 처리, 경로 변환 기능 아님

### 2. 수정 3점 방향 정확, 단 범위 부족
- 현 실물 코드는 `python3 <<PY` 안에 `open(r"$RESULT")`로 쉘 변수를 Python 소스에 직접 삽입 — 경로 형식 문제 + 한글 깨짐 둘 다 키우는 패턴
- `<<'PY'` + `os.environ[]` + cygpath 조합은 이번 증상에 맞음
- **중요 추가 쟁점**: `statusline.sh`도 `python3 <<PY`에 `$input` 직접 삽입 — 동일 계열 패턴 → "heredoc 변수 인라인 삽입" 전수 점검 필요

### 3. 170행 stdin 파이프 구간 — 수정 대상 아님
- `printf "${ERRORS[@]}" | python3 -c`는 stdin 전달이라 heredoc 인라인 삽입과 다름
- 구조상 더 안전

### 4. Phase 2-C 승격 타이밍 — 7일 유지
- 18건이 전부 경로/인코딩 결함 때문이라는 건 의심이지 증명 아님
- 현 훅 주석이 "incident 0건 7일 연속"을 승격 조건으로 명시
- 3일로 줄이면 버그 수정 직후 착시를 구조 승격으로 오판 가능성
- **7일 유지 + 실제 3way 커밋 성공 샘플 수까지 확인** 권고

### 5. cygpath + Python 보강 필요 (실패 판정)
- cygpath는 POSIX → Windows 변환 용도로 원래 존재
- 현 fallback `${RESULT/#\/c\//C:/}`는 **C드라이브 전용**, `/d/...`, `/cygdrive/c/...` 못 잡음
- 권고: cygpath 우선 유지 + **fallback 일반화** + Python 쪽 `os.path.normpath()` 또는 regex 정규화 마지막 안전망

## GPT 최종 판정 5개

| # | 항목 | 판정 | 근거 요약 |
|---|------|------|----------|
| 1 | 근본 원인 진단 | **조건부 통과** | POSIX 경로 맞음, CP949 단정 표현 완화 필요 |
| 2 | 수정 3점 변경 충분성 | **조건부 통과** | 방향 맞음, heredoc 인라인 패턴 전수 점검(statusline 포함) 필요 |
| 3 | 170행 stdin 파이프 수정 대상 아님 | **통과** | stdin 전달 구조상 이번 버그 직접 원인 아님 |
| 4 | Phase 2-C 승격 7일 유지 | **조건부 통과** | 7일 유지 + 3way 커밋 성공 샘플 수 확인 병행 |
| 5 | cygpath + bash fallback만으로 충분 | **실패** | C드라이브 전용 한계, fallback 일반화 + Python os.path.normpath 보정 필요 |

## Claude 하네스 분석

| 라벨 | 수 | 항목 |
|------|----|------|
| **채택** | 3건 | statusline.sh 전수 점검 필요(실증됨), Python 측 보정 추가(실증됨), 7일 유지(일반론→근거 타당) |
| **보류** | 1건 | CP949 표현 완화 — 표현 완화는 수용, 원인 진단 자체는 실증 근거 있으므로 절반 반영 |
| **버림** | 0건 | — |

## 쟁점 재정리 (Round 1 후)

1. **cygpath fallback 일반화** — `sed` 또는 `awk`로 `/[a-z]/` prefix를 `[A-Z]:/` 로 변환하는 범용 패턴 필요
2. **Python 측 2차 보정** — `os.path.normpath()` 또는 pathlib 활용
3. **statusline.sh 동시 수정** — 동일 커밋에 포함 vs 별건 분리
4. **hook_common.sh 공통 래퍼** — `py_read_file_utf8 <path>` 헬퍼 함수 추출
