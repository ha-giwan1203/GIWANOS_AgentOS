# VELOS v2-fts-lockin 릴리즈 노트

## 🏆 골든 스냅샷 정보

**파일 경로**: `backup/velos_golden_20250819_171455.db`  
**생성 시간**: 2025-08-19 17:14:55  
**파일 크기**: 262,144 bytes  
**SHA256 해시**: `E31FF82CDB05BB2D5D06542DDAFBF96864FEC0B7A72FB70223342DBC2B402F3E`

## 🔒 SQL 스키마 파일 보호

**파일**: `scripts/sql/fts_lockin_ext.sql`  
**상태**: 읽기 전용 + 해시 가드  
**SHA256 해시**: `B7B57815C1CEAF133CD52314CD82A8D7C6E8945A44E89A06A118E48597555721`

## 📊 검색 품질 메트릭 (기준값)

- **search.qps**: 18,922/s (기준값 1,000/s 초과)
- **search.latency_p50**: 0.0ms (기준값 50ms 미만)
- **fts.rebuild_count**: 0/7days (기준값 1/주 미만)

## ✅ 검증 결과

```
schema_guard: OK
fts_healthcheck: OK
insert=1 update(beta)=1 alpha_after_update=0 after_delete=0
FTS_OK
```

## 🛡️ 방어 체계

1. **스키마 버전**: 2 (최신)
2. **FTS 상태**: 완벽 정상
3. **자동 복구**: 5단계 복구 프로세스
4. **카나리아 헬스체크**: 프로세스 시작 시 자동 실행
5. **주간 유지보수**: 자동 스케줄러 등록
6. **pre-commit 가드**: 로컬 삽질 방지
7. **CI 가드**: 선행 검증 단계

## 🚨 장애 퀵런북

### 30초 자가검사
```powershell
python scripts\py\check_schema_guard.py; `
python scripts\py\fts_healthcheck.py; `
python scripts\py\fts_smoke_test.py; 'FTS_OK'
```

### "사고 났다" 복구 절차
1. `python scripts\py\fts_healthcheck.py` 실패 →
2. `python scripts\py\fts_emergency_recovery.py` 실행 →
3. 다시 헬스체크 →
4. 안 되면 `recreate_velos_db.py` →
5. 그래도 불안하면 골든 스냅샷 스왑

### 골든 롤백 원라이너
```powershell
$g = Get-ChildItem "C:\giwanos\backup\velos_golden_*.db" | 
     Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $g.FullName "C:\giwanos\data\velos.db" -Force
```

## 📋 중요 규칙

- **CI/러너가 빨간불이면 배포 중단. 변명 금지.**
- **접두사 검색은 꼭 별(*) 붙인다**: `search_memory(cur, "deploy*")`
- **LIKE의 %는 금지**: FTS의 `term*` 패턴 사용
- **memory.id는 INTEGER PRIMARY KEY 유지**: tombstone 방어
- **FTS에 % 쓰는 사람 나오면 잡아라**: LIKE는 다른 우주다

## 🎯 완료 선언

**지금 상태는 숫자도, 스케줄도, CI도 다 당신 편입니다!**

누가 또 FTS를 발로 차면:
- **로그가 이름 부르고**
- **CI가 발목 잡고** 
- **러너가 재건합니다**

**잘했습니다. 이제 일이나 굴리세요!** 🚀✨

## Operational Appendix (v2-fts-lockin)

- Tag: v2-fts-lockin
- Schema version: 2
- Golden snapshot:
  - Path: `C:\giwanos\backup\velos_golden_20250819_171455.db`
  - SHA256: `E31FF82CDB05BB2D5D06542DDAFBF96864FEC0B7A72FB70223342DBC2B402F3E`
- SQL schema file:
  - Path: `scripts/sql/fts_lockin_ext.sql`
  - SHA256: `B7B57815C1CEAF133CD52314CD82A8D7C6E8945A44E89A06A118E48597555721`
- SQLite compatibility:
  - Minimum: 3.35.0+ (FTS5)
  - Recommended: 3.40.0+ (bm25 available; fallback to time-order if absent)

### Healthcheck (daily, 30s)
```powershell
python scripts\py\check_schema_guard.py; python scripts\py\fts_healthcheck.py; python scripts\py\fts_smoke_test.py; 'FTS_OK'
```
Expected: alpha_after_update=0, after_delete=0, final FTS_OK.

### Rollback (golden)
```powershell
$g = Get-ChildItem "C:\giwanos\backup\velos_golden_*.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $g.FullName "C:\giwanos\data\velos.db" -Force
```

### Emergency Recovery
```powershell
python scripts\py\fts_emergency_recovery.py
```

### Scheduled Maintenance
- Task: VELOS FTS Weekly (Sun 03:30, SYSTEM)
- Actions: optimize + WAL checkpoint

### Blockers
- memory.id must remain INTEGER PRIMARY KEY.
- Use term* for prefix; do not use % with MATCH.
