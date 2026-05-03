---
name: supanova-deploy
description: Pinterest 레퍼런스 → Gemini 영상 → WebP 프레임 + 스크롤 애니메이션 → 템플릿 HTML 결합 → Netlify Drop 배포
trigger: "수파노바 배포", "supanova deploy", "랜딩 영상", "스크롤 애니메이션 랜딩", "Gemini 영상으로 웹페이지", "WebP 프레임 변환", "Netlify Drop"
grade: A
---

# supanova-deploy

> 6단계 절차 / 검증 / 보고는 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 입력 자산 3종 (필수)
1. Pinterest 레퍼런스 이미지 (5장+, 16:9)
2. Gemini Pro로 생성한 영상 파일
3. 결합할 템플릿 HTML

셋 중 하나라도 없으면 진행 금지.

## 절차 (요약)
1. 입력 자산 3종 + 출력 폴더명 확인
2. Gemini 비디오 생성 모드 + Pro 모델 + 16:9
3. Claude Code 후처리: WebP 프레임 시퀀스 + 스크롤 애니메이션
4. 검증: 파일 / 로컬 실행 / 배포 (절대경로 0)
5. Netlify Drop 업로드 (output 폴더, ZIP 아님)

## 산출물
```
supanova-deploy-output/
  index.html
  assets/{css,js,img}/
  frames/{0001.webp ...}
  README_deploy.txt
```

## verify
```bash
python validate_frames.py
# 프레임 파일명 연속성 + 절대경로 0건 + index.html 존재
```

## 실패 시
- 입력 자산 미확보 / WebP 변환 실패 / 절대경로 포함 → FAIL
- 상세 → MANUAL.md "실패 조건" + "중단 기준"

## 한 줄 원칙
좋아 보이는 HTML이 아니라, **재배포 가능한 랜딩 산출물 폴더**.
