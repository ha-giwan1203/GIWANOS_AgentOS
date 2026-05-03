---
name: pptx-generator
description: PPT 자동 생성 (템플릿 편집 + 신규 생성). python-pptx + matplotlib + Beautify 규칙 + QA 3축
trigger: "PPT 만들어", "대책서 생성", "발표자료", "PPT 수정", "슬라이드 바꿔", "pptx"
grade: B
---

# PPT 자동 생성

> 3층 아키텍처 / Beautify / QA 3축 / MVP는 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 작업 모드
- **모드 1 템플릿 편집**: 기존 PPTX shape 텍스트/이미지/표 교체
- **모드 2 신규 생성**: 빈 프레젠테이션 (16:9, slide_layouts[6] Blank)

## 절차 (요약)
1. 의미 해석 (입력 → 슬라이드 역할)
2. 시각 타입 선택 (차트/표/도형/이미지)
3. Beautify 규칙 적용 (여백/폰트/색상)
4. python-pptx 렌더링
5. QA 3축 검증 → fix-and-verify 1회+
6. 저장

## QA 3축
- **텍스트**: `markitdown output.pptx` (placeholder 잔존 0)
- **시각**: LibreOffice PDF 또는 python-pptx 썸네일 (겹침/잘림)
- **구조**: 좌표·폰트·제목 검증 (음수 좌표, 8pt 미만 검출)

## verify
- QA 3축 모두 PASS
- 슬라이드 수 = 의도 수량
- Beautify 색상 팔레트 준수 (1E2761 / E8702A / 333333 등)

## 실패 시
- python-pptx 미설치 / 템플릿 손상 / QA 1축 미통과 → FAIL
- 원본 템플릿 직접 수정 시도 → 즉시 중단
- 상세 → MANUAL.md "실패 조건" + "중단 기준" + "되돌리기"
