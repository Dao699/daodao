# 趁 explorer 未启动时直接删掉 PowerTaskbar.dll，彻底去掉绿色电池图标
$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\卸载记录.log'
function Log($m){ [IO.File]::AppendAllText($log, '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $m + "`r`n", (New-Object Text.UTF8Encoding($true))) }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $isAdmin){
  Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) -Verb RunAs
  exit
}
Log '=== 强删 PowerTaskbar.dll 开始 ==='

$dir = 'C:\Program Files\Lenovo\OneKey Optimizer'

# 1. 结束 explorer 和该目录下的所有进程
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.Path -and $_.Path.StartsWith($dir) } | ForEach-Object {
  try{ Stop-Process -Id $_.Id -Force -ErrorAction Stop; Log ('已结束 ' + $_.ProcessName) } catch {}
}
Start-Sleep -Seconds 2

# 2. 删文件（explorer 已不在，DLL 应已释放）
$files = Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue
foreach($f in $files){
  try{ Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop } catch { Log ('删除失败 ' + $f.Name + ' : ' + $_.Exception.Message) }
}
$dirs = Get-ChildItem -LiteralPath $dir -Recurse -Directory -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
foreach($d in $dirs){ try{ Remove-Item -LiteralPath $d.FullName -Force -ErrorAction Stop } catch {} }
try{ Remove-Item -LiteralPath $dir -Force -ErrorAction Stop } catch {}
Log ('OneKey Optimizer 还在=' + (Test-Path -LiteralPath $dir))

# 3. 重新启动 explorer
Start-Process 'explorer.exe'
Start-Sleep -Seconds 8

# 4. 截图核对任务栏
Add-Type @'
using System; using System.Runtime.InteropServices;
public class DPIF { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }
'@
[DPIF]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height
$g=[System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen(0,0,0,0,$b.Size); $g.Dispose()
$crop=New-Object System.Drawing.Bitmap $b.Width,60
$gc=[System.Drawing.Graphics]::FromImage($crop); $gc.DrawImage($bmp,(New-Object System.Drawing.Rectangle 0,0,$b.Width,60),(New-Object System.Drawing.Rectangle 0,($b.Height-60),$b.Width,60),[System.Drawing.GraphicsUnit]::Pixel); $gc.Dispose()
$crop.Save('E:\Daodao\_bar13.png',[System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose(); $crop.Dispose()
Log '已截图 _bar13.png'
Log '=== 强删完成 ==='
