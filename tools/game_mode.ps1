<#
  游戏模式：一键清后台
  用法：双击桌面「游戏模式-清后台.lnk」，或手动执行
        powershell -NoProfile -ExecutionPolicy Bypass -File E:\Daodao\tools\game_mode.ps1
  参数：-DryRun        只报告不真杀
        -KeepDoubao    保留豆包客户端（默认会被关掉）
        -KeepSearch    保留 Windows 搜索索引服务（默认暂停）
#>
param(
  [switch]$DryRun,
  [switch]$KeepDoubao,
  [switch]$KeepSearch
)

$ErrorActionPreference = 'SilentlyContinue'
$logDir = 'E:\Daodao\tools'
$log = Join-Path $logDir 'game_mode.log'

function Get-FreeGB { [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2) }
function Log($msg) {
  $line = ('[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg)
  Write-Host $line
  Add-Content -LiteralPath $log -Value $line -Encoding UTF8
}

# 保护：系统进程永不结束
$protected = @('system','idle','csrss','wininit','winlogon','services','lsass','svchost','smss','dwm','explorer','ctfmon','audiodg','sihost','taskhostw','runtimebroker','搜索','textinputhost','shellexperiencehost','startmenuexperiencehost','searchhost','python','pythonw','Dao','道','MsMpEng','SecurityHealthService','MumuPlayer','MuMuVMMHeadless','NemuHeadless')

# 要清的后台进程（按名称匹配，不区分大小写）
$targets = @(
  @{ n = 'msedge';        d = 'Edge 浏览器' },
  @{ n = 'Weixin';        d = '微信' },
  @{ n = 'WeChat';        d = '微信' },
  @{ n = 'WeChatApp';     d = '微信组件' },
  @{ n = 'QQBrowser';     d = 'QQ 浏览器' },
  @{ n = 'QQPCTray';      d = 'QQ 电脑管家托盘' },
  @{ n = '360se';         d = '360 浏览器' },
  @{ n = '360Chrome';     d = '360 极速浏览器' },
  @{ n = '360safe';       d = '360 安全卫士' },
  @{ n = 'steamwebhelper';d = 'Steam 网页组件' },
  @{ n = 'OneDrive';      d = 'OneDrive' },
  @{ n = 'Teams';         d = 'Teams' },
  @{ n = 'nwmonitor';     d = '网易云监控组件' },
  @{ n = 'wpscloudsvr';   d = 'WPS 云服务' },
  @{ n = 'wpscenter';     d = 'WPS 中心' },
  @{ n = 'SearchApp';     d = '搜索界面' }
)
if (-not $KeepDoubao) { $targets += @{ n = 'Doubao'; d = '豆包客户端（会结束本次对话，玩完重开即可）' } }

Log '==== 游戏模式开始 ===='
$before = Get-FreeGB
Log "清理前可用内存：$before GB"
if ($DryRun) { Log '（演练模式：只报告，不真结束进程）' }

$killed = 0
$freed = 0
foreach ($t in $targets) {
  if ($t.n.ToLower() -in $protected) { continue }
  $procs = Get-Process -Name $t.n -ErrorAction SilentlyContinue
  if (-not $procs) { continue }
  $wset = ($procs | Measure-Object WorkingSet64 -Sum).Sum
  Log ("命中 {0}（{1}）：{2} 个进程，约占 {3} MB" -f $t.n, $t.d, $procs.Count, [math]::Round($wset / 1MB, 0))
  if (-not $DryRun) {
    foreach ($p in $procs) { try { Stop-Process -Id $p.Id -Force -ErrorAction Stop } catch { Log ("结束 {0} (PID {1}) 失败：{2}" -f $p.ProcessName, $p.Id, $_.Exception.Message) } }
  }
  $killed += $procs.Count
  $freed += $wset
}

# 暂停 Windows 搜索索引（大量磁盘 IO 来源，玩完可自行恢复或重启后自动恢复）
if (-not $KeepSearch) {
  $w = Get-Service -Name 'WSearch' -ErrorAction SilentlyContinue
  if ($w -and $w.Status -eq 'Running') {
    if (-not $DryRun) { try { Stop-Service -Name 'WSearch' -Force -ErrorAction Stop } catch { Log '暂停 WSearch 失败（可能需要管理员权限，不影响游戏）' } }
    Log 'Windows 搜索索引（WSearch）已尝试暂停'
  }
}

# 电源计划保持高性能
$active = (powercfg /getactivescheme) -join ''
if ($active -notmatch '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c') {
  if (-not $DryRun) { powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>$null }
  Log '电源计划已切到「高性能」'
} else {
  Log '电源计划已是「高性能」，无需调整'
}

Start-Sleep -Milliseconds 600
$after = Get-FreeGB
if ($DryRun) {
  Log ("预计可结束 {0} 个进程、释放约 {1} MB；当前可用内存 {2} GB" -f $killed, [math]::Round($freed / 1MB, 0), $after)
} else {
  Log ("结束进程 {0} 个，释放约 {1} MB；当前可用内存 {2} GB" -f $killed, [math]::Round($freed / 1MB, 0), $after)
}
Log '==== 游戏模式结束 ===='

if (-not $DryRun) {
  Write-Host ''
  Write-Host ('后台已清理。可用内存 {0} GB -> {1} GB。' -f $before, $after) -ForegroundColor Green
  Write-Host '玩完想恢复：豆包/微信/浏览器直接双击图标重开即可；搜索索引重启电脑后自动恢复。' -ForegroundColor Gray
  Start-Sleep -Seconds 2
}
