$ErrorActionPreference = 'Continue'
$log = 'E:\Daodao\_build_stage25.txt'
$s = @()
$s += '== 1 编译电脑端 =='
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'E:\Daodao\src\_apk\build_pc.ps1' 2>&1 | Out-Null
$exe = Get-Item 'E:\Daodao\src\桌面分身\道_new.exe' -ErrorAction SilentlyContinue
if ($exe) { $s += ('新 exe: ' + [math]::Round($exe.Length/1MB,2) + 'MB ' + $exe.LastWriteTime.ToString('HH:mm:ss')) } else { $s += '编译失败：没有 道_new.exe' }
$s += '== 2 停顿并替换运行文件 =='
Get-Process -Name '道' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
if (Test-Path -LiteralPath 'E:\Daodao\src\桌面分身\道_new.exe') {
  Copy-Item -LiteralPath 'E:\Daodao\src\桌面分身\道_new.exe' -Destination 'E:\Daodao\道.exe' -Force
  $s += ('已部署 道.exe: ' + [math]::Round((Get-Item 'E:\Daodao\道.exe').Length/1MB,2) + 'MB')
}
Start-Sleep -Seconds 2
Start-Process -FilePath 'E:\Daodao\道.exe'
Start-Sleep -Seconds 12
$s += ('进程数: ' + @(Get-Process -Name '道' -ErrorAction SilentlyContinue).Count)
$s += '== 3 打包手机端 =='
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'E:\Daodao\src\_apk\build.ps1' 2>&1 | Out-Null
$b = 'E:\Daodao\src\_apk\_build.txt'
if (Test-Path -LiteralPath $b) { $s += ((Get-Content -LiteralPath $b -Encoding UTF8 | Select-Object -Last 12) -join "`r`n") }
$apk = Get-Item 'E:\Daodao\src\_apk\Dao.apk' -ErrorAction SilentlyContinue
if ($apk) {
  Copy-Item -LiteralPath $apk.FullName -Destination 'E:\Daodao\道.apk' -Force
  $s += ('已部署 道.apk: ' + [math]::Round($apk.Length/1MB,2) + 'MB ' + $apk.LastWriteTime.ToString('HH:mm:ss'))
} else { $s += 'apk 打包失败' }
$s += '== 4 同步服务 =='
try {
  $c = New-Object Net.Sockets.TcpClient
  $c.Connect('127.0.0.1', 8848)
  $st = $c.GetStream()
  $w = [Text.Encoding]::ASCII.GetBytes("GET /ping HTTP/1.0`r`nHost: 127.0.0.1`r`n`r`n")
  $st.Write($w, 0, $w.Length); $st.Flush()
  $sr = New-Object IO.StreamReader($st)
  $resp = $sr.ReadToEnd()
  $c.Close()
  $line = ($resp -split "`r?`n" | Where-Object { $_ -match 'OK\|' } | Select-Object -First 1)
  $s += ('ping: ' + $line)
} catch { $s += ('ping 失败: ' + $_.Exception.Message) }
[IO.File]::WriteAllLines($log, $s, (New-Object Text.UTF8Encoding($true)))
'stage done'
