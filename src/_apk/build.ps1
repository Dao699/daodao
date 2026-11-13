$logs = New-Object System.Collections.ArrayList
function W($s) { [void]$logs.Add([string]$s) }

$jdk = 'E:\AndroidTools\jdk_ext\jdk-17.0.20.1+1'
$sdk = 'E:\AndroidTools\sdk'
$bt  = "$sdk\build-tools\34.0.0"
$aj  = "$sdk\platforms\android-33\android.jar"
$a   = 'E:\Daodao\src\_apk'

$env:JAVA_HOME = $jdk
$env:PATH = "$jdk\bin;$bt;$env:PATH"

W ("jdk=" + (Test-Path $jdk) + " bt=" + (Test-Path $bt) + " jar=" + (Test-Path $aj))

foreach ($d in @("$a\obj", "$a\dex", "$a\gen")) {
    if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force }
}
foreach ($f in @("$a\res.zip", "$a\base.apk", "$a\aligned.apk", "$a\Dao.apk")) {
    if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force }
}

W "== 1 aapt2 compile =="
$r = & "$bt\aapt2.exe" compile --dir "$a\res" -o "$a\res.zip" 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)
W ("res.zip=" + (Test-Path -LiteralPath "$a\res.zip"))

W "== 2 aapt2 link =="
$r = & "$bt\aapt2.exe" link -o "$a\base.apk" -I $aj --manifest "$a\AndroidManifest.xml" -R "$a\res.zip" --java "$a\gen" --min-sdk-version 21 --target-sdk-version 33 -A "$a\assets" --auto-add-overlay 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)
W ("base.apk=" + (Test-Path -LiteralPath "$a\base.apk"))

W "== 3 javac =="
New-Item -ItemType Directory -Path "$a\obj" -Force | Out-Null
$srcFiles = @(Get-ChildItem -LiteralPath "$a\src" -Recurse -Filter *.java | ForEach-Object { $_.FullName })
$genFiles = @(Get-ChildItem -LiteralPath "$a\gen" -Recurse -Filter *.java -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
W ("src=" + $srcFiles.Count + " gen=" + $genFiles.Count)
$allSrc = @($srcFiles) + @($genFiles)
$r = & "$jdk\bin\javac.exe" -encoding UTF-8 -source 8 -target 8 -bootclasspath $aj -d "$a\obj" $allSrc 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)

W "== 4 d8 =="
New-Item -ItemType Directory -Path "$a\dex" -Force | Out-Null
$clsFiles = @(Get-ChildItem -LiteralPath "$a\obj" -Recurse -Filter *.class | ForEach-Object { $_.FullName })
W ("classes=" + $clsFiles.Count)
$r = & "$bt\d8.bat" --lib $aj --min-api 21 --output "$a\dex" $clsFiles 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)
W ("classes.dex=" + (Test-Path -LiteralPath "$a\dex\classes.dex"))

W "== 5 add dex =="
$sevenZ = 'E:\Tools\7-Zip\7z.exe'
if (-not (Test-Path -LiteralPath $sevenZ)) { $sevenZ = 'C:\Program Files\7-Zip\7z.exe' }
W ("7z=" + $sevenZ + " exists=" + (Test-Path -LiteralPath $sevenZ))
Push-Location "$a\dex"
$r = & $sevenZ a -tzip "$a\base.apk" "classes.dex" 2>&1 | Out-String
Pop-Location
W $r.Trim()
W ("exit=" + $LASTEXITCODE)

W "== 6 zipalign =="
$r = & "$bt\zipalign.exe" -f -p 4 "$a\base.apk" "$a\aligned.apk" 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)
W ("aligned.apk=" + (Test-Path -LiteralPath "$a\aligned.apk"))

W "== 7 keytool =="
$ks = "$a\dao.jks"
if (Test-Path -LiteralPath $ks) {
    W "keystore reuse=True"
} else {
    $r = & "$jdk\bin\keytool.exe" -genkeypair -keystore $ks -alias dao -keyalg RSA -keysize 2048 -validity 10000 -storepass daodao123 -keypass daodao123 -dname "CN=Dao, OU=Dao, O=Dao, L=Meizhou, ST=Guangdong, C=CN" -noprompt 2>&1 | Out-String
    W $r.Trim()
    W ("exit=" + $LASTEXITCODE)
}
W ("keystore=" + (Test-Path -LiteralPath $ks))

W "== 8 apksigner sign =="
$r = & "$bt\apksigner.bat" sign --ks $ks --ks-pass "pass:daodao123" --key-pass "pass:daodao123" --out "$a\Dao.apk" "$a\aligned.apk" 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)

W "== 9 verify =="
$r = & "$bt\apksigner.bat" verify --verbose "$a\Dao.apk" 2>&1 | Out-String
W $r.Trim()
W ("exit=" + $LASTEXITCODE)

if (Test-Path -LiteralPath "$a\Dao.apk") {
    W ("APK_MB=" + [math]::Round((Get-Item -LiteralPath "$a\Dao.apk").Length / 1MB, 2))
} else {
    W "APK_MISSING"
}

[IO.File]::WriteAllText("$a\_build.txt", ($logs -join "`r`n"), (New-Object Text.UTF8Encoding($true)))
'done'
