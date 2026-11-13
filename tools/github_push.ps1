# 每天把「道」的源码推到 GitHub。
# 这台机器 github.com 的 HTTPS 走不通（连接被重置），所以统一走 SSH-over-443（ssh.github.com:443）。
$ErrorActionPreference = 'Continue'
$repo = 'E:\Daodao'
$log  = Join-Path $repo 'github_sync.log'

function L($m) {
    $line = "[{0}] {1}" -f (Get-Date -f 'yyyy-MM-dd HH:mm:ss'), $m
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
    if (Test-Path -LiteralPath $log) {
        $all = @(Get-Content -LiteralPath $log -Encoding UTF8)
        if ($all.Count -gt 200) { [IO.File]::WriteAllLines($log, $all[($all.Count-200)..($all.Count-1)], (New-Object Text.UTF8Encoding($true))) }
    }
}

# git 与 ssh 的绝对路径（PATH 里没有）
$git = 'E:\Git\cmd\git.exe'
if (-not (Test-Path -LiteralPath $git)) {
    $c = @(Get-Command git.exe -ErrorAction SilentlyContinue)
    if ($c.Count -eq 0) { L '找不到 git，跳过'; exit 0 }
    $git = $c[0].Source
}
$ssh = 'E:\Git\usr\bin\ssh.exe'
if (Test-Path -LiteralPath $ssh) {
    $cfg = Join-Path $env:USERPROFILE '.ssh\config'
    $env:GIT_SSH_COMMAND = '"' + $ssh + '" -F "' + $cfg + '"'
} else {
    $env:GIT_SSH_COMMAND = 'ssh'
}

# 仓库地址：优先读 .github_remote，否则读 origin
$remoteFile = Join-Path $repo '.github_remote'
$remote = ''
if (Test-Path -LiteralPath $remoteFile) { $remote = (Get-Content -LiteralPath $remoteFile -Raw).Trim() }
if (-not $remote) { $remote = (& $git -C $repo config --get remote.origin.url 2>&1 | Out-String).Trim() }
if (-not $remote -or $remote -notmatch 'github') {
    L '还没配置 GitHub 仓库地址，本轮跳过'
    exit 0
}

# 确保 origin 指向这个地址
$curOrigin = (& $git -C $repo config --get remote.origin.url 2>&1 | Out-String).Trim()
if ($curOrigin -ne $remote) {
    if ($curOrigin) { & $git -C $repo remote set-url origin $remote 2>&1 | Out-Null }
    else { & $git -C $repo remote add origin $remote 2>&1 | Out-Null }
}

# 提交本地改动（没改动就只推，不造空提交）
& $git -C $repo add -A 2>&1 | Out-Null
$staged = (& $git -C $repo diff --cached --name-only 2>&1 | Out-String).Trim()
if ($staged) {
    $n = @($staged -split "`n" | Where-Object { $_.Trim() }).Count
    $msg = '自动备份 ' + (Get-Date -f 'yyyy-MM-dd HH:mm')
    & $git -C $repo commit -m $msg 2>&1 | Out-Null
    L ("已提交 $n 个文件")
}

# 推送
$branch = (& $git -C $repo rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
$r = (& $git -C $repo push origin ("HEAD:" + $branch) 2>&1 | Out-String)
if ($LASTEXITCODE -eq 0) {
    L ("推送成功 -> " + $remote + " (" + $branch + ")")
} else {
    L ("推送失败: " + ($r.Trim() -replace "`r`n", ' '))
}
exit 0