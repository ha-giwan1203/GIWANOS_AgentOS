# supanova-deploy 프롬프트 템플릿

## Gemini 영상 생성 프롬프트

```
Create a cinematic 16:9 landing-page background video based on the attached references.
Keep the motion smooth, modern, premium, and web-friendly.
Avoid abrupt cuts, avoid text overlays, avoid clutter.
Camera movement should support scroll-based storytelling.
```

한국어 버전:
```
첨부한 레퍼런스 이미지를 바탕으로 16:9 랜딩 페이지 배경 영상을 생성해줘.
천천히 돌아가거나 부드럽게 움직이는 시네마틱 스타일로 만들어줘.
텍스트 오버레이, 급격한 컷 전환, 복잡한 요소는 제외해줘.
스크롤 기반 스토리텔링에 어울리는 카메라 무브먼트를 적용해줘.
```

---

## Claude Code 후처리 지시문 (필수)

```
이 영상을 웹 랜딩용 스크롤 애니메이션 자산으로 변환해.
반드시 입력 영상을 WebP 프레임 시퀀스로 변환해서 /frames 폴더에 저장하고,
index.html + assets/ + frames/ 구조로 정리해.
스크롤 방향에 따라 프레임이 자연스럽게 전환되는 애니메이션을 구현하고,
부드럽게 동작하도록 꼭 신경 써서 해줘.
상대경로 기준으로 로컬 실행 가능하게 구성하고,
모든 연관 파일을 포함해줘.
```

---

## 로컬 검증 지시문

```
로컬 기준으로 실행 검증해.
빈 화면, 404, 프레임 누락, 경로 오류, 콘솔 에러를 먼저 보고해.
```

---

## ZIP 압축 지시문 (GitHub 보관용)

```
[프로젝트명] 폴더와 연관된 모든 파일을 함께 ZIP으로 압축해줘.
단, Netlify Drop 업로드는 ZIP이 아니라 output 폴더 기준이야.
```
