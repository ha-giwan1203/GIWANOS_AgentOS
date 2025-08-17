# init_velos_folders.ps1
$root = "C:\giwanos"
$dirs = @(
  "$root\configs",
  "$root\data\logs",
  "$root\data\reports",
  "$root\data\backup",
  "$root\modules",
  "$root\scripts",
  "$root\experiments",
  "$root\archive",
  "$root\trash"
)
$dirs | % { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

# 폴더 설명 파일(빈 폴더 가시화)
$descs = @{
  "$root\configs"     = "환경설정과 샘플 설정 보관"
  "$root\data\logs"   = "런처/서비스/헬스체크 로그"
  "$root\data\reports"= "리포트/결과물"
  "$root\data\backup" = "XML/설정 백업"
  "$root\modules"     = "VELOS 파이썬 모듈"
  "$root\scripts"     = "운영에 쓰는 스크립트(확정본)"
  "$root\experiments" = "실험/임시/미완성"
  "$root\archive"     = "오래된 보관"
  "$root\trash"       = "삭제 대기 (보호 버퍼)"
}
$descs.GetEnumerator() | % {
  Set-Content -Path (Join-Path $_.Key "README.txt") -Value $_.Value -Encoding UTF8
}

Write-Host "[OK] 기본 폴더 구조 생성 완료"
