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
