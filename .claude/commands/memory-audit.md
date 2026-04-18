---
description: MEMORY.md 비대화/충돌/구식 항목 점검
allowed-tools: Read, Grep, Glob
skill-alias: memory-audit (Skill(skill="memory-audit") 공통 지시문)
---

# memory-audit

MEMORY.md와 개별 메모리 파일을 점검하여 다음을 확인:

1. **비대화 점검**: MEMORY.md가 200줄을 초과하는지 확인
2. **고아 파일**: MEMORY.md에 없는 메모리 파일이 있는지 확인
3. **깨진 링크**: MEMORY.md에 있으나 실제 파일이 없는 항목
4. **구식 항목**: 프로젝트 현재 상태와 맞지 않는 메모리 (파일/함수명 변경 등)
5. **중복 항목**: 같은 내용을 다른 파일에 중복 기록한 경우

## 실행 방법
1. `~/.claude/projects/*/memory/MEMORY.md` 읽기
2. 각 링크된 파일 존재 여부 확인
3. memory 디렉토리 내 MEMORY.md에 없는 파일 탐지
4. 각 메모리 파일의 description과 현재 프로젝트 상태 대조

## 출력 형식
```
[MEMORY AUDIT]
- 총 항목: N개
- 고아 파일: [목록]
- 깨진 링크: [목록]
- 구식 의심: [목록 + 사유]
- 판정: PASS / WARN (정리 필요) / FAIL (즉시 수정)
```
