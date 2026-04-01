---
name: zdm-daily-inspection
description: ZDM 시스템 일상점검 자동 입력 (SP3M3 라인)
version: v0.1-placeholder
trigger: "일상점검", "ZDM", "ZDM 점검", "점검 입력", "일상점검 등록"
author: 하지완
last_updated: 2026-04-01
status: placeholder
---

# ZDM 일상점검 자동 입력

## 상태: PLACEHOLDER

이 문서는 도메인 가드 등록을 위한 최소 문서이다.
실제 ZDM 시스템 selector, 입력 방식, 점검 항목 등은 아직 문서화되지 않았다.

**이 문서를 읽었더라도, 실제 ZDM 조작은 사용자 확인 후에만 진행할 것.**

## 대상 업무

| 업무 | 주기 | 시간 | 방식 |
|------|------|------|------|
| ZDM 시스템 일상점검 입력 | 매일 | 08:00 | Chrome 자동화 |

## 대상 라인
- SP3M3 (현재 확인된 대상)

## 실행 전 필수 조건
- Chrome 브라우저가 Claude in Chrome과 연결되어 있어야 함
- ZDM 시스템에 이미 로그인되어 있어야 함

## TODO (문서 보강 필요)
- [ ] ZDM 시스템 URL
- [ ] 점검 화면 selector
- [ ] 입력 항목 및 기본값
- [ ] 저장/제출 절차
- [ ] 오류 대응

## 금지사항
- selector, 입력 방식 미확인 상태에서 추정 실행 금지
- ZDM 시스템 자동 로그인 시도 금지
