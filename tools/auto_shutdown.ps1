# 每晚定时关机（由 Windows 计划任务调用，不需要管理员）
# 判定规则：只有真正在装更新（InstallInProgress=1 或 TiWorker 在跑）才跳过，避免装到一半被打断
param([switch]$DryRun)
$log = 'E:\Daodao\关机日志.txt'
function L($m){ Add-Content -LiteralPath $log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) -Encoding UTF8 }
$reason = ''
$k = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update'
$install = (Get-ItemProperty -Path $k -Name 'InstallInProgress' -ErrorAction SilentlyContinue).InstallInProgress
if ($install -eq 1) { $reason = 'InstallInProgress=1' }
if (-not $reason -and (Get-Process -Name TiWorker -ErrorAction SilentlyContinue)) { $reason = 'TiWorker 在跑' }
if ($reason) {
  L ("检测到系统更新正在安装（" + $reason + "），今晚不关机，避免装到一半被打断")
  Write-Output ("SKIP: " + $reason)
  exit
}
if ($DryRun) {
  L "预演：条件满足，正式运行时会执行 shutdown /s /t 90"
  Write-Output "WOULD_SHUTDOWN"
  exit
}
L "没有更新在安装，执行关机（90 秒倒计时）"
& shutdown.exe /s /t 90 /c "定时关机：90 秒后自动关机，要取消请运行 shutdown /a"