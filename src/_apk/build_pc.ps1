$ErrorActionPreference = 'Stop'
$nl = [Environment]::NewLine
$d = 'E:\Daodao\src\桌面分身'
$log = @()

Set-Location -LiteralPath $d
if (Test-Path -LiteralPath "$d\pet.cs") {
    Copy-Item -LiteralPath "$d\pet.cs" -Destination "$d\pet.cs.bak" -Force
}

$csc = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $csc)) {
    [IO.File]::WriteAllText("$d\_buildsync.txt", 'CSC_MISSING', (New-Object Text.UTF8Encoding($true)))
    return
}

$cargs = @('/nologo', '/target:winexe', '/out:道_new.exe', '/win32icon:道.ico')
$cargs += '/r:System.Windows.Forms.dll'
$cargs += '/r:System.Drawing.dll'
$cargs += '/r:System.dll'

for ($i = 0; $i -lt 12; $i++) {
    $p = "faces_cut5\face_$i.png"
    if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,face_$i.png" }
}
# 每套姿势图（stand/wave/walk/cheer/sit）按形象分开塞，程序按当天的形象取对应那一套
for ($sp = 0; $sp -lt 12; $sp++) {
    foreach ($n in @('stand', 'wave', 'walk', 'cheer', 'sit')) {
        $p = "_poses_dev$sp\$n.png"
        if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,pose_${sp}_$n.png" }
    }
}
# 八帧走路循环：按形象分目录放，进了 exe 才是自包含的，拷到哪都能走
for ($sp = 0; $sp -lt 12; $sp++) {
    for ($wi = 1; $wi -le 8; $wi++) {
        $p = "_walk8_$sp\walk$wi.png"
        if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,walk8_${sp}_$wi.png" }
    }
}
# 御剑姿势图：有真图的形象就嵌进去，没有的还是由程序自己画一把剑
for ($sp = 0; $sp -lt 12; $sp++) {
    $p = "_swordfly\$sp.png"
    if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,swordfly_$sp.png" }
}
# 表情整图：笑/难过/生气/睡着，按形象分文件塞进去，进了 exe 才是自包含的
for ($sp = 0; $sp -lt 12; $sp++) {
    foreach ($k in @('happy', 'sad', 'angry', 'sleep')) {
        $p = "_expr\${k}_$sp.png"
        if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,expr_${sp}_$k.png" }
    }
}
# 笑的动态帧：happy 是第一帧，再补三张，四帧循环才动得起来
for ($sp = 0; $sp -lt 12; $sp++) {
    for ($li = 2; $li -le 4; $li++) {
        $p = "_expr\laugh${li}_$sp.png"
        if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,expr_${sp}_laugh$li.png" }
    }
}
foreach ($n in @('names.txt', 'voices.txt')) {
    $p = "faces\$n"
    if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,$n" }
}
foreach ($n in @('key.txt', '知识库.txt', 'hear.py', 'hear_en.py', 'trans.py', 'voice.py', 'play_audio.py', 'github_learn.py', '记忆.txt', '我说的话.txt', '今日所学.txt', '更新日志.txt')) {
    if (Test-Path -LiteralPath $n) { $cargs += "/resource:$n,$n" }
}
$cargs += 'pet.cs'

$log += ('cargs=' + $cargs.Count)
$out = & $csc @cargs 2>&1 | Out-String
$log += $out
$log += ('exit=' + $LASTEXITCODE)
$exe = "$d\道_new.exe"
$log += ('exe_ok=' + (Test-Path -LiteralPath $exe))
if (Test-Path -LiteralPath $exe) {
    $log += ('size=' + (Get-Item -LiteralPath $exe).Length)
}

[IO.File]::WriteAllText("$d\_buildsync.txt", ($log -join $nl), (New-Object Text.UTF8Encoding($true)))
'done'
