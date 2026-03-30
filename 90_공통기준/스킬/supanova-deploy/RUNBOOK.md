# supanova-deploy RUNBOOK

## 0. 목적
이 RUNBOOK의 목적은 아래 워크플로우를 **재현 가능한 배포 절차**로 고정하는 것이다.

1. Supanova 계열 `.skill` 패키지 로드
2. Pinterest 레퍼런스 이미지 수집
3. Gemini Pro에서 16:9 영상 생성
4. Claude Code에서 영상 → WebP 프레임 시퀀스 변환 + 스크롤 애니메이션 적용
5. 템플릿 HTML 결합
6. 정적 산출물 검증
7. Netlify Drop 검수 배포 또는 후속 운영 배포

이 문서는 디자인 참고용이 아니라, **실제 실행 가능한 SOP**를 정의한다.

---

## 1. 적용 범위

적용:
- 영상 기반 웹 랜딩 시제품 제작
- Pinterest 레퍼런스를 이용한 모션 랜딩 생성
- Gemini 영상 결과물을 HTML 랜딩에 결합하는 작업
- WebP 프레임 기반 스크롤 애니메이션 구현
- Netlify Drop으로 빠르게 검수 URL 확인하는 작업

비적용:
- 단순 HTML 수정 / 문구 교체
- 정적 랜딩만 필요한 작업
- Netlify 사용법 설명만 필요한 경우

---

## 2. 프로젝트 기준
- `.skill` 패키지는 `90_공통기준/스킬/` 하위 보관
- 실제 사용은 **GitHub URL 로드 방식** 기준
- 반복 절차는 skill로 분리
- 산출물은 **재배포 가능한 폴더 구조**로 남긴다

---

## 3. 사전 준비 체크리스트

### 3-1. 스킬 로드
- [ ] supanova-deploy.skill GitHub URL 정상 접근
- [ ] Claude Code 세션에서 스킬 호출 가능 상태 확인

### 3-2. 입력 자산 확인 (3종 모두 있어야 시작)
- [ ] Pinterest 레퍼런스 이미지 (최소 5장, 16:9 가로형 우선)
- [ ] Gemini에서 생성한 영상 파일
- [ ] 결합할 템플릿 HTML

셋 중 하나라도 없으면 → 부족한 항목 보고 후 진행 중단

### 3-3. 환경 확인
- [ ] 출력 폴더명 사전 확정
- [ ] Gemini Pro 플랜/모델 접근 가능 여부

---

## 4. 실행 SOP

### Step 1. 레퍼런스 이미지 정리
- 최소 5장, 톤앤무드 단일 방향
- 텍스트 삽입 과다 이미지 제외
- 산출: 레퍼런스 이미지 세트 + 작업 방향 1줄

### Step 2. Gemini 비디오 생성
> ⚠️ 반드시 비디오 생성 모드에서 시작. 일반 채팅 요청 금지.

체크포인트:
- [ ] Tools → 동영상 만들기 진입 확인
- [ ] Pro 모델 선택 확인
- [ ] 16:9 기준 생성
- [ ] 결과 영상 다운로드

권장 프롬프트:
```
Create a cinematic 16:9 landing-page background video based on the attached references.
Keep the motion smooth, modern, premium, and web-friendly.
Avoid abrupt cuts, avoid text overlays, avoid clutter.
Camera movement should support scroll-based storytelling.
```

### Step 3. Claude Code 후처리
> ⚠️ 아래 지시문에서 WebP 변환 + frames 폴더 + 부드러운 애니메이션 3가지 반드시 포함

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

체크포인트:
- [ ] WebP 프레임 변환 완료
- [ ] frames/ 폴더 생성 확인
- [ ] 상대경로 기준 구성
- [ ] 템플릿 HTML과 결합 완료

### Step 4. 로컬 검증
- [ ] 브라우저에서 첫 화면 정상 로드
- [ ] 스크롤 시 프레임 전환 동작
- [ ] 404 없음 / 콘솔 치명 에러 없음
- [ ] 빈 화면 없음

권장 지시문:
```
로컬 기준으로 실행 검증해.
빈 화면, 404, 프레임 누락, 경로 오류, 콘솔 에러를 먼저 보고해.
```

### Step 5. 배포
> ⚠️ Netlify Drop은 ZIP이 아닌 output 폴더 기준 업로드

- [ ] Netlify Drop: output 폴더 드래그앤드롭
- [ ] 배포 URL 확인 및 기록
- [ ] URL 성격 기록 (검수용 임시 / 운영용)
- [ ] 운영 배포 필요 시: Git 연동 또는 CLI 배포로 전환

---

## 5. 산출물 정의

```
supanova-deploy-output/
  index.html              # 최종 진입 파일, 상대경로 기준
  assets/
    css/
    js/
    img/
  frames/                 # WebP 프레임 시퀀스 (누락 시 애니메이션 깨짐)
    0001.webp
    0002.webp
    ...
  README_deploy.txt       # 배포 메타 정보
```

README_deploy.txt:
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

## 6. 배포 전 검증 3단계

| 단계 | 확인 항목 | 실패 판정 |
|------|----------|---------|
| 1. 파일 검증 | index.html / assets/ / frames/ 존재, 프레임 연속성, 절대경로 없음 | frames/ 누락, 절대경로 존재 |
| 2. 로컬 실행 | 첫 화면 정상, 스크롤 애니메이션, 404 없음, 콘솔 에러 없음 | 빈 화면, 프레임 미노출 |
| 3. 배포 검증 | Netlify 폴더 기준 업로드, 첫 화면, URL 성격 기록 | ZIP 업로드, 배포 후 애니메이션 안 보임 |

---

## 7. 완료 기준
- [ ] 산출물 폴더 구조 완성 (index.html + assets/ + frames/)
- [ ] 로컬 검증 PASS
- [ ] 배포 URL 확인 및 성격 기록
- [ ] README_deploy.txt 작성 완료

> 좋아 보이는 HTML 한 장이 아니라, **재배포 가능한 랜딩 산출물 폴더**가 완료 기준이다.

---

## 8. 임시 vs 운영 배포 구분

| 구분 | 방법 | 목적 |
|------|------|------|
| 검수용 임시 배포 | Netlify Drop (폴더 업로드) | 빠른 URL 확인, 검수 |
| 운영 배포 | Git 연동 또는 Netlify CLI | 지속 배포, 버전 관리 |

> Netlify Drop URL은 임시 — 계정 없으면 만료됨. 운영 목적이라면 반드시 Git 연동으로 전환.
