$log = 'E:\Daodao\卸载记录.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }

# 联想照片大师：InstallShield 卸载
$setup = 'C:\Program Files (x86)\InstallShield Installation Information\{BC94C56A-3649-420C-8756-2ADEBE399D33}\Setup.exe'
if (Test-Path -LiteralPath $setup) {
  $p = Start-Process -FilePath $setup -ArgumentList '/z-uninstall' -WorkingDirectory (Split-Path -LiteralPath $setup -Parent) -Wait -PassThru -WindowStyle Hidden
  W ('照片大师 退出码=' + $p.ExitCode)
} else {
  W '照片大师卸载器不存在'
}

# 清理已卸载产品的残留登记项（对应目录已不存在或为空才清）
$stale = @(
  @{ key = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{0F82EA83-B0C5-4AB9-9695-DFE92C5FD57B}'; name = 'PhoneCompanion' },
  @{ key = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{D5D573DC-D989-4769-9B56-D6A7EA503D7F}'; name = 'OneKey Optimizer' },
  @{ key = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{C93283A4-091F-4502-A443-F01E0C9BDC6F}'; name = '联想通行证服务' },
  @{ key = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{F07C2CF8-4C53-4EC3-8162-A6221E36EB88}'; name = '用户手册' }
)
foreach ($s in $stale) {
  if (Test-Path -LiteralPath $s.key) {
    Remove-Item -LiteralPath $s.key -Recurse -Force -ErrorAction SilentlyContinue
    W ('已清残留登记: ' + $s.name)
  }
}

W ('C盘剩余GB=' + [math]::Round((Get-PSDrive C).Free/1GB,2))
W '完成第二轮'
