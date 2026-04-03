---
name: pptx-generator
description: >
  PPT 자동 생성 스킬. 템플릿 기반 편집 + 신규 생성 지원.
  엔진: python-pptx (단일 Python 스택)
  QA: 텍스트검사 + 시각검사 + 구조검사 3축
  GPT 합의: 2026-04-03 (C+D 혼합, 재사용 우선, MVP 2종)
---

# PPT 자동 생성 (pptx-generator)

## 트리거

| 입력 패턴 | 동작 |
|----------|------|
| "PPT 만들어", "대책서 생성", "발표자료 만들어" | 신규 생성 |
| "PPT 수정", "슬라이드 바꿔" + 파일 경로 | 템플릿 편집 |
| "pptx" + 데이터 파일 경로 | 데이터 주입 생성 |

---

## 아키텍처 (3층 구조)

```
A. 의미 해석층 — 입력 → 슬라이드 역할 판정 (제목/요약/데이터/결론)
B. 시각 타입 선택층 — 규칙 테이블로 차트/표/도형/이미지 분기
C. 렌더링층 — python-pptx + Matplotlib + Beautify 규칙 엔진
```

### A. 의미 해석층

입력 데이터를 분석하여 각 슬라이드의 역할을 판정한다.

| 입력 유형 | 우선순위 | 처리 |
|----------|---------|------|
| 구조화 데이터 (Excel/JSON/CSV) | 1순위 | 컬럼 구조 → 슬라이드 매핑 |
| 정형 문서 (대책서, 보고서) | 2순위 | 섹션 추출 → 슬라이드 매핑 |
| 프롬프트만 | 3순위 | AI 문안 생성 → 슬라이드 매핑 |

### B. 시각 타입 선택층 (Visualize 엔진)

데이터 특성에 따라 시각 타입을 자동 선택한다.

| 데이터 패턴 | 시각 타입 | 도구 |
|------------|----------|------|
| 수치 비교 (2개 이상 항목) | 막대/선 차트 | matplotlib → 이미지 삽입 |
| 비율/구성 | 원형 차트 | matplotlib → 이미지 삽입 |
| 원인-대책 쌍 | 2단 표 | python-pptx 네이티브 표 |
| 프로세스/절차 | 순서도 | python-pptx 도형 조합 |
| 타임라인 | 화살표 연결 | python-pptx 도형 조합 |
| KPI/핵심 수치 | 큰 숫자 카드 | python-pptx 텍스트 박스 |
| 사진/증빙 | 이미지 배치 | python-pptx add_picture |

### C. 렌더링층

#### Beautify 규칙 엔진

| 규칙 | 값 |
|------|---|
| 여백 | 슬라이드 폭의 5~7% |
| 제목 높이 | 고정 (슬라이드 높이의 12~15%) |
| 본문 글머리 | 최대 5개 |
| 색상 | 주색 1 + 보조색 1~2 + 강조색 1 |
| 폰트 크기 | 제목 28~36pt / 본문 14~18pt / 캡션 10~12pt |
| 밀도 초과 | 자동 분할 (1슬라이드 → 2슬라이드) |
| 텍스트 | 네이티브 PPT 텍스트 우선 (이미지 렌더링 금지) |

#### 색상 팔레트 (제조업 보고서 기본)

| 용도 | 색상 | Hex |
|------|------|-----|
| 주색 (헤더/강조) | 진한 남색 | 1E2761 |
| 보조색 (배경) | 연한 회색 | F2F2F2 |
| 강조색 (포인트) | 주황 | E8702A |
| 텍스트 (본문) | 진회색 | 333333 |
| 양호/PASS | 녹색 | 2C5F2D |
| 불량/FAIL | 적색 | C0392B |

---

## 작업 모드

### 모드 1: 템플릿 편집

기존 PPTX 파일을 열어 내용을 교체한다.

```python
from pptx import Presentation

prs = Presentation("template.pptx")
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                # 텍스트 치환 로직
                pass
prs.save("output.pptx")
```

절차:
1. 템플릿 구조 분석 (슬라이드 수, shape 목록, 텍스트 위치)
2. 치환 매핑 생성 (placeholder → 실데이터)
3. shape 순회 → 텍스트/이미지/표 교체
4. QA 실행
5. 저장

### 모드 2: 신규 생성

빈 프레젠테이션에서 슬라이드를 구성한다.

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width = Inches(13.333)  # 16:9
prs.slide_height = Inches(7.5)

slide_layout = prs.slide_layouts[6]  # Blank
slide = prs.slides.add_slide(slide_layout)
```

절차:
1. 의미 해석 → 슬라이드 구성안
2. 시각 타입 선택 → 각 슬라이드별 요소 결정
3. Beautify 규칙 적용 → 레이아웃 계산
4. python-pptx로 렌더링
5. QA 실행
6. 저장

---

## QA 프레임워크 (3축)

> Anthropic skills/pptx QA 패턴 차용 + 구조검사 추가 (GPT 합의)

### 축 1: 텍스트 검사

```bash
python -m markitdown output.pptx
```

확인 항목:
- 누락 콘텐츠
- placeholder 잔존 (`xxxx`, `lorem`, `ipsum`)
- 오탈자, 순서 오류

### 축 2: 시각 검사

슬라이드를 이미지로 변환하여 육안 확인.

```bash
# LibreOffice가 있는 경우
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide

# LibreOffice 없이 (python-pptx + Pillow 썸네일)
python -c "
from pptx import Presentation
prs = Presentation('output.pptx')
print(f'슬라이드 수: {len(prs.slides)}')
for i, slide in enumerate(prs.slides):
    shapes = [s.name for s in slide.shapes]
    print(f'  Slide {i+1}: {len(shapes)} shapes - {shapes[:5]}')
"
```

확인 항목:
- 요소 겹침
- 텍스트 잘림/overflow
- 여백 부족
- 색상 대비 부족

### 축 3: 구조 검사 (GPT 제안 반영)

python-pptx로 프로그래밍 검증.

```python
def qa_structure(pptx_path):
    from pptx import Presentation
    from pptx.util import Pt, Emu
    prs = Presentation(pptx_path)
    issues = []

    for i, slide in enumerate(prs.slides):
        slide_num = i + 1
        has_title = False

        for shape in slide.shapes:
            # 제목 존재 확인
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size and run.font.size >= Pt(24):
                            has_title = True

            # shape bbox 범위 확인 (슬라이드 밖 감지)
            if shape.left < 0 or shape.top < 0:
                issues.append(f"Slide {slide_num}: {shape.name} 음수 좌표")
            if shape.left + shape.width > prs.slide_width:
                issues.append(f"Slide {slide_num}: {shape.name} 우측 초과")
            if shape.top + shape.height > prs.slide_height:
                issues.append(f"Slide {slide_num}: {shape.name} 하단 초과")

            # 최소 폰트 크기 확인
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size and run.font.size < Pt(8):
                            issues.append(f"Slide {slide_num}: 폰트 {run.font.size} 너무 작음")

        if not has_title:
            issues.append(f"Slide {slide_num}: 제목 없음")

    return issues
```

### QA 루프

```
생성 → 텍스트검사 → 시각검사 → 구조검사 → 문제 발견 시 수정 → 재검증
최소 1회 fix-and-verify 사이클 필수
```

---

## MVP 대상

| # | 문서 유형 | 샘플 | 특징 |
|---|----------|------|------|
| 1 | 품질 대책서 | 각인텅_대책서_대원테크.pptx | 원인분석+대책+일정, 사진 포함 |
| 2 | 월간 생산실적 | (신규 생성) | 표+차트 중심, 데이터 주입 |

---

## 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| python-pptx | 1.0.2 | 핵심 엔진 |
| matplotlib | 3.10.8 | 차트 생성 |
| Pillow | 12.2.0 | 이미지 처리 |
| markitdown[pptx] | - | 텍스트 QA |
| lxml | 6.0.2 | XML 처리 (python-pptx 의존) |

선택:
| 패키지 | 용도 |
|--------|------|
| Graphviz | 순서도/다이어그램 (필요 시 설치) |
| LibreOffice | PDF 변환 시각검사 (필요 시 설치) |

---

## 제약 / 주의사항

- 텍스트는 반드시 네이티브 PPT 텍스트로 렌더링 (이미지 변환 금지)
- 차트는 matplotlib 이미지 삽입 방식 (PPT 네이티브 차트보다 시각 품질 우선)
- 원본 템플릿 직접 수정 금지 (복사본에서 작업)
- 생성 결과물은 QA 3축 통과 후에만 완료 판정
- 디자인은 Beautify 규칙 엔진 기준 준수
