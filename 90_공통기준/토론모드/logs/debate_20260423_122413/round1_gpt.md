# Round 1 — GPT 응답

## 판정: 조건부 통과 (전면 채택)

## 핵심 수정 요구 (내 초안 대비)
1. **domain_registry YAML → JSON** (실물 `.claude/domain_entry_registry.json`)
2. **count만 → count + 이름 리스트 병행** (final_check readme 이름 대조 실존)
3. **JSON 단일 출력 계약** (셸 재파싱 금지)
4. **M1에서 risk_profile_prompt / domain_entries 실전환 제외** (M4 이월)
5. **Shadow mode 1주 관찰** 추가
6. **risk_profile_prompt 캐시 금지** (UserPromptSubmit 고빈도)

## 2축 경계 (GPT 확정)
- runtime: settings 실파일 / python3 / smoke_fast / smoke_test / block_dangerous / write_marker / after_state_sync
- docs: TASKS/HANDOFF/STATUS 날짜·세션 / README-STATUS 훅수 / AGENTS_GUIDE
- skill_instruction_gate: 별도 축 유지

## 헬퍼 시그니처 최종안
```
parse_hooks_from_settings(json_paths)
extract_readme_hook_names(md_path)
extract_status_hook_count(md_path)
load_domain_entries(json_path)
extract_doc_dates(md_path)
extract_doc_session(md_path)
```

## 마일스톤 A-수정안
- M1: 헬퍼 + list_active_hooks만 전환 (후에 Claude가 "shadow 검증만"으로 더 보수화 — Round 2에서 수용)
- M2: final_check 내부 파싱 헬퍼화
- M3: final_check 2축 분리
- M4: risk_profile_prompt 전환 (마지막)

## Claude 독립 검증 (실물 대조)
- domain_entry_registry.json 실존 (JSON) → 지적 실증
- final_check.sh:71 readme_active_hook_names 함수 실존 → 지적 실증
- 전체 7건 전면 채택, 보류·버림 0건
