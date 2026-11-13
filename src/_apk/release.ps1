# 发布新版本的电脑版「道」
# 用法：先跑 build_pc.ps1 生成 道_new.exe，再跑本脚本把新包投进 updates\
# 道下次启动或点「我现在就检查更新」时会自己换上新身子

$nl = [Environment]::NewLine
$o = ''
$src = 'E:\Daodao\src\桌面分身\道_new.exe'
$dst = 'E:\Daodao\updates\道.exe'

if (-not (Test-Path -LiteralPath $src)) {
    [IO.File]::WriteAllText('E:\Daodao\src\_apk\_release.txt', 'MISSING 道_new.exe', (New-Object Text.UTF8Encoding($true)))
    return
}

New-Item -ItemType Directory -Force -Path 'E:\Daodao\updates' | Out-Null
Copy-Item -LiteralPath $src -Destination $dst -Force

$o += 'published=' + (Get-Item -LiteralPath $dst).Length + $nl
$o += 'stamp=' + (Get-Item -LiteralPath $dst).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') + $nl
$o += 'notice=道下次启动会自己换上新版本' + $nl

[IO.File]::WriteAllText('E:\Daodao\src\_apk\_release.txt', $o, (New-Object Text.UTF8Encoding($true)))
'done'
