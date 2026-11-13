# 每天把代码打包成快照存本地（不依赖网盘和账号，断网也能跑）
$ErrorActionPreference = 'Continue'
$repo = 'E:\Daodao'
$outDir = 'E:\备份\代码快照'
$keep = 7
$u8 = New-Object Text.UTF8Encoding($false)

if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$git = 'E:\Git\cmd\git.exe'
if (-not (Test-Path -LiteralPath $git)) {
    $c = @(Get-Command git.exe -ErrorAction SilentlyContinue)
    if ($c.Count -eq 0) { exit 0 }
    $git = $c[0].Source
}

# 先把当天的改动提交进本地历史，再按提交内容打包（这样快照里带历史，能回滚）
& $git -C $repo add -A 2>&1 | Out-Null
$staged = (& $git -C $repo diff --cached --name-only 2>&1 | Out-String).Trim()
if ($staged) {
    & $git -C $repo commit -m ('自动快照 ' + (Get-Date -f 'yyyy-MM-dd HH:mm')) 2>&1 | Out-Null
}

$zip = Join-Path $outDir ('daodao_' + (Get-Date -f 'yyyyMMdd_HHmm') + '.zip')
& $git -C $repo archive --format=zip --output $zip HEAD 2>&1 | Out-Null

$log = Join-Path $repo 'github_sync.log'
$line = "[{0}] 本地快照 {1}" -f (Get-Date -f 'yyyy-MM-dd HH:mm:ss'), (Split-Path $zip -Leaf)
Add-Content -LiteralPath $log -Value $line -Encoding UTF8

# 只留最近 7 份，旧的删掉
Get-ChildItem -LiteralPath $outDir -Filter 'daodao_*.zip' -File | Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $keep | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
