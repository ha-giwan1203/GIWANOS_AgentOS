# SmartMES 생산 스케줄 재정렬 자동화

Excel에 정의된 품번 순서대로 SmartMES 생산 스케줄 조정 화면의 대기(R) 항목을 재배치한다.

## 사용 흐름

### 1. 최초 1회: 좌표 캘리브레이션

SmartMES [S] 스케줄 → 생산 스케줄 조정 화면을 띄워놓고:

```bash
python smartmes_reorder.py --calibrate
```

안내에 따라 각 UI 요소에 마우스를 올리고 Enter:
1. 스케줄 리스트 1번 행 중앙
2. 스케줄 리스트 2번 행 중앙 (행 간격 계산용)
3. 품번 컬럼 중앙
4. ↑ 버튼 중앙
5. ↓ 버튼 중앙
6. 저장 버튼 (기본값 1265, 108 확인)

결과는 `smartmes_reorder_config.json` 에 저장된다.

### 2. 실행 (매일 야간 교대 전)

#### dry-run (계획만 확인)
```bash
python smartmes_reorder.py
```

#### 실제 실행
```bash
python smartmes_reorder.py --execute
```

Excel 경로 지정:
```bash
python smartmes_reorder.py --execute --excel "C:\path\to\upload.xlsx"
```

## 동작 원리

1. Excel 읽기 — 품번 순서 (1열: 생산일, 2열: 품번, 3열: 수량)
2. SmartMES API 호출 — 현재 SP3M3 라인 오늘 스케줄 조회 (`list.api` 정상 동작 확인됨)
3. 재정렬 계획 산출 — shift:02 + workStatusCd:R 항목만 대상, Excel 순서로 변환
4. UI 자동화 — 각 항목을 ↑ 버튼으로 목표 위치까지 이동 후 저장 클릭

## 제약

- **save.api** 는 서버 500 오류로 사용 불가 → UI 클릭 방식 사용
- 반드시 SmartMES 화면이 켜진 상태로 실행
- 화면 해상도/레이아웃이 바뀌면 재캘리브레이션 필요
- 보조 모니터("LG FULL HD (2)")에서 실행 전제

## 안전장치

- `pyautogui.FAILSAFE = True` — 마우스 좌상단 이동 시 즉시 중단
- dry-run 기본 — `--execute` 없으면 계획만 출력
- 실행 5초 카운트다운 — Ctrl+C로 중단 가능
