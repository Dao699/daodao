$log = 'E:\Daodao\卸载记录.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }

$Host.UI.RawUI.WindowTitle = '电脑收尾：开机项 + 清残留'
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Host '正在申请管理员权限，请在弹窗里点“是”...'
  Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"') -Verb RunAs
  Read-Host '按回车关闭'
  exit
}
W '========== 收尾四件事 =========='
Write-Host '1/4 关闭多余的系统级开机项...'

# ---- 1. 系统级开机启动项：前置 OFF_ 停用（原值保留，可逆）
$runKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
$runKey32 = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'
$off = @(
  @{ key = $runKey;   name = 'IAStorIcon' },
  @{ key = $runKey;   name = 'RtsFT' },
  @{ key = $runKey;   name = 'LENOVO.TPKNRRES' },
  @{ key = $runKey;   name = 'PhoneCompanion' },
  @{ key = $runKey;   name = 'OneKeyOptimizer' },
  @{ key = $runKey32; name = 'LPS' },
  @{ key = $runKey32; name = 'LPSmcL' }
)
foreach ($i in $off) {
  $p = Get-ItemProperty -LiteralPath $i.key -ErrorAction SilentlyContinue
  if ($p -and $p.PSObject.Properties.Name -contains $i.name) {
    $val = $p.($i.name)
    New-ItemProperty -LiteralPath $i.key -Name ('OFF_' + $i.name) -Value $val -PropertyType String -Force | Out-Null
    Remove-ItemProperty -LiteralPath $i.key -Name $i.name -Force -ErrorAction SilentlyContinue
    W ('已停用开机项: ' + $i.name)
  }
}

# ---- 2. 公共桌面清理（快捷方式移到备份目录，不硬删）
$bak = 'E:\Daodao\备份\桌面快捷方式备份_20261112'
if (-not (Test-Path -LiteralPath $bak)) { New-Item -ItemType Directory -Path $bak -Force | Out-Null }
$pub = 'C:\Users\Public\Desktop'
$moveList = @('Microsoft Edge.lnk','Lenovo Photo Master.lnk','Microsoft Office 2013 Activation.lnk','联想通行证服务.lnk','OneKey Optimizer.Lnk')
foreach ($n in $moveList) {
  $src = Join-Path $pub $n
  if (Test-Path -LiteralPath $src) {
    Move-Item -LiteralPath $src -Destination $bak -Force -ErrorAction SilentlyContinue
    W ('公共桌面移走: ' + $n)
  }
}

# ---- 3. 已卸载产品的实际安装目录（Program Files 下）
foreach ($d in @('C:\Program Files\Lenovo PhoneCompanion','C:\Program Files\Lenovo\OneKey Optimizer')) {
  if (Test-Path -LiteralPath $d) {
    try { Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction Stop; W ('已删目录: ' + $d) } catch { W ('删不动: ' + $d) }
  }
}

# ---- 4. 照片大师：用完整 msi 路径
foreach ($n in @('msiexec','uninstall')) {
  Get-Process $n -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID } | Stop-Process -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3
$msi = 'C:\Program Files (x86)\InstallShield Installation Information\{BC94C56A-3649-420C-8756-2ADEBE399D33}\Lenovo Photo Master.msi'
if (Test-Path -LiteralPath $msi) {
  $proc = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/x', ('"' + $msi + '"'), '/qn', '/norestart' -Wait -PassThru -WindowStyle Hidden
  W ('照片大师 卸载退出码=' + $proc.ExitCode)
} else { W '照片大师 msi 不存在' }
Start-Sleep -Seconds 4
$pmDir = 'C:\Program Files (x86)\Lenovo\Lenovo Photo Master'
if (Test-Path -LiteralPath $pmDir) {
  try { Remove-Item -LiteralPath $pmDir -Recurse -Force -ErrorAction Stop; W '照片大师目录已删' } catch { W ('照片大师目录删不动: ' + $_.Exception.Message) }
}
if (-not (Test-Path -LiteralPath $pmDir)) {
  $k = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\InstallShield_{BC94C56A-3649-420C-8756-2ADEBE399D33}'
  if (Test-Path -LiteralPath $k) { Remove-Item -LiteralPath $k -Recurse -Force -ErrorAction SilentlyContinue; W '照片大师登记项已清' }
  $k2 = 'C:\Program Files (x86)\InstallShield Installation Information\{BC94C56A-3649-420C-8756-2ADEBE399D33}'
  if (Test-Path -LiteralPath $k2) { Remove-Item -LiteralPath $k2 -Recurse -Force -ErrorAction SilentlyContinue }
}

W ('照片大师还在=' + (Test-Path -LiteralPath $pmDir))
$free = [math]::Round((Get-PSDrive C).Free/1GB,2)
W ('C盘剩余GB=' + $free)
W '========== 收尾完成 =========='
Write-Host ''
Write-Host ('已完成。C 盘现在可用 ' + $free + 'GB。') -ForegroundColor Green
if (Test-Path -LiteralPath $pmDir) { Write-Host '照片大师仍未卸掉，建议在 设置 → 应用 里手动卸载。' -ForegroundColor Yellow }
Read-Host '按回车关闭'
