# /video — YouTube 영상 프레임+자막 통합 분석

## 용도
YouTube URL을 받아 영상 다운로드 → 프레임 추출 → 자막 추출 → 멀티모달 통합 분석

## 인수
- `$ARGUMENTS`: YouTube URL (필수)

## 실행 순서

### Phase 0 — 플랜모드 감지
현재 플랜모드 상태인지 확인한다.
- **플랜모드 ON**: Phase 1~7 실행 계획을 플랜 파일에 작성 → ExitPlanMode로 승인 요청 → 승인 후 Phase 1부터 실행
- **플랜모드 OFF**: Phase 1로 바로 진행

### Phase 1 — 파이프라인 실행
```bash
PYTHONUTF8=1 python "90_공통기준/스킬/youtube-analysis/youtube_analyze.py" "$ARGUMENTS" --max-frames 15
```

### Phase 2 — 매니페스트 읽기
출력된 `manifest.json` 경로를 Read로 열어 영상 메타 정보 확인.

### Phase 3 — 프레임 + 자막 통합 분석
1. `transcript.txt` Read → 전체 내용 파악
2. `frames/` 폴더의 주요 이미지를 Read → 시각 정보 확인 (코드, UI, 설정 화면 등)
3. 자막 타임스탬프와 프레임 시점 교차 매핑
4. SKILL.md 9개 관점으로 분석 + A/B/C 판정

### Phase 4 — 구조화 출력
SKILL.md 수동 모드 Step 3 출력 포맷을 따른다.

### Phase 5 — 우리 환경 대비 갭 분석 + 개선안
1. 영상 기법/구조를 현재 저장소(hooks, rules, settings, 스킬, MCP 등)와 대조
2. 갭 식별 → 개선안 도출 → A/B/C 판정
3. 출력: 갭 비교표 + 개선 제안 목록

### Phase 6 — 결과 저장
- Notion DB에 upsert + Drive 업로드 (SKILL.md Step 4 참조)

### Phase 7 — 상태 갱신 + 커밋 + GPT 공유
1. TASKS.md / HANDOFF.md 갱신
2. 커밋 + 푸시
3. GPT에 SHA + 결과 요약 공유
4. 사용자 보고

## 참조 스킬
`90_공통기준/스킬/youtube-analysis/SKILL.md`

## 전제 조건
- `yt-dlp`, `ffmpeg`, `youtube-transcript-api` 설치
- 영상 접근 가능 (비공개/삭제 영상 불가)
