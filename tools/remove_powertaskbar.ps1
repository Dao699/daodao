# 去掉任务栏上多余的绿色电池图标（OneKey Optimizer 的 PowerTaskbar 插件）并清残留
$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\卸载记录.log'
function Log($m){ [IO.File]::AppendAllText($log, '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $m + "`r`n", (New-Object Text.UTF8Encoding($true))) }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $isAdmin){
  Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) -Verb RunAs
  exit
}
Log '=== 卸载 PowerTaskbar 电池插件开始（管理员）==='

$bin = 'C:\Program Files\Lenovo\OneKey Optimizer\bin'
$dll = Join-Path $bin 'PowerTaskbar.dll'

# 1. 先结束 explorer，释放被占用的 DLL
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Log '已结束 explorer（DLL 已释放）'

# 2. 反注册 DeskBand
if(Test-Path -LiteralPath $dll){
  $r = Start-Process -FilePath "$env:WINDIR\System32\regsvr32.exe" -ArgumentList @('/u','/s','"' + $dll + '"') -Wait -PassThru -WindowStyle Hidden
  Log ('regsvr32 /u PowerTaskbar.dll 退出码=' + $r.ExitCode)
} else { Log ('PowerTaskbar.dll 不存在: ' + $dll) }

# 3. 备份整个 OneKey Optimizer 目录到 E 盘，再删
$src = 'C:\Program Files\Lenovo\OneKey Optimizer'
$bak = 'E:\Daodao\备份\OneKeyOptimizer_备份_20261112'
if(Test-Path -LiteralPath $src){
  if(-not (Test-Path -LiteralPath $bak)){
    New-Item -ItemType Directory -Path $bak -Force | Out-Null
    Copy-Item -LiteralPath $src -Destination $bak -Recurse -Force -ErrorAction SilentlyContinue
    Log ('已备份到 ' + $bak + '，大小MB=' + [math]::Round(((Get-ChildItem -LiteralPath $bak -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum)/1MB,1))
  }
  try{
    Remove-Item -LiteralPath $src -Recurse -Force -ErrorAction Stop
    Log '已删除 OneKey Optimizer 目录'
  } catch {
    Log ('整目录删除失败: ' + $_.Exception.Message + ' → 逐个删')
    Get-ChildItem -LiteralPath $src -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
      try{ Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop } catch {}
    }
    Get-ChildItem -LiteralPath $src -Recurse -Directory -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object {
      try{ Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop } catch {}
    }
    try{ Remove-Item -LiteralPath $src -Force -ErrorAction Stop } catch {}
    Log ('复查 OneKey Optimizer 还在=' + (Test-Path -LiteralPath $src))
  }
} else { Log 'OneKey Optimizer 目录已不存在' }

# 4. PhoneCompanion 目录再试一次
$pc = 'C:\Program Files\Lenovo PhoneCompanion'
if(Test-Path -LiteralPath $pc){
  Get-Process | Where-Object { $_.Path -and $_.Path.StartsWith($pc) } | ForEach-Object { try{ Stop-Process -Id $_.Id -Force -ErrorAction Stop } catch {} }
  try{
    Remove-Item -LiteralPath $pc -Recurse -Force -ErrorAction Stop
    Log '已删除 PhoneCompanion 目录'
  } catch {
    Log ('PhoneCompanion 删除失败: ' + $_.Exception.Message)
    Get-ChildItem -LiteralPath $pc -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { try{ Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop } catch {} }
    Get-ChildItem -LiteralPath $pc -Recurse -Directory -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object { try{ Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop } catch {} }
    try{ Remove-Item -LiteralPath $pc -Force -ErrorAction Stop } catch {}
    Log ('复查 PhoneCompanion 还在=' + (Test-Path -LiteralPath $pc))
  }
}

# 5. OneDrive 存根
$stub = 'C:\Windows\SysWOW64\OneDriveSetup.exe'
if(Test-Path -LiteralPath $stub){
  try{ Remove-Item -LiteralPath $stub -Force -ErrorAction Stop; Log '已删除 OneDriveSetup.exe 存根' } catch { Log ('存根删除失败: ' + $_.Exception.Message) }
}

# 6. 重新拉起 explorer
if(-not (Get-Process explorer -ErrorAction SilentlyContinue)){ Start-Process 'explorer.exe' }
Start-Sleep -Seconds 6
Log '=== 卸载 PowerTaskbar 完成 ==='
