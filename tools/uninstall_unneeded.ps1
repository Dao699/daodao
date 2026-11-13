$log = 'E:\Daodao\卸载记录.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }
W ('开始，管理员=' + (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)))

$jobs = @(
  @{ n = 'Copilot'; cmd = '"C:\Program Files (x86)\Microsoft\Copilot\Application\157.0.4341.46\Installer\copilot_setup.exe" --uninstall --mscopilot --channel=stable --system-level --verbose-logging' },
  @{ n = '友约'; cmd = '"C:\Program Files (x86)\Youyue\uninstall.exe" /S' },
  @{ n = 'Lenovo SHAREit'; cmd = '"C:\Program Files (x86)\Lenovo\SHAREit\unins000.exe" /SILENT /NORESTART' },
  @{ n = '用户手册'; cmd = 'MsiExec.exe /X{F07C2CF8-4C53-4EC3-8162-A6221E36EB88} /qn /norestart' },
  @{ n = 'PhoneCompanion'; cmd = 'MsiExec.exe /X{0F82EA83-B0C5-4AB9-9695-DFE92C5FD57B} /qn /norestart' },
  @{ n = 'OneKey Optimizer'; cmd = 'MsiExec.exe /X{D5D573DC-D989-4769-9B56-D6A7EA503D7F} /qn /norestart' },
  @{ n = '联想通行证服务'; cmd = 'MsiExec.exe /X{C93283A4-091F-4502-A443-F01E0C9BDC6F} /qn /norestart' }
)

foreach ($j in $jobs) {
  try {
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $j.cmd -Wait -PassThru -WindowStyle Hidden
    W ($j.n + ' 退出码=' + $p.ExitCode)
  } catch {
    W ($j.n + ' 启动失败: ' + $_.Exception.Message)
  }
}

$left = @()
foreach ($k in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')) {
  if (Test-Path $k) {
    Get-ChildItem $k -ErrorAction SilentlyContinue | ForEach-Object {
      $d = (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).DisplayName
      if ($d -match 'Copilot|友约|SHAREit|User Manuals|用户手册|PhoneCompanion|Phone Companion|OneKey Optimizer|通行证') { $left += $d }
    }
  }
}
W ('卸载后仍残留登记项: ' + ($left -join ', '))
W ('C盘剩余GB=' + [math]::Round((Get-PSDrive C).Free/1GB,2))
W '完成'
