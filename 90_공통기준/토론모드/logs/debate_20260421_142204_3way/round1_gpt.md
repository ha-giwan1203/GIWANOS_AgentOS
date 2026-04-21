# Round 1 GPT 응답 (B5)

**D1**: 부분반대. 실행 표면(hook·command·agent) vs 지식 표면(skill·memory) 분리, 강도 차별화.

**D2**: 카운트 정의부터 정규화. README 31 vs raw 44 분모 다름. raw 파일 수로 차단하면 보조 스크립트까지 억울.

**D3**: 하이브리드 방향 맞으나 130% commit 차단은 너무 늦음. 36 기준이면 46까지 통과 → 정원제 체감 없음. 초과 즉시 advisory + 반복 초과/보호영역 추가 시 차단.

**D4**: mtime 90일+미호출 결합 동의하나 그것만으론 위험. 재난 대응 stop hook은 호출 빈도 낮음 → 보호리스트 제외 + 대체 경로 존재 + smoke/호출자 참조 없음까지 결합.

**D5**: 차단 + 정리 후보 제안 동의. 단 "삭제 추천" 아닌 "병합/아카이브/미등록 전환"까지 같이 제안.

**Q3 알고리즘**: 보호리스트 제외 → settings 미등록/보조 스크립트 우선 → 90일 무변경·무호출 → 대체 기능 존재 여부 → 최종 후보. 점수식 단일 X, 4등급(삭제금지/병합후삭제/아카이브우선/즉시삭제후보).

**Q4 면제**: 순감소 커밋(추가≤제거), 긴급보안/복구 라벨, override 1회 + 사유기록 + 24h 만료. 면제 커밋도 다음 세션 quota debt 노출.

**Q5 보호리스트**: 별도 YAML 레지스트리. 필드 path / class(core·guard·recovery) / reason / removal_policy(never·manual·replace-only) / replacement_evidence. 최소 SessionStart·UserPromptSubmit·Stop·commit/evidence 계열 기본 보호.

**추가 비판**: 파일 수 quota와 활성 경로 quota 분리 필수. 이름만 합치고 내부 분기 늘리면 숫자만 줄고 복잡도 올라감.
