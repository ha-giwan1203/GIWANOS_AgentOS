# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ROOT=$env:VELOS_ROOT; if(-not $ROOT){$ROOT="C:\giwanos"}
$targets=@("modules","scripts","interface","configs")
$res=@()

Write-Host "[VELOS] 코어 핑거프린트 생성 시작 - $ROOT"

foreach($t in $targets){
    $path = Join-Path $ROOT $t
    if(Test-Path $path){
        Write-Host "[INFO] 스캔 중: $t"
        $files = Get-ChildItem $path -Recurse -File
        $count = 0

        foreach($f in $files){
            try {
                $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
                $rel = $f.FullName.Substring($ROOT.Length+1)
                $res += [pscustomobject]@{
                    rel = $rel
                    sha256 = $h
                    size = $f.Length
                    modified = $f.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss")
                }
                $count++
            } catch {
                Write-Host "[WARN] 파일 해시 실패: $($f.FullName) - $_"
            }
        }

        Write-Host "[INFO] $t`: $count개 파일 처리됨"
    } else {
        Write-Host "[WARN] 경로 없음: $path"
    }
}

$output = Join-Path $ROOT "data\reports\core_fingerprint.json"
$res | ConvertTo-Json -Depth 3 | Out-File $output -Encoding utf8

Write-Host "[OK] 코어 핑거프린트 생성 완료: $($res.Count)개 파일 -> $output"
