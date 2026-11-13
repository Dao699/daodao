# 一次性配置 GitHub：建仓库 + 写凭据 + 首推。用法：
#   powershell -File setup_github.ps1 -User <GitHub用户名> -Token <ghp_xxx> [-Repo daodao] [-Private]
# 令牌只要 classic token 且勾了 repo 权限即可。
param(
    [Parameter(Mandatory = $true)][string]$User,
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$Repo = 'daodao',
    [switch]$Private
)

$ErrorActionPreference = 'Stop'
$root = 'E:\Daodao'
$git = 'E:\Git\cmd\git.exe'
if (-not (Test-Path -LiteralPath $git)) { $git = (Get-Command git.exe).Source }
$log = Join-Path $root 'github_sync.log'

function L($m) {
    $line = "[{0}] {1}" -f (Get-Date -f 'yyyy-MM-dd HH:mm:ss'), $m
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
    Write-Host $line
}

# 1) 用令牌建仓库（已存在就跳过）
$headers = @{ Authorization = "token $Token"; Accept = 'application/vnd.github+json'; 'User-Agent' = 'dao-pet' }
$body = @{ name = $Repo; private = [bool]$Private; description = '桌面宠物「道」源码每日快照' } | ConvertTo-Json
try {
    $r = Invoke-RestMethod -Uri 'https://api.github.com/user/repos' -Method Post -Headers $headers -Body $body -ContentType 'application/json'
    L ("仓库已创建: " + $r.full_name)
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -eq 422) { L '仓库已存在，继续' } else { L ("建仓库失败: " + $_.Exception.Message); exit 1 }
}

# 2) 落凭据与远端（凭据文件已在 .gitignore 里，不会进库）
$remoteUrl = "https://github.com/$User/$Repo.git"
[IO.File]::WriteAllText((Join-Path $root '.github_token'), $Token, (New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $root '.github_remote'), $remoteUrl, (New-Object Text.UTF8Encoding($false)))
Push-Location $root
& $git remote remove origin 2>&1 | Out-Null
& $git remote add origin $remoteUrl 2>&1 | Out-Null
& $git -c user.name=$User -c user.email="$User@users.noreply.github.com" config user.name $User
& $git config user.email "$User@users.noreply.github.com"

# 3) 首推
$pushUrl = "https://x-access-token:$Token@github.com/$User/$Repo.git"
$r2 = & $git push $pushUrl "HEAD:main" 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) { L ("首推成功 -> " + $remoteUrl) } else { L ("首推失败: " + ($r2 -replace $Token, '***')) }
Pop-Location
