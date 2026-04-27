# NotebookLM ↔ Gemini Bridge

Gemini 노트북 페이지 직접 진입 + 토론모드 컨텍스트 주입 절차.

## 배경
2026-04-08부터 Gemini 앱에 NotebookLM이 통합되어 노트북 페이지를 직접 호출할 수 있다.
Gemini와 NotebookLM은 **동일 UUID**를 공유하며 양방향 동기화된다 (실증됨, 2026-04-27 세션114).

### 동기화 제약 (실증됨)
- Gemini에서 만든 노트북 → NotebookLM에 즉시 노출 ✅
- NotebookLM에서 만든 **non-shared** 노트북 → Gemini에 노출 ✅
- NotebookLM에서 만든 **shared** 노트북 (= MCP `add_notebook`으로 등록한 노트북) → **Gemini에 노출 안 됨** ❌
  - NotebookLM 웹에서 `public` 마크로 표시됨
  - 우회: Gemini에서 새 노트북 생성 + 소스 재업로드 (현재 v2 노트북)

## A. Gemini 노트북 페이지 직접 진입 (메인 흐름) — 실측 완료

### Step 1. CDP Chrome 진입 확인
- 토론모드와 동일: 포트 9222 / 프로필 `C:\temp\chrome-cdp` 필수
- `90_공통기준/토론모드/CLAUDE.md` "CDP Chrome 단독 사용" 참조

### Step 2. 노트북 페이지 진입
- registry.yaml에서 도메인의 `gemini_url` 추출
- `mcp__chrome-devtools-mcp__list_pages`로 기존 탭 확인
- 없으면 `new_page(url=<gemini_url>)`
- `select_page(pageId, bringToFront=true)` 활성화

### Step 3. 채팅 입력창 셀렉터
- `.ql-editor.ql-blank.textarea.new-input-ui` (placeholder="Gemini에게 물어보기")
- 일반 Gem 채팅과 동일한 `.ql-editor` — `/gemini-send`의 입력 로직 그대로 재사용 가능

### Step 4. 질의 전송 + 응답 수령
- `/gemini-send` 절차 그대로 사용 (입력창 셀렉터 호환)
- 노트북 페이지에서는 응답이 등록 소스 기반
- `/gemini-read`로 응답 수령

### Step 5. 소스 추가 (선택, 노트북 강화)
- 파일 업로드 메뉴: `button[aria-label="파일 업로드 메뉴 열기"]`
- 파일 input: `[data-test-id="hidden-local-file-upload-button"]`
- 이미지 input: `[data-test-id="hidden-local-image-upload-button"]`

## B. NotebookLM MCP 직접 질의 (Legacy 노트북용 fallback)

> shared 노트북은 Gemini 미노출이므로 MCP 직접 호출만 가능.

### Step 1. MCP 질의
```
mcp__notebooklm-mcp__ask_question(
  notebook_url=<registry.notebooklm_url>,
  question=<질문>
)
```

### Step 2. 응답 정규화 (Claude 수행)
- 인용 marker 정리, 핵심 발췌 추출
- 토큰 절약을 위해 200~400자 요약본 생성

### Step 3. (선택) Gemini 챗에 컨텍스트 주입
- `/gemini-send`로 다음 형식 전송:
```
[노트북 근거 — <노트북명>]
<NotebookLM 응답 발췌·인용>

[질문]
<원래 토론 주제 또는 후속 질문>
```

## C. 토론모드(3-way)에서 노트북 근거 활용

> 라운드 시작 전 양측에 동일한 노트북 근거 배포 → 검증 일관성 확보.

1. Round 시작 전 Claude가 NotebookLM MCP로 도메인 근거 수집
2. 발췌본을 `[근거]` 블록으로 라운드 페이로드 상단에 삽입
3. GPT·Gemini 양측에 동일 페이로드 전송 (gpt-send / gemini-send)
4. 응답 하네스 라벨링 시 `[근거]`와의 일치도 검증 (실증됨/일반론 라벨 판정에 사용)

---

## 셀렉터 메모 (2026-04-27 세션114 — 2차 실측 확정)

> 환경: Gemini PRO 구독자 (s250ppp@gmail.com), CDP Chrome 포트 9222.

### 진입 경로
| 용도 | URL |
|------|-----|
| Notebooks 목록 | `https://gemini.google.com/notebooks/view` (`/view` 필수) |
| 새 노트북 생성 | `https://gemini.google.com/notebooks/create` |
| 노트북 상세 | `https://gemini.google.com/notebook/notebooks/<UUID>` |
| NotebookLM 동일 노트북 | `https://notebooklm.google.com/notebook/<UUID>` (UUID 공통) |

### 사이드 네비
| 용도 | 셀렉터 |
|------|--------|
| 사이드 네비 토글 | `button[data-test-id="side-nav-menu-button"]` |
| Notebooks 진입 | `a[data-test-id="side-nav-entry-button"][aria-label="Notebooks"]` (href=`/notebooks/view`) |
| 새 노트북 (사이드) | `a[data-test-id="side-nav-entry-button"][aria-label="새 노트북"]` |
| Gems 진입 | `a[data-test-id="side-nav-entry-button"][aria-label="Gems"]` |

### 노트북 목록 페이지 (`/notebooks/view`)
| 용도 | 셀렉터 |
|------|--------|
| 새 노트북 만들기 (메인) | `button[data-test-id="open-project-creation-window"]` |
| 첫 사용 스플래시 시작하기 | `button[data-test-id="create-project-button"]` (스플래시 표시 시) |
| 노트북 카드 (목록) | `a[href^="/notebook/notebooks/"]` |
| 카드 텍스트 형식 | `📔\n<노트북명>\n출처 N개` |

### 노트북 생성 페이지 (`/notebooks/create`)
| 용도 | 셀렉터 |
|------|--------|
| 이름 입력 | `input[data-test-id="project-name-input"]` (placeholder="새 노트북", aria="노트북 이름") |
| 저장 버튼 | `button[data-test-id="save-project-button"]` (이름 입력 후 활성화) |

### 노트북 상세 페이지 (`/notebook/notebooks/<UUID>`)
| 용도 | 셀렉터 |
|------|--------|
| 채팅 입력창 | `.ql-editor.ql-blank.textarea.new-input-ui` (placeholder="Gemini에게 물어보기") |
| 파일 업로드 메뉴 토글 | `button[aria-label="파일 업로드 메뉴 열기"]` |
| 파일 input (hidden) | `[data-test-id="hidden-local-file-upload-button"]` |
| 이미지 input (hidden) | `[data-test-id="hidden-local-image-upload-button"]` |
| 노트북 제목 표시 | (h1/title 영역에서 `innerText`로 추출) |

### NotebookLM 웹 (notebooklm.google.com)
| 용도 | 셀렉터 |
|------|--------|
| 노트북 카드 | `project-button` (커스텀 엘리먼트, innerText에 이름 포함) |
| 카드 텍스트 형식 | `📔\nmore_vert\n<노트북명>\n<날짜>·소스 N개` |
| shared 표시 | `public` 텍스트 (legacy/공유 노트북에만 표시) |

---

## 사용자 액션 — 신규 v2 노트북에 소스 업로드

### 자동 동기화 확인된 노트북 2건
| 노트북 | UUID | 소스 |
|--------|------|------|
| 라인배치_대원테크_v2 | `515e5104-12c0-4900-892f-f19a570edd92` | 0개 (업로드 대기) |
| 조립비정산_대원테크_v2 | `b49dc000-49cc-4cb1-9eb2-2a3a3abb028f` | 0개 (업로드 대기) |

### 업로드 권장 절차
1. **legacy 노트북에서 소스 다운로드**
   - NotebookLM 웹(`https://notebooklm.google.com`) 접속
   - "라인배치_대원테크" / "조립비정산_대원테크" (public 마크 있음) 진입
   - 소스 패널 → 각 소스 다운로드
2. **신규 v2 노트북에 업로드**
   - Gemini 신규 노트북 페이지 진입 (위 UUID URL)
   - "파일 업로드 메뉴 열기" → 소스 파일 첨부
3. **확인**
   - 양쪽 (Gemini · NotebookLM)에서 소스가 동일하게 보이는지 검증
4. **legacy 노트북 폐기** (선택)
   - 모든 소스가 v2로 이전된 후 NotebookLM 웹에서 legacy 노트북 삭제
   - registry.yaml에서 legacy 항목 active=false 또는 제거

---

## 변경 이력
- 2026-04-27 신설 + 1차 실측 (사이드 네비·스플래시까지)
- 2026-04-27 2차 실측 — 노트북 생성·상세·소스 업로드 셀렉터 전체 확정
- 2026-04-27 양방향 동기화 실증 (UUID 공통, NotebookLM 웹 직접 확인)
- 2026-04-27 shared 제약 실증 (legacy 노트북 `public` 마크 → Gemini 미노출)
