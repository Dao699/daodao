# 每周系统与软件更新巡检（由 Windows 计划任务调用）
$log = 'E:\Daodao\更新巡检日志.txt'
function L($m){ Add-Content -LiteralPath $log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) -Encoding UTF8 }
L "=== 开始巡检 ==="
try{
  $sess = New-Object -ComObject Microsoft.Update.Session
  $searcher = $sess.CreateUpdateSearcher()
  $res = $searcher.Search("IsInstalled=0 and IsHidden=0")
  L ("待安装更新: " + $res.Updates.Count + " 个")
  foreach($u in $res.Updates){ L ("  - " + $u.Title) }
  if ($res.Updates.Count -gt 0) {
    L "触发下载"
    & 'C:\Windows\System32\UsoClient.exe' StartDownload 2>&1 | Out-Null
    Start-Sleep -Seconds 20
    L "触发安装"
    & 'C:\Windows\System32\UsoClient.exe' StartInstall 2>&1 | Out-Null
    Start-Sleep -Seconds 20
    $k = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update'
    L ("InstallInProgress=" + (Get-ItemProperty -Path $k -Name 'InstallInProgress' -ErrorAction SilentlyContinue).InstallInProgress)
  } else {
    L "系统已是最新，无需操作"
  }
}catch{ L ("查询或安装失败: " + $_.Exception.Message) }
try{
  $m = Get-MpComputerStatus -ErrorAction Stop
  L ("Defender 病毒库: " + $m.AntivirusSignatureVersion + " 更新于 " + $m.AntivirusSignatureLastUpdated)
}catch{ L "读不到 Defender 状态" }
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (Test-Path -LiteralPath $edge) { L ("Edge 当前版本: " + (Get-Item -LiteralPath $edge).VersionInfo.FileVersion) }
L ("C 盘剩余: " + [math]::Round((Get-PSDrive C).Free/1GB,2) + " GB")
L "=== 巡检结束 ==="