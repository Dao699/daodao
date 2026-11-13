# 每天把下载页的版本号、体积、日期对齐本机真实安装包，然后发布
$ErrorActionPreference = 'Continue'
$src = 'E:\Daodao\引导页_src'
$page = Join-Path $src 'index.html'
$repo = 'E:\Daodao'
$appId = 'app_17hnj8acgs2'
$log = Join-Path $repo 'github_sync.log'

function L($m) {
    $line = "[{0}] {1}" -f (Get-Date -f 'yyyy-MM-dd HH:mm:ss'), $m
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
    $all = @(Get-Content -LiteralPath $log -Encoding UTF8)
    if ($all.Count -gt 200) { [IO.File]::WriteAllLines($log, $all[($all.Count-200)..($all.Count-1)], (New-Object Text.UTF8Encoding($true))) }
}

if (-not (Test-Path -LiteralPath $page)) { L '下载页源码不在本机，本轮跳过网页更新'; exit 0 }

# 当前真实版本号：从源码取，取不到就用页面现有的
$ver = $null
$cs = Join-Path $repo 'src\桌面分身\pet.cs'
if (Test-Path -LiteralPath $cs) {
    $m = [regex]::Match([IO.File]::ReadAllText($cs, [Text.Encoding]::UTF8), 'APP_VER\s*=\s*(\d+)')
    if ($m.Success) { $ver = $m.Groups[1].Value }
}
$raw = [IO.File]::ReadAllText($page, [Text.Encoding]::UTF8)
if (-not $ver) { $ver = [regex]::Match($raw, 'data-ver="(\d+)"').Groups[1].Value }

$exe = Get-Item -LiteralPath (Join-Path $repo '道.exe') -ErrorAction SilentlyContinue
$apk = Get-Item -LiteralPath (Join-Path $repo '道.apk') -ErrorAction SilentlyContinue
$exeMB = if ($exe) { [math]::Round($exe.Length / 1MB, 1) } else { $null }
$apkMB = if ($apk) { [math]::Round($apk.Length / 1MB, 1) } else { $null }
$today = Get-Date -f 'yyyy-MM-dd'

$before = $raw
$raw = $raw -replace '<span class="vbadge">v\d+</span>', ('<span class="vbadge">v' + $ver + '</span>')
$raw = $raw -replace 'data-ver="\d+"', ('data-ver="' + $ver + '"')
if ($exeMB) { $raw = $raw -replace '电脑 \d+\.\d+ MB', ('电脑 ' + $exeMB + ' MB') }
if ($apkMB) { $raw = $raw -replace '手机 \d+\.\d+ MB', ('手机 ' + $apkMB + ' MB') }
$raw = $raw -replace '版本 \d+ ·', ('版本 ' + $ver + ' ·')
# 日期：只改形如 2026-11-11 的日期串，页面里只有元信息行和页脚两处
$raw = [regex]::Replace($raw, '\d{4}-\d{2}-\d{2}', $today)

if ($raw -eq $before) {
    L ('下载页内容已经是最新的（v' + $ver + ' / 电脑 ' + $exeMB + 'MB / 手机 ' + $apkMB + 'MB / ' + $today + '）')
} else {
    Copy-Item -LiteralPath $page -Destination (Join-Path $src ('index.v' + $ver + '.bak')) -Force
    [IO.File]::WriteAllText($page, $raw, (New-Object Text.UTF8Encoding($false)))
    L ('下载页已对齐：v' + $ver + ' / 电脑 ' + $exeMB + 'MB / 手机 ' + $apkMB + 'MB / ' + $today)
}

# 发布（cwd 与 lark-cli 必须同一条命令，路径用相对）
Push-Location $src
$out = & lark-cli apps +deploy --file-path ./index.html --app-id $appId 2>&1 | Out-String
Pop-Location
$json = $null
$st = $out.IndexOf('{')
if ($st -ge 0) { try { $json = $out.Substring($st) | ConvertFrom-Json } catch { } }
if (-not $json) { L ('网页发布返回看不懂: ' + ($out -replace "`r?`n", ' ').Substring(0, [Math]::Min(160, $out.Length))); exit 1 }

if ($json.ok -ne $true) {
    $err = ($json.error | ConvertTo-Json -Depth 4 -Compress)
    L ('网页发布失败: ' + $err)
    exit 1
}

$url = $json.data.online_url
$rid = $json.data.release_id
if (-not $url -and $rid) {
    for ($i = 0; $i -lt 12; $i++) {
        Start-Sleep -Seconds 10
        $r = & lark-cli apps +release-get --app-id $appId --release-id $rid 2>&1 | Out-String
        $st2 = $r.IndexOf('{')
        if ($st2 -lt 0) { continue }
        try { $rj = $r.Substring($st2) | ConvertFrom-Json } catch { continue }
        if ($rj.data.status -eq 'finished') { $url = $rj.data.online_url; break }
    }
}
if ($url) { L ('网页已发布 -> ' + $url) } else { L ('网页发布受理了，但没等到完成（release ' + $rid + '）') }
exit 0
