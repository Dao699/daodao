$Host.UI.RawUI.WindowTitle = '卸载联想照片大师'
$log = 'E:\Daodao\卸载记录.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }

$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
  Write-Host '正在申请管理员权限，请在弹窗里点“是”...'
  try {
    Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"') -Verb RunAs -ErrorAction Stop
  } catch {
    Write-Host '提权被取消，未做任何改动。'
  }
  Read-Host '按回车关闭'
  exit
}

W '--- 清理卡住的安装进程 ---'
foreach ($n in @('msiexec','uninstall','Setup')) {
  $ps = Get-Process $n -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID }
  if ($ps) {
    try { $ps | Stop-Process -Force -ErrorAction Stop; W ('已结束 ' + $n + ' 共' + @($ps).Count + '个') } catch { W ('结束 ' + $n + ' 失败: ' + $_.Exception.Message) }
  }
}
Start-Sleep -Seconds 4

$msi = 'C:\Program Files (x86)\InstallShield Installation Information\{BC94C56A-3649-420C-8756-2ADEBE399D33}\Lenovo Photo Master.msi'
W ('msi存在=' + (Test-Path -LiteralPath $msi))

if (Test-Path -LiteralPath $msi) {
  $p = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/x', ('"' + $msi + '"'), '/qn', '/norestart', '/l*v', 'E:\Daodao\pm_uninstall.log' -Wait -PassThru -WindowStyle Hidden
  W ('照片大师 官方卸载退出码=' + $p.ExitCode)
}

Start-Sleep -Seconds 5
$dir = 'C:\Program Files (x86)\Lenovo\Lenovo Photo Master'
if (Test-Path -LiteralPath $dir) {
  W '官方卸载后目录仍在，清理残留'
  try {
    Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction Stop
    W '已删除安装目录'
  } catch { W ('删目录失败: ' + $_.Exception.Message) }
}
if (-not (Test-Path -LiteralPath $dir)) {
  $k = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\InstallShield_{BC94C56A-3649-420C-8756-2ADEBE399D33}'
  if (Test-Path -LiteralPath $k) { Remove-Item -LiteralPath $k -Recurse -Force -ErrorAction SilentlyContinue; W '已清登记项' }
  $k2 = 'C:\Program Files (x86)\InstallShield Installation Information\{BC94C56A-3649-420C-8756-2ADEBE399D33}'
  if (Test-Path -LiteralPath $k2) { Remove-Item -LiteralPath $k2 -Recurse -Force -ErrorAction SilentlyContinue; W '已清 InstallShield 信息目录' }
}

$still = Test-Path -LiteralPath $dir
$free = [math]::Round((Get-PSDrive C).Free/1GB, 2)
W ('照片大师目录还在=' + $still + ' C盘剩余=' + $free + 'GB')
Write-Host ''
if ($still) {
  Write-Host '结果：还是没卸掉，请改到 设置 → 应用 里手动卸载。' -ForegroundColor Yellow
} else {
  Write-Host ('结果：已卸载干净，C 盘现在可用 ' + $free + 'GB。') -ForegroundColor Green
}
Read-Host '按回车关闭'
