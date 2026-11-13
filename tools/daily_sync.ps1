# 道的每日同步：电脑端和手机端始终是同一版
# 逻辑：源码比 exe 新就重编译；apk 里的页面和 dao.html 不一致就重打；
#       随身版网页跟着 dao.html 走。手机在局域网里从 8848/apk 就能拿到最新包。
$ErrorActionPreference = 'Continue'
$root = 'E:\Daodao'
$log  = Join-Path $root '同步日志.txt'
function Log([string]$m) {
    $line = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m
    Add-Content -LiteralPath $log -Value $line -Encoding utf8
}

$srcCs    = Join-Path $root 'src\桌面分身\pet.cs'
$exe      = Join-Path $root '道.exe'
$html     = Join-Path $root 'src\_apk\assets\dao.html'
$apk      = Join-Path $root '道.apk'
$apkSrc   = Join-Path $root 'src\_apk\Dao.apk'
$portable = Join-Path $root '道-随身版.html'
$sevenZ   = 'E:\Tools\7-Zip\7z.exe'
if (-not (Test-Path -LiteralPath $sevenZ)) { $sevenZ = 'C:\Program Files\7-Zip\7z.exe' }
$jdk = 'E:\AndroidTools\jdk_ext\jdk-17.0.20.1+1'
$bt  = 'E:\AndroidTools\sdk\build-tools\34.0.0'
$ks  = Join-Path $root 'src\_apk\dao.jks'
$bd  = 'C:\Users\Administrator\Doubao\chats\2026-11-06\_bd.ps1'

$changed = @()
Log '--- 每日同步开始 ---'

# 1) 随身版网页
if (Test-Path -LiteralPath $html) {
    $need = $true
    if (Test-Path -LiteralPath $portable) {
        if ((Get-Item -LiteralPath $portable).LastWriteTime -ge (Get-Item -LiteralPath $html).LastWriteTime) { $need = $false }
    }
    if ($need) {
        Copy-Item -LiteralPath $html -Destination $portable -Force
        # 桌面那份是给快捷方式用的入口，跟着一起换，免得点开的还是旧版
        $deskHtml = Join-Path ([Environment]::GetFolderPath('Desktop')) '道-随身版.html'
        Copy-Item -LiteralPath $html -Destination $deskHtml -Force
        $changed += '随身版网页已更新'
        Log '随身版网页已更新'
    }
} else { Log '找不到 dao.html，跳过随身版' }

# 2) 电脑端是否需要重编译
if ((Test-Path -LiteralPath $srcCs) -and (Test-Path -LiteralPath $exe)) {
    if ((Get-Item -LiteralPath $srcCs).LastWriteTime -gt (Get-Item -LiteralPath $exe).LastWriteTime) {
        Log '源码比 exe 新，开始重新编译'
        if (Test-Path -LiteralPath $bd) {
            & $bd *>&1 | Out-File -LiteralPath (Join-Path $root '构建输出.txt') -Encoding utf8
            $tail = @(Get-Content -LiteralPath (Join-Path $root '构建输出.txt') -Tail 1)
            Log ('编译完成: ' + ($tail -join ' '))
            $changed += '电脑端已重新编译'
        } else { Log '找不到构建脚本，跳过编译' }
    }
}

# 3) 手机端 apk 里是不是最新的页面
$needApk = $false
if ((Test-Path -LiteralPath $html) -and (Test-Path -LiteralPath $apk)) {
    $tmp = Join-Path $env:TEMP ('daoapk_' + [Guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    try {
        & $sevenZ e $apk ('-o' + $tmp) 'assets\dao.html' -y | Out-Null
        if (Test-Path -LiteralPath (Join-Path $tmp 'dao.html')) {
            $h1 = (Get-FileHash -LiteralPath (Join-Path $tmp 'dao.html') -Algorithm MD5).Hash
            $h2 = (Get-FileHash -LiteralPath $html -Algorithm MD5).Hash
            if ($h1 -ne $h2) { $needApk = $true; Log 'apk 内的页面与源码不一致' }
            else { Log 'apk 内页面已是最新' }
        } else { $needApk = $true; Log 'apk 里没找到页面' }
    } catch { $needApk = $true; Log ('读 apk 失败: ' + $_.Exception.Message) }
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
} else { Log '缺 apk 或页面文件，跳过打包' }

if ($needApk) {
    Log '开始重打手机安装包'
    $env:JAVA_HOME = $jdk
    $env:PATH = "$jdk\bin;$bt;$env:PATH"
    $adir = Join-Path $root 'src\_apk'
    $m = Join-Path $adir '_daily_m.apk'
    $a = Join-Path $adir '_daily_a.apk'
    try {
        Copy-Item -LiteralPath $apkSrc -Destination $m -Force
        Push-Location $adir
        & $sevenZ a -tzip $m 'assets\dao.html' | Out-Null
        Pop-Location
        & (Join-Path $bt 'zipalign.exe') -f -p 4 $m $a | Out-Null
        & (Join-Path $bt 'apksigner.bat') sign --ks $ks --ks-pass 'pass:daodao123' --key-pass 'pass:daodao123' --out $apkSrc $a 2>&1 | Out-Null
        & (Join-Path $bt 'apksigner.bat') verify $apkSrc | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Copy-Item -LiteralPath $apkSrc -Destination $apk -Force
            $changed += '手机端安装包已重打'
            Log '安装包已重打，签名校验通过'
        } else { Log '签名校验没过，保留旧包' }
    } catch { Log ('打包出错: ' + $_.Exception.Message) }
    Remove-Item -LiteralPath $m -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $a -Force -ErrorAction SilentlyContinue
}

if ($changed.Count -eq 0) { Log '两端本来就是同一版，无需改动' }
Log ('结果: ' + (($changed | ForEach-Object { $_ }) -join '、'))
Log '--- 每日同步结束 ---'