$log = 'E:\Daodao\启动项调整.log'
function W($m){ Add-Content -LiteralPath $log -Value ('[' + (Get-Date).ToString('HH:mm:ss') + '] ' + $m) -Encoding utf8 }

$runKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
$bk = 'E:\Daodao\备份\HKLM启动项备份_' + (Get-Date -Format 'yyyyMMdd_HHmm') + '.reg'
reg export 'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' $bk /y | Out-Null
W "已备份 HKLM 启动项到 $bk"

# 只关这些确实没用的 OEM 托盘/助手，驱动与音频、触摸板、热键、Defender 一律不动
$off = @('RtsFT','PhoneCompanion','OneKeyOptimizer','LENOVO.TPKNRRES','IAStorIcon')
$p = Get-ItemProperty -LiteralPath $runKey
foreach ($n in $off) {
  if ($p.PSObject.Properties.Name -contains $n) {
    $v = $p.$n
    New-ItemProperty -LiteralPath $runKey -Name ("OFF_" + $n) -Value $v -PropertyType String -Force | Out-Null
    Remove-ItemProperty -LiteralPath $runKey -Name $n -ErrorAction SilentlyContinue
    W "已关闭开机启动: $n"
  } else {
    W "本来就没有: $n"
  }
}

$p2 = Get-ItemProperty -LiteralPath $runKey
$left = $p2.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object { $_.Name }
W ("现在HKLM启动项: " + ($left -join ', '))
W '完成'
