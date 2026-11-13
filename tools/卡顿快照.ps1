# 卡顿现场快照：感觉卡的时候双击这个脚本，10 秒后把当时的状态追加到 卡顿记录.txt
$log = 'E:\Daodao\卡顿记录.txt'
function L($m){ $line = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m; Add-Content -LiteralPath $log -Value $line -Encoding UTF8; Write-Output $line }
L "=== 快照开始（请保持卡的状态不要关窗口）==="
$os = Get-CimInstance Win32_OperatingSystem
L ("内存 可用 " + [math]::Round($os.FreePhysicalMemory/1MB,2) + " GB / 使用率 " + [math]::Round((1-$os.FreePhysicalMemory/$os.TotalVisibleMemorySize)*100) + "%")
$cpu1 = (Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'").PercentProcessorTime
$s1 = @{}
foreach($p in (Get-Process)){ if($p.CPU){ $s1[$p.Id] = $p.CPU } }
Start-Sleep -Seconds 6
$cpu2 = (Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'").PercentProcessorTime
L ("CPU 总占用 " + $cpu1 + "% -> " + $cpu2 + "%")
$top = @()
foreach($p in (Get-Process)){
  if(-not $p.CPU -or -not $s1.ContainsKey($p.Id)){ continue }
  $d = $p.CPU - $s1[$p.Id]
  if($d -gt 0){ $top += [pscustomobject]@{ N=$p.Name; P=[math]::Round($d/6/4*100,1) } }
}
L "CPU 前八名（占单核百分比）:"
foreach($x in ($top | Sort-Object P -Descending | Select-Object -First 8)){ L ("   " + $x.N + "  " + $x.P + "%") }
$cu = @{}
foreach($p in (Get-Process)){ if($p.WorkingSet64){ if($cu.ContainsKey($p.Name)){$cu[$p.Name]+=$p.WorkingSet64}else{$cu[$p.Name]=$p.WorkingSet64} } }
$mg = @()
foreach($k in $cu.Keys){ $mg += [pscustomobject]@{ N=$k; M=[math]::Round($cu[$k]/1MB) } }
L "内存前八名:"
foreach($x in ($mg | Sort-Object M -Descending | Select-Object -First 8)){ L ("   " + $x.N + "  " + $x.M + " MB") }
foreach($n in @('C:','E:')){
  $dk = Get-CimInstance Win32_PerfFormattedData_PerfDisk_LogicalDisk -Filter ("Name='" + $n + "'")
  if($dk){ L ("磁盘 " + $n + " 繁忙 " + $dk.PercentDiskTime + "% / 队列 " + $dk.AvgDiskQueueLength + " / 读 " + [math]::Round($dk.DiskReadBytesPerSec/1MB,1) + " MB/s 写 " + [math]::Round($dk.DiskWriteBytesPerSec/1MB,1) + " MB/s") }
}
L ("进程数 " + (Get-Process | Measure-Object).Count)
L "=== 快照结束 ==="