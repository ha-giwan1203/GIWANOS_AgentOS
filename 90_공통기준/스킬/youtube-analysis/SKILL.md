---
name: youtube-analysis
description: >
  YouTube 영상을 URL만으로 자동 분석하는 스킬.
  자막을 자동 추출(youtube-transcript-api)하고 내용 요약 및 실무 적용안을 출력한다.
  '유튜브 분석', '영상 분석', 'YouTube 분석', '영상 요약', '이 영상', '유튜브 요약',
  youtu.be 또는 youtube.com URL이 포함된 요청에서 자동 발동한다.
---

# YouTube 영상 분석 (youtube-analysis)

## 개요

YouTube URL만 주면 자막을 자동 추출해서 내용을 분석하고 실무 적용안을 출력한다.
수동 자막 복붙 없이 젠스파크와 동일한 방식으로 동작한다.

## 트리거 조건

다음 중 하나라도 해당하면 이 스킬을 발동한다:
- 메시지에 `youtu.be/`, `youtube.com/watch` URL 포함
- "유튜브 분석", "영상 분석", "영상 요약", "이 영상 분석", "YouTube 분석" 키워드

## 스크립트 경로

```
C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\youtube-analysis\youtube_transcript.py
```

## 실행 절차

### Step 1 — URL에서 자막 추출

```bash
python "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\youtube-analysis\youtube_transcript.py" "<YouTube_URL>"
```

- 한국어 수동 자막 → 한국어 자동생성 자막 → 영어 순서로 시도
- `--timestamps` 플래그 추가 시 타임스탬프 포함 출력
- 오류 코드: 2=자막비활성화, 3=자막없음, 4=잘못된URL, 5=기타오류

### Step 2 — 자막 내용 분석

추출된 자막을 읽고 아래 포맷으로 분석 결과를 출력한다.

### Step 3 — 출력 포맷

```
## 영상 정보
- 제목: [자막 첫 줄 또는 추론]
- 자막 언어: [출력된 언어 정보]
- 세그먼트 수: [총 개수]

## 요약
[3~5줄 핵심 요약]

## 핵심 내용
| 주제 | 내용 | 실무 적용 여부 |
|------|------|--------------|
| ... | ... | ✅ / ⏳ / ❌ |

## 실무 적용안
[바로 적용 가능한 항목을 번호 목록으로]

## 다음 액션
[구체적 후속 작업 항목]
```

## 오류 처리

| 오류 | 원인 | 대응 |
|------|------|------|
| 자막 비활성화 | 영상 자막 설정 꺼짐 | 영상 설명란 + 댓글로 대체 분석 |
| 자막 없음 | 미지원 언어 또는 비공개 | 영상 설명 URL 요청 |
| 잘못된 URL | URL 형식 오류 | 올바른 URL 재입력 요청 |

## 사용 예시

```
# 기본 분석
이 영상 분석해줘: https://youtu.be/Pbtp17aZ7k4

# 타임스탬프 포함
이 영상 타임스탬프 포함해서 분석해줘: https://youtu.be/xxxx

# Claude 사용환경 개선 목적
이 영상 보고 내 Claude Code 설정에 적용할 게 뭔지 알려줘: https://youtu.be/xxxx
```

## 주의사항

- 자막이 없는 영상은 분석 불가 (자동생성 자막도 없는 경우)
- 영어 영상은 영어로 자막 추출 후 한국어로 번역해서 분석
- 스크립트는 Python 3.x 환경에서 실행 (`youtube-transcript-api` 설치 필요)
- 패키지 설치: `pip install youtube-transcript-api`
