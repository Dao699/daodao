# 极短窗口内删掉 OneKey Optimizer 文件（ACL 已放开，只卡进程占用）
$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\卸载记录.log'
function Log($m){ [IO.File]::AppendAllText($log, '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $m + "`r`n", (New-Object Text.UTF8Encoding($true))) }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $isAdmin){
  Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) -Verb RunAs
  exit
}

$dir = 'C:\Program Files\Lenovo\OneKey Optimizer'
Log '=== 快速窗口删除 OneKey Optimizer ==='

# 1) 先在同一个 cmd 里杀 explorer 并立刻删，减少 explorer 自动重启的抢锁窗口
$cmd = 'taskkill /f /im explorer.exe & ' +
       'ping -n 1 -w 300 127.0.0.1 > nul & ' +
       'del /f /q "' + $dir + '\bin\*.dll" & ' +
       'del /f /q "' + $dir + '\bin\*.exe" & ' +
       'rd /s /q "' + $dir + '"'
$r = Start-Process -FilePath "$env:WINDIR\System32\cmd.exe" -ArgumentList @('/c',$cmd) -Wait -PassThru -WindowStyle Hidden
Log ('cmd 删除退出码=' + $r.ExitCode + ' 目录还在=' + (Test-Path -LiteralPath $dir))

# 2) 还删不掉的部分登记到重启后删除
if(Test-Path -LiteralPath $dir){
  $pending = @()
  Get-ChildItem -LiteralPath $dir -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $pending += ('\??\' + $_.FullName)
    $pending += ''
  }
  if($pending.Count -gt 0){
    New-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' -Name 'PendingFileRenameOperations' -Value ([string[]]$pending) -PropertyType MultiString -Force | Out-Null
    Log ('已登记重启后删除文件数=' + ($pending.Count/2))
  }
}

# 3) 启动 explorer
if(-not (Get-Process explorer -ErrorAction SilentlyContinue)){ Start-Process 'explorer.exe' }
Start-Sleep -Seconds 8
Log '=== 快速窗口删除完成 ==='
