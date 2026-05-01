# SmartMES mesclient.exe 트래픽 캡처 (Phase A)

> Plan: `C:\Users\User\.claude\plans\wiggly-gliding-sundae.md`
> 실측일: 2026-05-01 17:36~17:38 KST
> 실측자: Claude (computer-use + Get-NetTCPConnection 폴링)
> 환경: 1920×1080, mesclient.exe PID 2800 (재기동 후 23240 → 2800)

## 0. 측정 방법

- 관리자 권한 미보유 → PktMon/Wireshark 사용 불가 (드라이버 액세스 거부)
- **사용자 권한 대안**: `Get-NetTCPConnection -OwningProcess <PID>` 폴링
- 한계: 페이로드 미관찰. host:port + 연결 상태만 확보 → 프로토콜 종류와 endpoint 패턴 식별은 가능
- 잡셋업 화면 진입 → 제품 드롭다운 → 첫 서열 선택 → 공정 드롭다운 4단계에서 매 단계 직후 TCP 스냅샷

## 1. 결과 — 단일 서버 + 3개 비표준 포트

mesclient.exe 가 **단 한 서버 (`210.216.217.95`, 사내 IP) 의 3개 포트만 사용**.

| 포트 | 표준 매핑 | 연결 패턴 | 용도 추정 |
|------|----------|----------|----------|
| **6379** | Redis (RESP 바이너리 프로토콜) | 2 connection persistent | 세션 캐시·실시간 데이터 공유 (.NET 클라이언트가 Redis 직접 접속) |
| **18100** | 비표준 | 단발 (요청 후 close-wait) | 메인 RPC — 부팅 시 1, 이후 액션마다 새로 열림 |
| **19220** | 비표준 | 단발 (요청 후 close-wait) | 잡셋업 진입 시 추가됨. 마스터/메뉴 데이터 조회 추정 |

**표준 HTTP/HTTPS (80/443) endpoint 0건.**

## 2. 단계별 TCP 변화 로그

### Step 1 — SmartMES 메인 메뉴 (잡셋업 클릭 직전)
```
58460 → 210.216.217.95:6379  Established
58461 → 210.216.217.95:6379  Established
58459 → 210.216.217.95:18100 Established
```
→ 부팅·로그인 시점 = 6379(×2) + 18100(×1)

### Step 2 — `[J] 잡셋업` 메뉴 클릭 후
```
58460 → 210.216.217.95:6379  Established
58461 → 210.216.217.95:6379  Established
58459 → 210.216.217.95:18100 Established
58463 → 210.216.217.95:19220 Established  ← 신규
58464 → 210.216.217.95:19220 Established  ← 신규
```
→ **19220 endpoint 2 connection 신규 생성**. 잡셋업 화면이 마스터 데이터를 19220 으로 받아옴

### Step 3 — 제품 드롭다운 화살표 클릭 (제품 리스트 fetch)
```
58460 → 210.216.217.95:6379  Established
58461 → 210.216.217.95:6379  Established
58463 → 210.216.217.95:19220 Established
58464 → 210.216.217.95:19220 Established
58459 → 210.216.217.95:18100 CloseWait    ← 18100 응답 후 종료
```
→ 제품 리스트(`1.RSP3SC0646_A` 외) 가 18100 으로 옴. 응답 후 즉시 close

### Step 4 — `1.RSP3SC0646_A` 선택 (첫 서열)
```
58460 → 210.216.217.95:6379  Established
58461 → 210.216.217.95:6379  Established
58463 → 210.216.217.95:19220 Established
58459 → 210.216.217.95:18100 CloseWait
58464 → 210.216.217.95:19220 CloseWait    ← 19220 한 connection 종료
```
→ 제품 선택 → 19220 으로 추가 정보 받고 close

### Step 5 — 공정 드롭다운 (11개 공정 fetch: [40] 베어링 부시 외)
```
58460 → 210.216.217.95:6379  Established
58461 → 210.216.217.95:6379  Established
58463 → 210.216.217.95:19220 Established
58464 → 210.216.217.95:19220 CloseWait
```
→ 공정 리스트도 같은 19220 endpoint 가 처리. **새 endpoint 0건**

## 3. 화면 캡처 데이터 (검증용)

- 첫 서열 품번: `1.RSP3SC0646_A`
- 풀 네임: `RETRACTOR SP3 SLL CLR MECHANISM MODULE`
- 공정 11개 (스크롤 가능): [40], [60], [91], [120], [180], [200], [210], ...

## 4. 시나리오 판정 → **시나리오 3 (하이브리드 불가) 강력**

근거:
1. **표준 HTTP/HTTPS endpoint 0건** — 생산계획 하이브리드의 전제(`requests` POST + cookie/XSRF)가 성립 불가
2. **단일 서버 + 비표준 커스텀 포트(18100/19220)** — 사내 인프라 직통. 외부 reverse proxy/API gateway 부재
3. **Redis 직접 연결(6379)** — 클라이언트가 캐시 인프라에 직접 RESP 프로토콜로 접속. 외부에서 재현하면 권한 없는 데이터 read/write 위험
4. **단발 connection 패턴** — HTTP 1.0 비슷하지만 비표준 포트. .NET Remoting/WCF NetTcpBinding/custom socket 가능성 큼

## 5. 잔여 불확실성 (관리자 권한 캡처 시 해소 가능)

- 18100/19220 페이로드가 무엇인지 (JSON? XML? .NET binary serialization?) — payload 미관찰
- 만약 plain JSON-over-TCP면 시나리오 1/2 가능성 일부 존재 (희박)
- TLS 적용 여부 — 비표준 포트라 TLS 비적용 가능성 더 큼 (사내망)

## 6. 권고 (사용자 결정용)

- **A. 좌표 자동화 유지 + `pywinauto` PoC** (차선책)
  - 현재 `run_jobsetup.py:36-194` 좌표 의존성 제거
  - .NET ClickOnce 앱이라 UI Automation framework 지원 가능성 높음 (WinForms/WPF 모두 호환)
  - 해상도 변경 안전, 컨트롤 ID 기반 입력
  - 공수 1~2일 PoC

- **B. 관리자 권한 PktMon 1회 추가 캡처** (시나리오 1/2 잔여 검증)
  - 18100 페이로드 1회 dump → JSON/XML/binary 판별
  - 결과가 plain text면 시나리오 1/2 재평가, binary면 시나리오 3 확정 후 종료
  - 사내 보안 정책 사전 확인 필요

- **C. 하이브리드 포기, 좌표 자동화 베이스라인 그대로 운영**
  - 현재 v1.0 baseline 유지, 다중 검사항목/OCR 동적 처리 v1.x 로 진행

**Claude 권고**: A 또는 C. B는 사내 정책 리스크 대비 얻는 정보가 페이로드 형태 1건뿐이라 ROI 낮음.
