$nl = [Environment]::NewLine
$o = ''

# 1. 部署新 APK
Copy-Item -LiteralPath 'E:\Daodao\src\_apk\Dao.apk' -Destination 'E:\Daodao\道.apk' -Force
$o += 'apk_MB=' + [math]::Round((Get-Item -LiteralPath 'E:\Daodao\道.apk').Length / 1MB, 2) + $nl

# 2. 部署新 exe（先停旧的）
Get-Process -Name '道' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
if (Test-Path -LiteralPath 'E:\Daodao\道.exe') {
    Copy-Item -LiteralPath 'E:\Daodao\道.exe' -Destination 'E:\Daodao\道.exe.bak3' -Force
}
Copy-Item -LiteralPath 'E:\Daodao\src\桌面分身\道_new.exe' -Destination 'E:\Daodao\道.exe' -Force
$o += 'exe_size=' + (Get-Item -LiteralPath 'E:\Daodao\道.exe').Length + $nl

# 3. 自更新投递目录
New-Item -ItemType Directory -Force -Path 'E:\Daodao\updates' | Out-Null
$o += 'updates_dir=' + (Test-Path -LiteralPath 'E:\Daodao\updates') + $nl

# 4. 拉起来
Start-Process -FilePath 'E:\Daodao\道.exe'
Start-Sleep -Seconds 4
$ps = @(Get-Process -Name '道' -ErrorAction SilentlyContinue)
$o += 'new_procs=' + $ps.Count + $nl

# 5. 同步服务还在不在
try {
    $c = Get-NetTCPConnection -LocalPort 8848 -State Listen -ErrorAction Stop
    $o += 'listen_8848=' + $c.Count + $nl
} catch { $o += 'listen_8848=none' + $nl }

# 6. 冒烟测一下
try {
    $t = New-Object System.Net.Sockets.TcpClient
    $t.Connect('127.0.0.1', 8848)
    $s = $t.GetStream()
    $b = [Text.Encoding]::ASCII.GetBytes("GET /ping HTTP/1.0`r`nHost: 127.0.0.1`r`n`r`n")
    $s.Write($b, 0, $b.Length); $s.Flush()
    $buf = New-Object byte[] 1024
    $sb = New-Object System.Text.StringBuilder
    while ($true) { $n = $s.Read($buf, 0, 1024); if ($n -le 0) { break }; [void]$sb.Append([Text.Encoding]::UTF8.GetString($buf, 0, $n)) }
    $txt = $sb.ToString()
    $i = $txt.IndexOf("`r`n`r`n")
    $o += 'ping=' + $(if ($i -ge 0) { $txt.Substring($i + 4).Trim() } else { 'no_body' }) + $nl
    $t.Close()
} catch { $o += 'ping=FAIL' + $nl }

[IO.File]::WriteAllText('C:\Users\Administrator\Doubao\chats\2026-11-06\_deploy3.txt', $o, (New-Object Text.UTF8Encoding($true)))
'done'
