# pptx-generator — MANUAL

> 3층 아키텍처 / Beautify 규칙 / QA 3축 / MVP. SKILL.md는 호출 트리거 + 80줄 요약.

## 트리거
| 입력 패턴 | 동작 |
|----------|------|
| "PPT 만들어", "대책서 생성", "발표자료 만들어" | 신규 생성 |
| "PPT 수정", "슬라이드 바꿔" + 파일 경로 | 템플릿 편집 |
| "pptx" + 데이터 파일 경로 | 데이터 주입 생성 |

## 아키텍처 (3층)
```
A. 의미 해석층 — 입력 → 슬라이드 역할 (제목/요약/데이터/결론)
B. 시각 타입 선택층 — 규칙 테이블로 차트/표/도형/이미지 분기
C. 렌더링층 — python-pptx + Matplotlib + Beautify 규칙 엔진
```

### A. 의미 해석층
| 입력 유형 | 우선순위 | 처리 |
|----------|---------|------|
| 구조화 데이터 (Excel/JSON/CSV) | 1순위 | 컬럼 → 슬라이드 매핑 |
| 정형 문서 (대책서, 보고서) | 2순위 | 섹션 → 슬라이드 매핑 |
| 프롬프트만 | 3순위 | AI 문안 생성 → 슬라이드 매핑 |

### B. 시각 타입 (Visualize 엔진)
| 데이터 패턴 | 시각 타입 | 도구 |
|------------|----------|------|
| 수치 비교 (2개+) | 막대/선 차트 | matplotlib → 이미지 |
| 비율/구성 | 원형 차트 | matplotlib → 이미지 |
| 원인-대책 쌍 | 2단 표 | python-pptx 네이티브 |
| 프로세스/절차 | 순서도 | Graphviz → PNG |
| 타임라인 | 화살표 연결 | Graphviz → PNG |
| 조직/계층 | 조직도/트리 | Graphviz → PNG |
| KPI/핵심 수치 | 큰 숫자 카드 | python-pptx 텍스트 |
| 사진/증빙 | 이미지 배치 | python-pptx add_picture |

### C. 렌더링층

#### Beautify 규칙
| 규칙 | 값 |
|------|---|
| 여백 | 슬라이드 폭의 5~7% |
| 제목 높이 | 슬라이드 높이의 12~15% |
| 본문 글머리 | 최대 5개 |
| 색상 | 주색 1 + 보조색 1~2 + 강조색 1 |
| 폰트 | 제목 28~36pt / 본문 14~18pt / 캡션 10~12pt |
| 밀도 초과 | 자동 분할 (1→2슬라이드) |
| 텍스트 | 네이티브 PPT 텍스트 우선 (이미지 X) |

#### 색상 팔레트 (제조업 기본)
| 용도 | 색상 | Hex |
|------|------|-----|
| 주색 (헤더) | 진한 남색 | 1E2761 |
| 보조색 (배경) | 연한 회색 | F2F2F2 |
| 강조색 (포인트) | 주황 | E8702A |
| 텍스트 (본문) | 진회색 | 333333 |
| 양호/PASS | 녹색 | 2C5F2D |
| 불량/FAIL | 적색 | C0392B |

## 작업 모드

### 모드 1: 템플릿 편집
```python
from pptx import Presentation

prs = Presentation("template.pptx")
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                # 텍스트 치환
                pass
prs.save("output.pptx")
```

절차: 구조 분석 → 치환 매핑 → shape 순회 교체 → QA → 저장

### 모드 2: 신규 생성
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

절차: 의미 해석 → 시각 타입 → Beautify → 렌더링 → QA → 저장

## QA 프레임워크 (3축)

### 축 1: 텍스트 검사
```bash
python -m markitdown output.pptx
```
확인: 누락 콘텐츠 / placeholder 잔존 (`xxxx`, `lorem`) / 오탈자, 순서

### 축 2: 시각 검사
```bash
# LibreOffice
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide

# python-pptx + Pillow 썸네일
python -c "
from pptx import Presentation
prs = Presentation('output.pptx')
print(f'슬라이드 수: {len(prs.slides)}')
for i, slide in enumerate(prs.slides):
    shapes = [s.name for s in slide.shapes]
    print(f'  Slide {i+1}: {len(shapes)} shapes - {shapes[:5]}')
"
```
확인: 요소 겹침 / 텍스트 잘림 / 여백 / 색상 대비

### 축 3: 구조 검사
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
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size and run.font.size >= Pt(24):
                            has_title = True

            if shape.left < 0 or shape.top < 0:
                issues.append(f"Slide {slide_num}: {shape.name} 음수 좌표")
            if shape.left + shape.width > prs.slide_width:
                issues.append(f"Slide {slide_num}: {shape.name} 우측 초과")
            if shape.top + shape.height > prs.slide_height:
                issues.append(f"Slide {slide_num}: {shape.name} 하단 초과")

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
생성 → 텍스트 → 시각 → 구조 → 발견 시 수정 → 재검증
최소 1회 fix-and-verify 필수
```

## MVP 대상
| # | 문서 유형 | 샘플 | 특징 |
|---|----------|------|------|
| 1 | 품질 대책서 | 각인텅_대책서_대원테크.pptx | 원인분석+대책+일정, 사진 |
| 2 | 월간 생산실적 | (신규) | 표+차트 중심, 데이터 주입 |

## 의존성
| 패키지 | 버전 | 용도 |
|--------|------|------|
| python-pptx | 1.0.2 | 핵심 |
| matplotlib | 3.10.8 | 차트 |
| Pillow | 12.2.0 | 이미지 |
| markitdown[pptx] | - | 텍스트 QA |
| lxml | 6.0.2 | XML |

선택:
| graphviz (Python) | 0.21 | API |
| Graphviz (바이너리) | 14.1.4 | dot 렌더링 |
| LibreOffice | - | PDF 변환 시각검사 |

### 다이어그램 모듈 (diagram_renderer.py)
| 함수 | 용도 |
|------|------|
| `render_flowchart()` | 순서도 (분기) |
| `render_process()` | 프로세스 흐름 (순차) |
| `render_org_chart()` | 조직도/계층 |
| `insert_diagram()` | 슬라이드 비율 유지 삽입 |
| `auto_select_visual()` | 데이터 설명 → 시각 타입 추천 |

노드 자동 판정: "?"/"판정"/"검사" → diamond, "시작"/"입고" → oval(녹색), "종료"/"반품" → oval(적색)

## 실패 조건
| 조건 | 판정 |
|------|------|
| python-pptx 미설치 | FAIL |
| 템플릿 읽기 실패 | FAIL |
| QA 3축 중 1축이라도 미통과 | FAIL |
| 슬라이드 0장 | FAIL |
| matplotlib 차트 에러 | FAIL |

## 중단 기준
1. 원본 템플릿 직접 수정 시도 — 복사본만 작업
2. shape 음수/슬라이드 범위 초과 5건+ — 레이아웃 붕괴
3. placeholder 잔존 다수 — 데이터 매핑 실패
4. 폰트 8pt 미만 다수 — 가독성

## 검증 항목
- QA 텍스트 PASS (placeholder 0)
- QA 시각 PASS (겹침/잘림 0)
- QA 구조 PASS (좌표/폰트/제목 충족)
- 슬라이드 수 의도와 일치
- Beautify 색상 팔레트 준수

## 되돌리기
| 범위 | 방법 |
|------|------|
| 생성 결과물 | output.pptx 삭제 |
| 차트 이미지 | 임시 png 삭제 |
| 원본 템플릿 | 미수정 (복사본) — 복원 X |

## 제약/주의
- 텍스트는 네이티브 PPT (이미지 변환 X)
- 차트는 matplotlib 이미지 (PPT 네이티브 차트보다 시각 품질 우선)
- 원본 템플릿 직접 수정 금지 (복사본)
- QA 3축 통과 후에만 완료
- 디자인은 Beautify 규칙 준수
