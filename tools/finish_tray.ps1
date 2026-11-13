# 任务栏收尾：去掉多余电源图标 + 清掉联想两个残留目录 + 删 OneDrive 存根
$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\卸载记录.log'

function Log($msg){
  $line = '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $msg
  [IO.File]::AppendAllText($log, $line + "`r`n", (New-Object Text.UTF8Encoding($true)))
}

# 自我提权
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $isAdmin){
  Log '=== 任务栏收尾：请求提权 ==='
  Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) -Verb RunAs
  exit
}

Log '=== 任务栏收尾开始（管理员）==='

# 1. 停用并禁用 LenovoPAWDService（绿色 100% 电池图标的宿主）
foreach($svc in @('LenovoPAWDService','Lenovo System Agent Service','Lenovo OKO Service','LenovoUpdate')){
  try{
    $s = Get-Service -Name $svc -ErrorAction Stop
    if($s.Status -ne 'Stopped'){ Stop-Service -Name $svc -Force -ErrorAction Stop; Log ('已停止服务 ' + $svc) }
    Set-Service -Name $svc -StartupType Disabled -ErrorAction Stop
    Log ('已禁用服务 ' + $svc)
  } catch { Log ('服务处理失败 ' + $svc + ' : ' + $_.Exception.Message) }
}

# 2. 结束残留进程
foreach($n in @('LPAWDService','SystemAgentService','OneKeyOptimizerTray','OneKeyOptimizer','onekeyoptimizer')){
  Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
    try{ Stop-Process -Id $_.Id -Force -ErrorAction Stop; Log ('已结束进程 ' + $n + '#' + $_.Id) } catch { Log ('进程结束失败 ' + $n + '#' + $_.Id) }
  }
}
Start-Sleep -Seconds 2

# 3. 删联想两个残留目录
foreach($dir in @('C:\Program Files\Lenovo PhoneCompanion','C:\Program Files\Lenovo\OneKey Optimizer')){
  if(Test-Path -LiteralPath $dir){
    try{
      Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction Stop
      Log ('已删除目录 ' + $dir)
    } catch {
      Log ('目录删除失败 ' + $dir + ' : ' + $_.Exception.Message)
      Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        try{ Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop } catch {}
      }
      Log ('复查是否还在 ' + $dir + ' = ' + (Test-Path -LiteralPath $dir))
    }
  } else { Log ('目录已不存在 ' + $dir) }
}

# 4. 删 OneDrive 卸载存根
$stub = 'C:\Windows\SysWOW64\OneDriveSetup.exe'
if(Test-Path -LiteralPath $stub){
  try{ Remove-Item -LiteralPath $stub -Force -ErrorAction Stop; Log '已删除 OneDriveSetup.exe 存根' } catch { Log ('存根删除失败 : ' + $_.Exception.Message) }
}

# 5. 重启资源管理器让任务栏图标刷新
try{
  Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 3
  Log '已重启资源管理器'
} catch {}

Log '=== 任务栏收尾完成 ==='
Write-Host ''
Write-Host '处理完成，看看任务栏右侧是不是只剩一个电池图标了。按回车关闭本窗口。'
Read-Host | Out-Null
