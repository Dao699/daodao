# 逐个停掉联想托盘候选，测出绿色电池图标到底来自谁
$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\卸载记录.log'
function Log($m){ [IO.File]::AppendAllText($log, '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $m + "`r`n", (New-Object Text.UTF8Encoding($true))) }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $isAdmin){
  Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) -Verb RunAs
  exit
}

Add-Type @'
using System; using System.Runtime.InteropServices;
public class DPIA { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }
'@
[DPIA]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

function Shot($name){
  $b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height
  $g=[System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen(0,0,0,0,$b.Size); $g.Dispose()
  $crop=New-Object System.Drawing.Bitmap $b.Width,60
  $gc=[System.Drawing.Graphics]::FromImage($crop); $gc.DrawImage($bmp,(New-Object System.Drawing.Rectangle 0,0,$b.Width,60),(New-Object System.Drawing.Rectangle 0,($b.Height-60),$b.Width,60),[System.Drawing.GraphicsUnit]::Pixel); $gc.Dispose()
  $crop.Save($name,[System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose(); $crop.Dispose()
}

# 1. 停 Lenovo Settings Service + SettingsService 进程
try{ Stop-Service -Name 'Lenovo Settings Service' -Force -ErrorAction Stop; Log '已停 Lenovo Settings Service' }catch{ Log ('停 Settings Service 失败: ' + $_.Exception.Message) }
Get-Process SettingsService,LenovoSetSvr -ErrorAction SilentlyContinue | ForEach-Object { try{ Stop-Process -Id $_.Id -Force -ErrorAction Stop; Log ('已结束 ' + $_.ProcessName) }catch{} }
Start-Sleep -Seconds 5
Shot 'E:\Daodao\_t1.png'
Log '已截图 _t1.png（停 Settings Service 后）'

# 2. 停 TpKnrres
Get-Process TpKnrres -ErrorAction SilentlyContinue | ForEach-Object { try{ Stop-Process -Id $_.Id -Force -ErrorAction Stop; Log '已结束 TpKnrres' }catch{} }
Start-Sleep -Seconds 4
Shot 'E:\Daodao\_t2.png'
Log '已截图 _t2.png（再停 TpKnrres 后）'

Log '=== 图标来源测试结束 ==='
Start-Sleep -Seconds 2
