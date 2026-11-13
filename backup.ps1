param([string]$dir)
$dst = Join-Path $dir '备份'
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }
$stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$zip = Join-Path $dst ('道_' + $stamp + '.zip')
$list = @()
foreach ($n in @('道.exe','pet.cs','pet.manifest','记忆.txt','我说的话.txt','make_icons.ps1','daily_brief.ps1','daily_bing.ps1','hear.py','backup.ps1')) {
  $p = Join-Path $dir $n
  if (Test-Path -LiteralPath $p) { $list += $p }
}
foreach ($d in @('icons','faces')) {
  $p = Join-Path $dir $d
  if (Test-Path -LiteralPath $p) { $list += $p }
}
if ($list.Count -eq 0) { Write-Output 'NONE'; exit }
Compress-Archive -Path $list -DestinationPath $zip -Force
Get-ChildItem -LiteralPath $dst -Filter '道_*.zip' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 7 | Remove-Item -Force
$f = Get-Item -LiteralPath $zip
Write-Output ('OK|' + $f.Name + '|' + [math]::Round($f.Length/1MB,1))
