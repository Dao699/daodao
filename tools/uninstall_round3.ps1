$log = 'E:\Daodao\卸载记录.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }

$id = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"') -Verb RunAs
  exit
}
W ('第三轮开始 管理员=True')

function MsiOf($guid){
  $d = 'C:\Program Files (x86)\InstallShield Installation Information\' + $guid
  if (Test-Path -LiteralPath $d) {
    Get-ChildItem -LiteralPath $d -Filter '*.msi' -File -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
  }
}

function UnMsi($label, $guid){
  $msi = MsiOf $guid
  if ($msi) {
    $p = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/x', $msi, '/qn', '/norestart' -Wait -PassThru -WindowStyle Hidden
    W ($label + ' msiexec 退出码=' + $p.ExitCode)
    return
  }
  $p2 = Start-Process -FilePath 'msiexec.exe' -ArgumentList '/x', ('{' + $guid + '}'), '/qn', '/norestart' -Wait -PassThru -WindowStyle Hidden
  W ($label + ' 按产品码 msiexec 退出码=' + $p2.ExitCode)
}

UnMsi 'Lenovo Photo Master' 'BC94C56A-3649-420C-8756-2ADEBE399D33'
UnMsi 'Lenovo PhoneCompanion' '0F82EA83-B0C5-4AB9-9695-DFE92C5FD57B'
UnMsi 'OneKey Optimizer' 'D5D573DC-D989-4769-9B56-D6A7EA503D7F'
UnMsi 'User Manuals' 'F07C2CF8-4C53-4EC3-8162-A6221E36EB88'
UnMsi 'Intel Update Manager' '84A2B59B-6A7B-4C01-8592-15C9BFE6AC36'

$u1 = 'C:\Program Files (x86)\MagicPlus\MagicPlus_Uninstall.exe'
if (Test-Path -LiteralPath $u1) {
  $p = Start-Process -FilePath $u1 -ArgumentList '/S' -Wait -PassThru -WindowStyle Hidden
  W ('乐助手 退出码=' + $p.ExitCode)
}

$u2 = 'C:\Program Files (x86)\Lenovo\Lenovo Home\uninstall.exe'
if (Test-Path -LiteralPath $u2) {
  $p = Start-Process -FilePath $u2 -ArgumentList '/S' -Wait -PassThru -WindowStyle Hidden
  W ('联想服务 退出码=' + $p.ExitCode)
}

$targets = @(
  @{ dir = 'C:\Program Files (x86)\Lenovo\Lenovo Photo Master'; name = '照片大师' },
  @{ dir = 'C:\Program Files (x86)\Lenovo\PhoneCompanion'; name = 'PhoneCompanion' },
  @{ dir = 'C:\Program Files (x86)\Lenovo\OneKey Optimizer'; name = '一键优化' },
  @{ dir = 'C:\Program Files (x86)\Lenovo\UserGuide'; name = '用户手册' },
  @{ dir = 'C:\Program Files (x86)\MagicPlus'; name = '乐助手' },
  @{ dir = 'C:\Program Files (x86)\Lenovo\Lenovo Home'; name = '联想服务' },
  @{ dir = 'C:\Program Files (x86)\Lenovo PhotoMasterImport'; name = '手机导入组件' }
)

Start-Sleep -Seconds 3
foreach ($t in $targets) {
  if (Test-Path -LiteralPath $t.dir) {
    try {
      Remove-Item -LiteralPath $t.dir -Recurse -Force -ErrorAction Stop
      W ('已删除残留目录: ' + $t.name)
    } catch { W ('目录删不动: ' + $t.name + ' ' + $_.Exception.Message) }
  }
}

foreach ($root in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')) {
  if (Test-Path $root) {
    Get-ChildItem $root -ErrorAction SilentlyContinue | ForEach-Object {
      $d = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
      $n = $d.DisplayName
      if (-not $n) { return }
      if ($n -match 'Photo Master|PhoneCompanion|OneKey Optimizer|User Manuals|乐助手|联想服务|Mobile Phone Wireless Import') {
        $loc = $d.InstallLocation
        $gone = $true
        if ($loc) {
          $clean = $loc.Trim('"')
          if (Test-Path -LiteralPath $clean) { $gone = $false }
        }
        if ($gone) {
          Remove-Item -LiteralPath $_.PSPath -Recurse -Force -ErrorAction SilentlyContinue
          W ('清登记项: ' + $n)
        }
      }
    }
  }
}

W ('C盘剩余GB=' + [math]::Round((Get-PSDrive C).Free/1GB,2))
W '第三轮完成'
