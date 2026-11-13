$ErrorHandlingPreference = 'Stop'
$log = 'E:\Daodao\微信迁移.log'
function W($m){ $s = '[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m; Add-Content -LiteralPath $log -Value $s -Encoding utf8 }

$src = 'C:\Program Files\Tencent\Weixin'
$dst = 'E:\Tencent\Weixin'

W "开始，管理员身份=$(([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"

if (-not (Test-Path -LiteralPath $src)) { W '源目录不存在，退出'; exit 1 }
if (Test-Path -LiteralPath $dst) { W "目标已存在：$dst ，先删"; Remove-Item -LiteralPath $dst -Recurse -Force }

# 1. 停进程
Get-Process | Where-Object { $_.ProcessName -match 'Weixin|WeChat' } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 6
if (-not (Test-Path -LiteralPath 'E:\Tencent')) { New-Item -ItemType Directory -Path 'E:\Tencent' -Force | Out-Null }

# 2. 整体搬目录
$rc = robocopy $src $dst /E /MOVE /NFL /NDL /NJH /NJS /R:1 /W:1
W "robocopy 退出码=$LASTEXITCODE"
if ($LASTEXITCODE -ge 8) { W '搬目录失败，退出'; exit 2 }

# 3. 残留目录清掉，建目录联接
if (Test-Path -LiteralPath $src) { Remove-Item -LiteralPath $src -Recurse -Force -ErrorAction SilentlyContinue }
$j = cmd /c "mklink /J `"$src`" `"$dst`" 2>&1"
W "联接结果=$j"
if (-not (Test-Path -LiteralPath $src)) { W '联接没建成功，把目录搬回去'; robocopy $dst $src /E /MOVE /NFL /NDL /NJH /NJS | Out-Null; exit 3 }

# 4. 修正注册表卸载信息（路径虽经联接仍可用，但写实地改到新位置）
$keys = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Weixin',
          'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Weixin')
foreach ($k in $keys) {
  if (Test-Path $k) {
    Set-ItemProperty -LiteralPath $k -Name 'InstallLocation' -Value $dst -ErrorAction SilentlyContinue
    Set-ItemProperty -LiteralPath $k -Name 'UninstallString' -Value "`"$src\Uninstall.exe`"" -ErrorAction SilentlyContinue
    W "已更新注册表 $k"
  }
}

# 5. 启起来验证
Start-Process -FilePath "$src\Weixin.exe"
Start-Sleep -Seconds 12
$p = @(Get-Process | Where-Object { $_.ProcessName -match 'Weixin' })
W "启动后进程数=$($p.Count)"
W "C盘联接存在=$(Test-Path -LiteralPath $src)"
W "E盘实际目录大小=$([math]::Round(((Get-ChildItem -LiteralPath $dst -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB),1))MB"
W '完成'
