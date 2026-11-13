# Dao: empty recycle bin for current user (skip SYSTEM-owned folders)
$log = 'E:\Daodao\recycle_clean.log'
$o = @()
foreach ($d in @('C','D','E','F','G')) {
    $t = $d + ':\$Recycle.Bin'
    if (-not (Test-Path -LiteralPath $t)) { continue }
    $subs = Get-ChildItem -LiteralPath $t -Force -ErrorAction SilentlyContinue
    foreach ($s in $subs) {
        if (-not $s.PSIsContainer) { continue }
        if ($s.Name -notlike 'S-1-5-21-*') { continue }
        $fs = Get-ChildItem -LiteralPath $s.FullName -Recurse -Force -File -ErrorAction SilentlyContinue
        $sz = ($fs | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $sz) { $sz = 0 }
        try {
            Remove-Item -LiteralPath $s.FullName -Recurse -Force -ErrorAction Stop
            $res = 'DEL_OK'
        } catch {
            $res = 'DEL_ERR ' + $_.Exception.Message
        }
        $o += ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $d + ' files=' + @($fs).Count + ' MB=' + [math]::Round($sz/1MB,1) + ' ' + $res)
    }
}
if ($o.Count -eq 0) { $o = @((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' nothing to do') }
Add-Content -LiteralPath $log -Value ($o -join "`r`n") -Encoding utf8