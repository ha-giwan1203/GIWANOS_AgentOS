---
name: daily-routine
description: ZDM 일상점검 + MES 생산실적 업로드 통합 자동화 (월~토 08:07 cron)
trigger: "일상점검", "ZDM 점검", "실적 올려", "MES 업로드", "매일 업무", "daily", "/daily"
grade: A
version: 1.0
status: active
---

# 매일 반복 업무 통합 실행

> 상세 절차/실패조건/되돌리기는 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 절차 (요약)
1. KST 일요일 → 즉시 종료
2. ZDM SP3M3 75개 항목 OK 입력 + 누락분 보정
3. BI 파일 갱신 (Z드라이브 → 로컬)
4. MES 직접 HTTP OAuth + 누락일 일괄 업로드 (3회 재시도)

## 실행
```bash
# 자동 (cron daily-routine)
bash .claude/scripts/task_runner.sh daily-routine python3 \
  "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py"

# 수동
python3 "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py"
```

## verify
- ZDM: records 75/75 PASS
- MES: 누락일별 건수+qty 합계 BI 원본 일치
- 일요일 데이터 0건

## 실패 시
- 일요일/BI 0건/MES 중복 = STOP (정상 종료)
- API 연속 실패 = 사용자 보고
- 상세 → MANUAL.md "실패 조건" + "되돌리기"
