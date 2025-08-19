# [ACTIVE] VELOS 운영 철학 선언문
# 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

param(
    [string]$DbPath = $env:VELOS_DB_PATH ?? "C:\giwanos\data\velos.db"
)

Write-Host "VELOS FTS Weekly Maintenance 시작: $(Get-Date)" -ForegroundColor Green

# 환경 변수 설정
$env:VELOS_DB_PATH = $DbPath

# Python 스크립트 실행
$pythonScript = @'
import os
import sqlite3
import sys

try:
    db = os.environ["VELOS_DB_PATH"]
    print(f"데이터베이스 경로: {db}")
    
    if not os.path.exists(db):
        print(f"ERROR: 데이터베이스 파일이 존재하지 않습니다: {db}")
        sys.exit(1)
    
    con = sqlite3.connect(db, isolation_level=None)
    c = con.cursor()
    
    print("FTS 최적화 시작...")
    c.executescript("""
        BEGIN IMMEDIATE;
        INSERT INTO memory_fts(memory_fts) VALUES('optimize');
        COMMIT;
    """)
    
    print("WAL 체크포인트 수행...")
    checkpoint_result = c.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    print(f"WAL 체크포인트 결과: {checkpoint_result}")
    
    # 데이터베이스 무결성 검사
    print("데이터베이스 무결성 검사...")
    integrity_result = c.execute("PRAGMA integrity_check").fetchall()
    if integrity_result[0][0] == "ok":
        print("무결성 검사 통과")
    else:
        print(f"무결성 검사 실패: {integrity_result}")
        sys.exit(1)
    
    con.close()
    print("FTS 주간 유지보수 완료")
    
except Exception as e:
    print(f"ERROR: FTS 유지보수 실패: {e}")
    sys.exit(1)
'@

try {
    $result = $pythonScript | python -
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FTS 주간 유지보수 성공 완료" -ForegroundColor Green
    } else {
        Write-Host "FTS 주간 유지보수 실패" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "FTS 주간 유지보수 실행 중 오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host "VELOS FTS Weekly Maintenance 완료: $(Get-Date)" -ForegroundColor Green
