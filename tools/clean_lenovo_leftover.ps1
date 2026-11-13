$log = 'E:\Daodao\卸载记录.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"') -Verb RunAs
  Read-Host '按回车关闭'
  exit
}
W '=== 停服务 + 删联想手机助手/一键优化 ==='

foreach ($s in @('PhoneCompanionPusher','LPSZ','Lenovo OKO Service','LenovoUpdate','PhoneCompanionVap')) {
  $o = Get-Service -Name $s -ErrorAction SilentlyContinue
  if ($o) {
    try {
      if ($o.Status -eq 'Running') { Stop-Service -Name $s -Force -ErrorAction Stop }
      Set-Service -Name $s -StartupType Disabled -ErrorAction Stop
      W ('已停用服务: ' + $s)
    } catch { W ('服务处理失败: ' + $s + ' ' + $_.Exception.Message) }
  }
}

foreach ($n in @('Phone Companion','PhoneCompanionPusher','OneKeyOptimizer','OneKeyOptimizerTray','OnekeyOptimizerUpdata','LPSmc','LPSZ')) {
  Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
    try { Stop-Process -Id $_.Id -Force -ErrorAction Stop } catch {}
  }
}
Start-Sleep -Seconds 5

foreach ($d in @('C:\Program Files\Lenovo PhoneCompanion','C:\Program Files\Lenovo\OneKey Optimizer')) {
  if (Test-Path -LiteralPath $d) {
    try { Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction Stop; W ('已删目录: ' + $d) }
    catch { W ('目录仍占用: ' + $d) }
  }
}

foreach ($root in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')) {
  if (Test-Path $root) {
    Get-ChildItem $root -ErrorAction SilentlyContinue | ForEach-Object {
      $d = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
      if ($d.DisplayName -match 'PhoneCompanion|OneKey Optimizer') {
        Remove-Item -LiteralPath $_.PSPath -Recurse -Force -ErrorAction SilentlyContinue
        W ('已清登记: ' + $d.DisplayName)
      }
    }
  }
}

$left = (Test-Path -LiteralPath 'C:\Program Files\Lenovo PhoneCompanion') -or (Test-Path -LiteralPath 'C:\Program Files\Lenovo\OneKey Optimizer')
$free = [math]::Round((Get-PSDrive C).Free/1GB,2)
W ('残留还在=' + $left + ' C盘剩余=' + $free + 'GB')
W '=== 完成 ==='
Write-Host ('完成。C 盘可用 ' + $free + 'GB。')
if ($left) { Write-Host '仍有文件被占用，重启后再删一次即可。' -ForegroundColor Yellow }
Read-Host '按回车关闭'
