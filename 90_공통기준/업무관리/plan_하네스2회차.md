# plan.md — 하네스 파일럿 2회차 (skill-creator harness 모드 개선)

> research.md 완성 후 작성: research_하네스2회차.md (SHA: a8c9a892)
> **승인 상태: [ ] 미승인 — 승인 전 코드/구조 변경 금지**
> 수정 지시는 채팅이 아닌 이 문서의 해당 위치에 인라인 주석으로 남긴다.

---

## 작업 식별

- 작업명: skill-creator harness 모드 3가지 한계 해결
- 기반 research.md: `90_공통기준/업무관리/research_하네스2회차.md`
- 승인 상태: [ ] 미승인 | [ ] 승인완료

---

## 목표 / 비목표 / 완료 조건

**목표:**
- 평가 기준표를 SKILL.md harness 섹션에 참조/요약 규칙으로 연결
- Known Exception 처리 로직을 SKILL.md에 명문화
- 재작업 피드백 루프 단계·중단 조건 표준화

**비목표 (이번 작업에서 하지 않을 것):**
- 기존 6개 mode 구조 변경 금지 (draft/improve/eval/optimize/package/harness)
- 하네스 3인 체제 기본 흐름 변경 금지
- 평가 기준표 가중치 변경 금지
- 조립비정산 파이프라인 실제 재실행 금지 (문서 작업만)

**완료 조건 (이것이 충족되면 작업 완료):**
- skill-creator SKILL.md harness 모드에 평가 기준 참조 섹션 추가됨
- Known Exception 입력 경로 / FAIL vs WARNING 경계가 SKILL.md에 명시됨
- 재작업 루프 단계 (Evaluator 지적 → Generator 수정 → 최대 3회 또는 PASS) 절차가 명시됨
- Evaluator 판정 PASS (기준: 94점 이상, 신규 치명 오류 없음)

**증거 파일 위치:**
- `90_공통기준/스킬/skill-creator-merged.skill` (수정 후 재패키징)
- GitHub commit SHA (push 후 기록)

---

## 접근 방식

### 선택한 방법
- skill-creator-merged.skill ZIP 언패킹 → SKILL.md harness 섹션 수정 → 재패키징

### 참조 구현 / 기존 코드 예시
- 파일/경로: `90_공통기준/업무관리/하네스_스킬평가기준표.md` (평가 기준 원본)
- 파일/경로: `90_공통기준/업무관리/하네스_운영가이드.md` (3인 체제 구조 원본)
- 참조 포인트: harness 모드 Full 실행 절차, Evaluator 판정 4단계 구조

### 선택하지 않은 방법 및 이유
- 새 스킬 파일 생성: 기존 skill-creator 구조 유지가 목표이므로 불필요
- 별도 평가 기준표 스킬 생성: 이번 범위 밖 (비목표)

---

## 구현 계획

> **승인 후에만 구현 시작. 구현 시작 프롬프트: "plan.md 기준으로 구현 시작해"**

### Step 1 — [ ] 평가 기준표 참조 섹션 추가
- 수정 파일: `skill-creator-merged/SKILL.md` (harness 모드 설명 섹션)
- 주의사항: 기존 mode 표 구조 변경 금지, 섹션 추가만 허용
<!-- [수정금지] harness 모드 트리거 조건 키워드는 변경하지 않는다 -->
**세부 작업:**
- [ ] skill-creator-merged.skill ZIP 언패킹
- [ ] SKILL.md harness 섹션에 "평가 기준 참조" 항목 추가 (기준표 파일 경로 + 4항목 요약)
- [ ] 변경 내용 확인 후 재패키징

### Step 2 — [ ] Known Exception 처리 섹션 추가
- 수정 파일: `skill-creator-merged/SKILL.md` (harness 모드 내 Evaluator 절차)
- 주의사항: 예외 처리 규칙이 Evaluator 판정 흐름을 바꾸면 안 됨
<!-- [신규추가] Known Exception 섹션 — 입력 경로: STATUS.md 또는 plan.md의 [예외처리] 인라인 주석 -->
**세부 작업:**
- [ ] Known Exception 정의: STATUS.md 등록 예외는 즉시 FAIL 아닌 감점/INFO 처리
- [ ] FAIL vs WARNING 경계 명시: 신규 미매칭/구조 누락 = FAIL, 기존 Known Exception = WARNING
- [ ] Evaluator 절차에 반영

### Step 3 — [ ] 재작업 피드백 루프 표준화
- 수정 파일: `skill-creator-merged/SKILL.md` (harness 모드 재작업 규칙)
- 주의사항: 최대 3회 규칙 유지, BLOCKED 기준 변경 금지
**세부 작업:**
- [ ] 루프 단계 명시: FAIL → Evaluator 지적만 전달 → Generator 수정 → 재판정
- [ ] 중단 조건 명시: PASS 또는 3회 소진 시 중단
- [ ] BLOCKED 전환 조건 유지: 동일 실패 2회 반복

---

## 제약사항 / 인라인 주석 모음

- [변경금지] 기존 6개 mode 구조 (draft/improve/eval/optimize/package/harness)
- [변경금지] 하네스 3인 체제 기본 흐름 (Planner→Generator→Evaluator)
- [변경금지] 평가 기준표 4항목 가중치 (트리거30/오류처리25/실무적용성25/문서완결성20)
- [신규추가허용] harness 모드 설명 섹션 내 보조 내용
- [확인필요] Known Exception 입력 경로가 STATUS.md 외에 다른 파일을 참조해야 하는지

### 구현 표준 프롬프트
```
plan.md 기준으로 구현 시작해. Step 1부터. [수정금지] 항목은 건드리지 마.
```
```
지금 plan.md 범위 벗어났어. 되돌리고 Step N 범위만 다시 해.
```

---

## 진행 상태

| 단계 | 상태 | 비고 |
|------|------|------|
| research.md 완성 | ✅ 완료 | SHA: a8c9a892 |
| plan.md 승인 | ⏳ 대기 | GPT 검토 중 |
| 구현 | ⬜ 미시작 | 승인 후 시작 |
| Evaluator 판정 | ⬜ 미시작 | |
| 완료 | ⬜ 미시작 | |

---

## 재개 위치

- 현재 단계: plan.md GPT 검토 대기
- 막힌 지점: 없음
- 다음 실행 항목: GPT PASS 후 "plan.md 기준으로 구현 시작해" 입력
