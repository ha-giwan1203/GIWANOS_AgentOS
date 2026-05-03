# supanova-deploy — MANUAL

> 6단계 절차 / 검증 / 보고. SKILL.md는 호출 트리거 + 80줄 요약.

## 시작 전 입력 자산
1. Pinterest 레퍼런스 이미지
2. Gemini에서 생성한 영상 파일
3. 결합할 템플릿 HTML

셋 중 하나라도 없으면 진행 금지. 부족한 항목만 짧게 보고 후 준비 요청.

완료 기준: 설명문 X. `index.html + assets/ + frames/` 구조 재배포 가능 산출물.

## 목적
Pinterest 레퍼런스 → Gemini Pro 16:9 영상 → Claude Code 후처리(WebP 프레임 + 스크롤 애니메이션) → 템플릿 HTML 결합 → 검증 → Netlify Drop 배포까지 한 번에 재현 가능 절차.

영상 기반 랜딩 페이지 빠른 시제품화 + 검수 가능 URL 확인 작업에 사용.

## 프로젝트 기준
- Claude Code 공식 `.claude/skills/` 경로 전제 아님
- `.skill` 패키지는 `90_공통기준/스킬/` 보관
- 실제 사용은 GitHub URL 로드
- 반복 절차는 프로젝트 문서 X, skill로 분리
- 산출물 = 재배포 가능한 폴더 구조

## 사용 시점 (트리거)
- 수파노바 배포 / supanova deploy
- 랜딩 영상 / 스크롤 애니메이션 랜딩
- Gemini 영상으로 웹페이지
- 영상 + HTML 결합 / Netlify Drop
- WebP 프레임 변환 / 템플릿 HTML + 영상 결합

## 쓰면 안 되는 경우
- 단순 HTML 문구 수정
- 단순 카피라이팅
- 단순 이미지 생성
- Netlify 사용법 설명만
- 디자인 레퍼런스 추천만
- 영상 없이 정적 랜딩만

## 실행 절차

### 1. 사전 확인
- supanova-deploy.skill GitHub URL 로드 상태
- 입력 자산 3종 보유
- 출력 폴더명 사전 확정

### 2. 레퍼런스 이미지 정리
- 최소 5장 이상, 16:9 가로형 우선
- 톤앤무드 단일 방향
- 텍스트 과다 이미지 제외

### 3. Gemini 영상 생성
반드시 비디오 생성 모드에서 시작.
- 일반 채팅창 X
- `동영상 만들기` 흐름 진입 확인
- Pro 모델 사용
- 16:9 기준
- 결과 영상 다운로드 확인

권장 프롬프트:
```
Create a cinematic 16:9 landing-page background video based on the attached references.
Keep the motion smooth, modern, premium, and web-friendly.
Avoid abrupt cuts, avoid text overlays, avoid clutter.
Camera movement should support scroll-based storytelling.
```

체크포인트: 비디오 생성 모드 ✓ / Pro ✓ / 16:9 ✓ / 다운로드 ✓

### 4. Claude Code 후처리
영상을 Claude Code에 드래그앤드롭 후 지시:
```
이 영상을 웹 랜딩용 스크롤 애니메이션 자산으로 변환해.
반드시 입력 영상을 WebP 프레임 시퀀스로 변환해서 /frames 폴더에 저장하고,
index.html + assets/ + frames/ 구조로 정리해.
스크롤 방향에 따라 프레임이 자연스럽게 전환되는 애니메이션을 구현하고,
부드럽게 동작하도록 꼭 신경 써서 해줘.
상대경로 기준으로 로컬 실행 가능하게 구성하고,
모든 연관 파일을 포함해줘.
```

체크포인트: WebP 변환 ✓ / frames/ ✓ / 상대경로 ✓ / 부드러운 애니메이션 ✓

### 5. 배포 전 검증 3단계
1. 파일 검증: index.html / assets/ / frames/ 존재, 프레임 파일명 연속성, 절대경로 0
2. 로컬 실행: 첫 화면 정상, 스크롤 애니메이션 동작, 404 0, 콘솔 에러 0
3. 배포 검증: Netlify Drop은 ZIP 아닌 output 폴더 기준 업로드, URL 임시 여부 기록

### 6. 산출물 정의
```
supanova-deploy-output/
  index.html
  assets/
    css/
    js/
    img/
  frames/
    0001.webp
    0002.webp
    ...
  README_deploy.txt
```

README_deploy.txt 권장:
```
Template source:
Gemini model used:
Video ratio: 16:9
Frame format: WebP
Frame count:
Entry file: index.html
Deploy method: Netlify Drop / other
Known issues:
```

## 보고 형식
```
판정:
입력 자산:
생성 영상:
프레임 수:
산출물 구조:
로컬 검증:
배포 검증:
URL 성격: 검수용 임시 / 운영
누락/리스크:
다음 단계:
```

## supporting files
- `RUNBOOK.md` — 운영 절차 SOP
- `eval_cases.md` — 실패 케이스 5종
- `deploy_checklist.md` — 사전/실행/배포 체크리스트
- `validate_frames.py` — 프레임 수/연속성/경로 검증
- `prompt_template.md` — Gemini/Claude Code용 프롬프트
- `sample_output_structure.txt` — 최종 산출물 예시

## 실패 조건
| 조건 | 판정 |
|------|------|
| 입력 자산 3종 중 1개 이상 미확보 | FAIL |
| ffmpeg 미설치 또는 WebP 변환 실패 | FAIL |
| 추출 프레임 수 0 | FAIL |
| index.html에 절대경로 포함 | FAIL |
| Netlify Drop 업로드 실패 | FAIL |

## 중단 기준
1. Gemini 영상 생성 3회 연속 실패
2. 프레임 시퀀스 연속성 깨짐 (validate_frames.py 실패)
3. 로컬 preview 콘솔 에러 다수
4. 원본 템플릿 직접 수정 시도

## 검증 항목
- output/에 index.html + assets/ + frames/ 구조
- 프레임 파일명 연속성 (validate_frames.py PASS)
- index.html 절대경로 0건
- 로컬 브라우저 preview에서 스크롤 애니메이션 정상
- README_deploy.txt 배포 기록 존재

## 되돌리기
| 범위 | 방법 |
|------|------|
| Netlify 배포 | 대시보드에서 임시 URL 삭제 |
| 로컬 산출물 | output/ 폴더 삭제 |
| 원본 자산 | 미수정, 복원 불필요 |

## 한 줄 운영 원칙
좋아 보이는 HTML 한 장이 아니라, **재배포 가능한 랜딩 산출물 폴더**를 남기는 것이 완료 기준.
