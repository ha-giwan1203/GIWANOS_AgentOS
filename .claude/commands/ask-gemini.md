# Gemini CLI 직접 호출 (minion 패턴)

Claude Code가 Gemini CLI를 부하(minion)로 호출해 답변을 받는다.
웹 UI(`/gemini-send`)와 달리 CLI 헤드리스 모드(`gemini -p`)로 즉시 응답.

## 인자

- `$ARGUMENTS`: Gemini에 전달할 질문/지시 (필수)

## 사용 시점 (Claude가 판단)

다음 경우 자동 호출 후보:
1. **WebFetch fallback**: Claude WebFetch 실패한 사이트(Reddit 등) 정보 필요
2. **대용량 분석**: 1M 토큰급 파일/문서 전수 분석 필요 (Gemini 1M 컨텍스트 활용)
3. **멀티모달**: 이미지/영상/오디오 분석 (자막 없는 영상 등)
4. **외부 정보 교차 검증**: GPT 답변에 추가로 다른 모델 의견 필요
5. **빠른 가설 확인**: 코드/문서 외 일반 지식 빠른 확인

다음 경우 사용 금지:
- 본 저장소 파일 수정 (Claude Code 단독)
- Git/MCP/hooks 작업 (Claude Code 단독)
- 사용자 환경 의사결정 (사용자 확인 필요)

## 실행 순서

### 1. 환경 확인 (생략 가능)

```bash
gemini --version  # 0.38 이상
ls ~/.gemini/api_key.env  # API 키 존재
```

### 2. 헤드리스 호출

```bash
echo "$ARGUMENTS" | gemini -p "사용자 질의에 한국어로 간결히 답하세요. 일반론·과잉설명 금지." -m gemini-2.5-flash 2>&1 | grep -v "Assertion failed" | grep -v "UV_HANDLE_CLOSING"
```

- `-p`: 헤드리스(non-interactive) 모드
- `-m gemini-2.5-flash`: 빠른 모델 기본 (대용량 필요 시 `gemini-2.5-pro` 변경)
- `grep -v "Assertion failed"`: Windows libuv 종료 노이즈 필터링 (응답 영향 없음)

### 3. 결과 처리

- 정상 응답 → Claude가 판단/검증 후 사용자에게 전달
- 빈 응답 → API 키/네트워크 점검
- 오류 → 메시지 그대로 보고 (자체 판단 금지)

## 무결성 검증 (Gemini Round 5 합의 조건)

Gemini 응답을 그대로 채택하지 않는다:
1. **사실 주장**: 본 저장소 실물 파일/Git/문서로 대조 검증
2. **수치/날짜**: 시스템 시간·실제 데이터로 재확인
3. **외부 사실**: 가능 시 추가 검색으로 교차 확인
4. **모호한 답변**: GPT에게 동일 질문 → 비교

## 모델 선택 가이드

| 용도 | 모델 | 이유 |
|------|------|------|
| 빠른 답 | `gemini-2.5-flash` | 빠름, 저비용 |
| 대용량 분석 | `gemini-2.5-pro` | 1M 컨텍스트, 깊이 |
| 영상 | `gemini-2.5-flash` | 멀티모달 |

## 호출 예시

```bash
# 빠른 질의
echo "Claude Code v2.5의 새 기능 3개 알려줘" | gemini -p "한국어로 답" -m gemini-2.5-flash

# 파일 입력
cat large_log.txt | gemini -p "이상 패턴 5개만 추출" -m gemini-2.5-pro

# 짧은 컨텍스트
echo "1+1=?" | gemini -p "" -m gemini-2.5-flash
```

## 주의사항

- [NEVER] `gemini` CLI를 통한 본 저장소 파일 수정 금지 (`gemini -y` 등 yolo 모드 절대 금지)
- [NEVER] API 키 출력/로그 노출 금지
- [MUST] 모든 응답은 무결성 검증 후 사용
- [MUST] Windows에서 libuv "Assertion failed" 노이즈는 응답에 영향 없음, grep 필터로 제거
- 비용: Gemini API 요금제 한도 내 (현재 ₩10,000 캡 — 세션62 설정)

## 비교: 다른 Gemini 호출 경로

| 경로 | 도구 | 사용 시점 |
|------|------|----------|
| `/ask-gemini` | CLI 헤드리스 | Claude 자동 호출, 빠른 답 |
| `/gemini-send` + `/gemini-read` | 웹 UI (Chrome MCP) | 토론, 멀티턴, 사용자 확인 가능 |
| Gemini API 직접 | Python 스크립트 | 영상 분석 등 멀티모달 (`90_공통기준/토론모드/gemini/`) |
