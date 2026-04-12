---
name: cdp-wrapper
description: >
  CDP(Playwright connect_over_cdp) 브라우저 작업을 Bash 1줄로 호출하는 래퍼 표준.
grade: A
---

# CDP 래퍼 표준 사용법

> 위치: `.claude/scripts/cdp/`
> 목적: CDP(Playwright connect_over_cdp) 브라우저 작업을 Bash 1줄로 호출

## 스크립트 목록

| 스크립트 | 용도 | 예시 |
|---------|------|------|
| cdp_tabs.py | 열린 탭 목록 | `python cdp_tabs.py` |
| cdp_navigate.py | URL 이동 | `python cdp_navigate.py "https://example.com"` |
| cdp_read.py | 페이지 텍스트 추출 | `python cdp_read.py --match-url chatgpt` |
| cdp_exec.py | JS 실행 | `python cdp_exec.py "document.title"` |
| cdp_screenshot.py | 스크린샷 | `python cdp_screenshot.py -o /tmp/ss.png` |

## 공통 옵션

모든 스크립트에 공통 적용:

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--tab N` | 탭 인덱스(0-based) | 첫 번째 탭 |
| `--match-url <패턴>` | URL 부분 일치로 탭 선택 | - |
| `--match-title <패턴>` | Title 부분 일치로 탭 선택 | - |
| `--browser-url` | CDP endpoint | http://localhost:9222 |
| `--timeout` | 타임아웃(ms) | 30000 |

탭 선택 우선순위: `--match-url` > `--match-title` > `--tab` > 첫 번째 탭

## 사용 규칙

1. 비토론 도메인(정산, MES, ZDM 등)에서 브라우저 작업 시 CDP 래퍼 우선
2. Chrome MCP는 토론모드에서만 허용 (domain_guard_config.yaml 참조)
3. 반드시 `PYTHONIOENCODING=utf-8` 환경변수와 함께 실행
4. CDP 브라우저(port 9222)가 열려있어야 동작

## 전제 조건

- Python 3.12 + playwright 설치
- 브라우저가 `--remote-debugging-port=9222`로 실행 중

## 실패 조건

다음 중 하나라도 해당하면 **실행 실패**로 판정한다:

| 조건 | 판정 |
|------|------|
| CDP 포트(9222) 무응답 — 브라우저 미실행 | FAIL |
| Python 또는 playwright 미설치 | FAIL |
| `--match-url` / `--match-title` 탭 매칭 결과 0건 | FAIL |
| PYTHONIOENCODING=utf-8 미설정 상태에서 한글 출력 깨짐 | FAIL |
| 스크립트 실행 시 timeout 초과 (기본 30초) | FAIL |

## 중단 기준

다음 상황에서는 **즉시 중단**하고 사용자에게 보고한다:

1. 연속 3회 CDP 연결 timeout — 브라우저 크래시 의심
2. 탭 매칭 결과가 2개 이상 — 의도와 다른 탭 조작 위험
3. cdp_exec.py 실행 후 페이지 비정상 상태 감지 (빈 응답, 에러 객체 반환)

## 검증 항목

실행 완료 후 반드시 확인:

- [ ] 출력 인코딩 UTF-8 정상 (한글 깨짐 없음)
- [ ] 탭 선택이 의도한 페이지와 일치 (URL/Title 확인)
- [ ] cdp_exec.py 사용 시 반환값이 예상 타입과 일치

## 되돌리기 방법

| 범위 | 방법 |
|------|------|
| 읽기 작업 (tabs/read/screenshot) | 시스템 변경 없음 — 되돌리기 불필요 |
| JS 실행 (cdp_exec.py) | DOM 부작용 발생 시 페이지 새로고침(F5)으로 복원 |
| 네비게이션 (cdp_navigate.py) | 브라우저 뒤로가기 또는 원래 URL 재이동 |
