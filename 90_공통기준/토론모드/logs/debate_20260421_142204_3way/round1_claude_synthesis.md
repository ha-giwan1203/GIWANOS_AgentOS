# Round 1 Claude 종합안 (B5)

> 양측 매우 우수한 비판 다수 채택. Claude 원안 대폭 수정.
> 라벨 분류: 양측 공통(실증됨) / 한쪽 강조(보류 후 채택) / Claude 원안 수정

## 양측 공통 채택 (실증됨)

1. **D1 카테고리 차별화** (양측 동의)
   - GPT: 실행 표면(hook·command·agent) vs 지식 표면(skill·memory) 분리
   - Gemini: hook/skill/agent 정원제 + memory/command TTL
   - **종합**: 실행 표면(hook·command·agent) = 정원제, 지식 표면(skill·memory) = TTL 자동 만료
2. **D2 Glide Path** (양측 동의)
   - GPT: 카운트 정의부터 정규화
   - Gemini: 현재값을 초기 상한, 주 1~2개 점진 감축
   - **종합**: ①raw 파일수 + 활성 등록수 분리 측정 ②현재 raw 카운트를 초기 상한 ③목표(36/30/12)로 매주 1~2개 감축 ④감축 진척도 invariant 추가
3. **D3 100% 즉시 advisory + 차단 강화** (양측 130% 너무 관대 동의)
   - **종합**: 100% 도달 시 advisory + 신규 추가 시 1 in 1 out 강제 + override는 [bypass-quota] 태그
4. **D4 다중 조건 결합** (양측 동의)
   - **종합**: 4단계 안전 검증 — ①보호리스트 제외 ②90일 호출 0 ③타 모듈 참조 없음 ④대체 경로 존재
5. **D5 4등급 분류** (GPT)
   - **종합**: 삭제금지 / 병합후삭제 / 아카이브우선 / 즉시삭제후보
6. **Q5 별도 YAML 레지스트리** (양측 동의)
   - **종합**: `90_공통기준/protected_assets.yaml` 신설. 필드: path / class(core·guard·recovery) / reason / removal_policy(never·manual·replace-only) / replacement_evidence
7. **Q4 [bypass-quota] override + quota debt 페널티** (양측 동의)
   - **종합**: [bypass-quota] 태그로 1회 통과 + 다음 정상 작업 시 2개 삭제 페널티 + 다음 세션 quota debt 노출

## Claude 추가 채택

8. **활성 경로 quota 분리** (GPT 추가 비판)
   - 파일 수 quota만으론 이름 합치고 내부 분기 늘리는 회피 가능. 활성 경로 quota 별도.
9. **고아(Orphan) 0순위** (Gemini 신규)
   - Q3 알고리즘에서 고아 = "30일 호출 0 + 타 모듈 참조 없음 + 보호리스트 제외" 모두 충족 → 0순위 삭제 후보

## 최종 안 (정원제 6개 + TTL 2개)

### A. 실행 표면 정원제 (현재값 → 목표값, Glide Path)
- hook (.sh): 현재 44 → 목표 36 (주 1~2개 감축)
- command (.md): 현재 30 → 목표 25
- agent (.md): 현재 9 → 목표 12 (여유)

### B. 지식 표면 TTL
- skill: 현재 38, 미사용 90일 자동 archive 후보 표시
- memory entry: 현재 38, 미사용 180일 자동 만료 후보 표시 (기존 "스테일 표시" 정책)

### C. 보호 레지스트리
- `90_공통기준/protected_assets.yaml` 신설
- 기본 보호: SessionStart·UserPromptSubmit·Stop·commit/evidence·debate·session_kernel 계열

### D. 강제 메커니즘
- M1: 신규 추가 시 advisory (현재 카운트 + 상한 표시)
- M2: 100% 도달 시 commit_gate 1 in 1 out 강제 (현재 추가 ≤ 제거 검증)
- M3: [bypass-quota] 태그 = 1회 면제 + 다음 정상 작업 2개 삭제 페널티
- M4: invariant `subtraction_quota_status` 신설 (Layer 1 추가 — B1과 정합)

### E. 산출 알고리즘 (Q3)
1. 보호리스트 제외
2. 고아(30일 호출 0 + 참조 없음) 0순위
3. settings 미등록 / 보조 스크립트 1순위
4. 90일 무변경·무호출 2순위
5. 대체 기능 존재 여부 가중치
6. 4등급 분류: 삭제금지 / 병합후삭제 / 아카이브우선 / 즉시삭제

## 미해결 1건 (양측 답 요청)

**Q-Activate**: Glide Path 시작값 = 현재 raw 카운트(보수)? vs 활성 등록수(엄격)? — GPT는 "raw로 차단 시 보조 스크립트 억울" 주장, Gemini는 "현재 실측치 사용" 주장. 양측 정합 안 명확화 요청.

## 응답 형식
verdict: 통과 | 조건부 통과 | 실패
Q-Activate 답: raw / 활성 / 혼합
이의: 항목 + 근거 1문장
한국어 200자 내외.
