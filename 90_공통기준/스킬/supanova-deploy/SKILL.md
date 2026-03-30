---
name: supanova-deploy
description: >
  Pinterest 레퍼런스 이미지 → Gemini Pro 16:9 영상 생성 → Claude Code WebP 프레임 변환 +
  스크롤 애니메이션 → 템플릿 HTML 결합 → 정적 산출물 검증 → Netlify Drop 배포까지
  재현 가능한 절차로 수행하는 영상 기반 랜딩 페이지 배포 스킬.
  '수파노바 배포', '랜딩 영상 넣어줘', '스크롤 애니메이션 랜딩', 'Gemini 영상으로 웹페이지',
  'WebP 프레임 변환', '템플릿 HTML + 영상 결합', 'Netlify Drop까지 묶어줘' 요청에서 발동한다.
---

# supanova-deploy

## 시작 전 입력 자산 확인
이 스킬은 텍스트만으로 완결되지 않는다.

시작 전에 아래 3개 입력 자산을 먼저 확인한다.
1. Pinterest 레퍼런스 이미지
2. Gemini에서 생성한 영상 파일
3. 결합할 템플릿 HTML

셋 중 하나라도 없으면 바로 진행하지 말고, 부족한 항목만 짧게 보고한 뒤 해당 자산 준비를 먼저 요청한다.

완료 기준은 설명문이 아니라 `index.html + assets/ + frames/` 구조의 재배포 가능한 산출물이다.

---

## 목적
Pinterest 레퍼런스 이미지 → Gemini Pro 16:9 영상 생성 → Claude Code 후처리(WebP 프레임 시퀀스 + 스크롤 애니메이션) → 템플릿 HTML 결합 → 정적 산출물 검증 → Netlify Drop 검수 배포까지 한 번에 재현 가능한 절차로 수행하는 배포 스킬이다.

이 스킬은 디자인 일반론이 아니라, **영상 기반 랜딩 페이지를 빠르게 시제품화하고 검수 가능한 URL까지 확인**하는 작업에 사용한다.

---

## 프로젝트 기준
- 이 프로젝트는 Claude Code 공식 `.claude/skills/` 경로 전제가 아니다.
- `.skill` 패키지는 `90_공통기준/스킬/` 하위에 보관한다.
- 실제 사용은 **GitHub URL 로드 방식**을 기준으로 한다.
- 반복 절차는 프로젝트 문서가 아니라 skill로 분리한다.
- 산출물은 설명문이 아니라 **재배포 가능한 폴더 구조**로 남긴다.

---

## 사용 시점
아래 요청이 들어오면 이 스킬 사용 후보로 본다.

- 수파노바 배포
- supanova deploy
- 랜딩 영상 넣어줘
- 스크롤 애니메이션 랜딩
- Gemini 영상으로 웹페이지 만들어줘
- 영상 넣고 HTML 결합
- Netlify Drop까지 묶어줘
- Pinterest 레퍼런스로 랜딩 만들기
- 영상 기반 웹 랜딩
- 프레임 애니메이션 페이지
- WebP 프레임 변환
- 템플릿 HTML + 영상 결합

---

## 쓰면 안 되는 경우
아래는 이 스킬이 아니라 일반 응답 또는 다른 스킬로 처리한다.

- 단순 HTML 문구 수정
- 단순 카피라이팅 요청
- 단순 이미지 생성 요청
- Netlify 사용법 설명만 필요한 경우
- 디자인 레퍼런스 추천만 필요한 경우
- 영상 생성 없이 정적 랜딩만 필요한 경우

---

## 실행 절차

### 1. 사전 확인
- supanova-deploy.skill GitHub URL 로드 상태 확인
- 입력 자산 3종 보유 여부 확인 (레퍼런스 이미지 / 영상 / 템플릿 HTML)
- 출력 폴더명 사전 확정

### 2. 레퍼런스 이미지 정리
- 최소 5장 이상, 16:9 가로형 우선
- 톤앤무드 단일 방향으로 정리
- 텍스트 과다 삽입 이미지 제외

### 3. Gemini 영상 생성
반드시 **비디오 생성 모드**에서 시작한다.

- 일반 채팅창에서 요청하지 않는다
- `동영상 만들기` 흐름 진입 여부 먼저 확인
- **Pro 모델** 사용 확인
- 16:9 기준 생성
- 결과 영상 다운로드 확인

권장 프롬프트:
```
Create a cinematic 16:9 landing-page background video based on the attached references.
Keep the motion smooth, modern, premium, and web-friendly.
Avoid abrupt cuts, avoid text overlays, avoid clutter.
Camera movement should support scroll-based storytelling.
```

체크포인트: 비디오 생성 모드 진입 ✓ / Pro 모델 ✓ / 16:9 ✓ / 다운로드 ✓

### 4. Claude Code 후처리
생성된 영상을 Claude Code에 드래그앤드롭 후 아래 조건 포함 지시:

권장 지시문:
```
이 영상을 웹 랜딩용 스크롤 애니메이션 자산으로 변환해.
반드시 입력 영상을 WebP 프레임 시퀀스로 변환해서 /frames 폴더에 저장하고,
index.html + assets/ + frames/ 구조로 정리해.
스크롤 방향에 따라 프레임이 자연스럽게 전환되는 애니메이션을 구현하고,
부드럽게 동작하도록 꼭 신경 써서 해줘.
상대경로 기준으로 로컬 실행 가능하게 구성하고,
모든 연관 파일을 포함해줘.
```

체크포인트: WebP 변환 명시 ✓ / frames/ 폴더 ✓ / 상대경로 ✓ / 부드러운 애니메이션 ✓

### 5. 배포 전 검증 3단계
1. **파일 검증**: index.html / assets/ / frames/ 존재, 프레임 파일명 연속성, 절대경로 없음
2. **로컬 실행**: 첫 화면 정상, 스크롤 애니메이션 동작, 404 없음, 콘솔 에러 없음
3. **배포 검증**: Netlify Drop은 ZIP이 아닌 **output 폴더 기준** 업로드, URL 임시 여부 기록

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

README_deploy.txt 권장 항목:
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

---

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

---

## supporting files
- `RUNBOOK.md` — 전체 운영 절차와 단계별 SOP
- `eval_cases.md` — 실패 케이스 5종 테스트 문서
- `deploy_checklist.md` — 사전 준비 / 실행 / 배포 전 체크리스트
- `validate_frames.py` — 프레임 수, 파일명 연속성, 경로 누락 검증 스크립트
- `prompt_template.md` — Gemini용 / Claude Code용 권장 프롬프트 모음
- `sample_output_structure.txt` — 최종 산출물 예시 구조

---

## 한 줄 운영 원칙
좋아 보이는 HTML 한 장이 아니라, **재배포 가능한 랜딩 산출물 폴더**를 남기는 것이 완료 기준이다.
