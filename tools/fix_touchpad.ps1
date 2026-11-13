<#
  触摸板误触修复（可回退）
  病因：ELAN 触摸板「轻敲即点击」「右下角右键区」「多指轻敲」全开，
        打字时手腕/手掌压到触摸板就会误触发右键菜单或拖选文字（表现为莫名的复制粘贴）。
  用法：
    修复：powershell -NoProfile -ExecutionPolicy Bypass -File fix_touchpad.ps1 -Apply
    回退：powershell -NoProfile -ExecutionPolicy Bypass -File fix_touchpad.ps1 -Revert
#>
param([switch]$Apply, [switch]$Revert)

$ErrorActionPreference = 'Stop'
$padKey  = 'HKCU:\Software\Elantech\SmartPad'
$ptKey   = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad'
$bakFile = 'E:\Daodao\tools\touchpad_backup.json'

# 要调整的开关：轻敲类全部关闭，关闭右下角右键区，插鼠标时自动禁用触摸板
$padSwitches = @(
  'Tap_Enable',
  'Tap_Activate_Enable',
  'Tap_One_Finger_Enable',
  'Tap_Two_Finger_Enable',
  'Tap_Three_Finger_Enable',
  'Tap_Four_Finger_Enable',
  'TwoFingerTap_Enable',
  'b3A2TP_RightButton_Enable'
)

function Show-State($tag) {
  Write-Host "---- $tag ----"
  foreach ($k in $padSwitches) {
    $v = (Get-ItemProperty -LiteralPath $padKey -Name $k -ErrorAction SilentlyContinue).$k
    Write-Host ("  {0} = {1}" -f $k, $v)
  }
  $l = (Get-ItemProperty -LiteralPath $ptKey -Name 'LeaveOnWithMouse' -ErrorAction SilentlyContinue).LeaveOnWithMouse
  Write-Host ("  LeaveOnWithMouse = {0}" -f $l)
}

if ($Revert) {
  if (-not (Test-Path -LiteralPath $bakFile)) { Write-Host '没有找到备份文件，无法回退。' -ForegroundColor Yellow; exit 1 }
  $bak = Get-Content -LiteralPath $bakFile -Raw | ConvertFrom-Json
  foreach ($k in $bak.pad.PSObject.Properties) {
    Set-ItemProperty -LiteralPath $padKey -Name $k.Name -Value ([int]$k.Value)
  }
  if ($null -ne $bak.leaveOnWithMouse) {
    Set-ItemProperty -LiteralPath $ptKey -Name 'LeaveOnWithMouse' -Value ([int]$bak.leaveOnWithMouse)
  }
  Restart-Service -Name 'ETDService' -Force -ErrorAction SilentlyContinue
  Write-Host '已回退到修改前的设置。' -ForegroundColor Green
  Show-State '当前状态'
  exit 0
}

if (-not $Apply) {
  Write-Host '请加参数：-Apply 修复，或 -Revert 回退。'
  exit 0
}

# 首次运行时备份
if (-not (Test-Path -LiteralPath $bakFile)) {
  $pad = @{}
  foreach ($k in $padSwitches) {
    $pad[$k] = [int]((Get-ItemProperty -LiteralPath $padKey -Name $k -ErrorAction SilentlyContinue).$k)
  }
  $lom = [int]((Get-ItemProperty -LiteralPath $ptKey -Name 'LeaveOnWithMouse' -ErrorAction SilentlyContinue).LeaveOnWithMouse)
  $obj = [ordered]@{ pad = $pad; leaveOnWithMouse = $lom }
  [IO.File]::WriteAllText($bakFile, ($obj | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
  Write-Host "已备份原值到 $bakFile" -ForegroundColor Gray
} else {
  Write-Host "备份已存在，沿用 $bakFile" -ForegroundColor Gray
}

Show-State '修改前'

foreach ($k in $padSwitches) {
  if ($null -ne (Get-ItemProperty -LiteralPath $padKey -Name $k -ErrorAction SilentlyContinue).$k) {
    Set-ItemProperty -LiteralPath $padKey -Name $k -Value 0 -Type DWord
  }
}
# 接鼠标时自动禁用触摸板，避免手腕压板
if ($null -ne (Get-ItemProperty -LiteralPath $ptKey -Name 'LeaveOnWithMouse' -ErrorAction SilentlyContinue).LeaveOnWithMouse) {
  Set-ItemProperty -LiteralPath $ptKey -Name 'LeaveOnWithMouse' -Value 0 -Type DWord
}
# 打字时禁用触摸板保持开启（如果被关了就重新打开）
if ($null -ne (Get-ItemProperty -LiteralPath $padKey -Name 'DisableWhenType_Enable' -ErrorAction SilentlyContinue).DisableWhenType_Enable) {
  Set-ItemProperty -LiteralPath $padKey -Name 'DisableWhenType_Enable' -Value 1 -Type DWord
}

Restart-Service -Name 'ETDService' -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 800
Show-State '修改后'

Write-Host ''
Write-Host '已关闭：轻敲点击、双/三/四指轻敲、右下角右键区；并设为“插上鼠标自动禁用触摸板”。' -ForegroundColor Green
Write-Host '建议重启一次让 ELAN 驱动完全生效。想还原：跑同一条命令加 -Revert。' -ForegroundColor Yellow
