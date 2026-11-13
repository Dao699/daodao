# 夺取所有权后彻底删除 OneKey Optimizer（PowerTaskbar 绿色电池图标）
$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\卸载记录.log'
function Log($m){ [IO.File]::AppendAllText($log, '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $m + "`r`n", (New-Object Text.UTF8Encoding($true))) }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $isAdmin){
  Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) -Verb RunAs
  exit
}

$dir = 'C:\Program Files\Lenovo\OneKey Optimizer'
Log '=== 夺权删除 OneKey Optimizer ==='

Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.Path -and $_.Path.StartsWith($dir) } | ForEach-Object { try{ Stop-Process -Id $_.Id -Force -ErrorAction Stop } catch {} }
Start-Sleep -Seconds 2

$take = & takeown.exe /f $dir /r /d y 2>&1
Log ('takeown 输出尾部: ' + (($take | Select-Object -Last 3) -join ' / '))
$acl = & icacls.exe $dir /grant '*S-1-5-32-544:(OI)(CI)F' /t /q 2>&1
Log ('icacls 输出尾部: ' + (($acl | Select-Object -Last 3) -join ' / '))

$files = Get-ChildItem -LiteralPath $dir -Recurse -File -Force -ErrorAction SilentlyContinue
foreach($f in $files){
  try{ Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop } catch { Log ('仍失败 ' + $f.Name + ' : ' + $_.Exception.Message) }
}
$dirs = Get-ChildItem -LiteralPath $dir -Recurse -Directory -Force -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
foreach($d in $dirs){ try{ Remove-Item -LiteralPath $d.FullName -Force -ErrorAction Stop } catch {} }
try{ Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction Stop } catch {}
Log ('OneKey Optimizer 还在=' + (Test-Path -LiteralPath $dir))

# OneDrive 存根也夺权删掉
$stub = 'C:\Windows\SysWOW64\OneDriveSetup.exe'
if(Test-Path -LiteralPath $stub){
  & takeown.exe /f $stub 2>&1 | Out-Null
  & icacls.exe $stub /grant '*S-1-5-32-544:F' 2>&1 | Out-Null
  try{ Remove-Item -LiteralPath $stub -Force -ErrorAction Stop; Log '已删除 OneDriveSetup.exe 存根' } catch { Log ('存根仍删不掉: ' + $_.Exception.Message) }
}

Start-Process 'explorer.exe'
Start-Sleep -Seconds 8

Add-Type @'
using System; using System.Runtime.InteropServices;
public class DPIG { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }
'@
[DPIG]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height
$g=[System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen(0,0,0,0,$b.Size); $g.Dispose()
$crop=New-Object System.Drawing.Bitmap $b.Width,60
$gc=[System.Drawing.Graphics]::FromImage($crop); $gc.DrawImage($bmp,(New-Object System.Drawing.Rectangle 0,0,$b.Width,60),(New-Object System.Drawing.Rectangle 0,($b.Height-60),$b.Width,60),[System.Drawing.GraphicsUnit]::Pixel); $gc.Dispose()
$crop.Save('E:\Daodao\_bar14.png',[System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose(); $crop.Dispose()
Log '已截图 _bar14.png'
Log '=== 夺权删除完成 ==='
