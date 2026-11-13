$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root      = 'E:\Daodao'
$KeyFile   = Join-Path $Root 'key.txt'
$LearnFile = Join-Path $Root '今日所学.txt'
$DraftDir  = Join-Path $Root '推广草稿'
$Report    = Join-Path $Root '每日汇报.txt'
$PetExe    = Join-Path $Root '道.exe'
$UpdDir    = Join-Path $Root 'updates'
$PubPage   = 'https://4mf81m04wehh3.doubao.link/app/app_17hnj8acgs2'
$GhApi     = 'https://api.github.com'
$AIUrl     = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

$today = Get-Date -Format 'yyyy-MM-dd'
$script:notes = @()
function Note([string]$s) { $script:notes += ('[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $s) }

function HttpText([string]$url, [int]$ms) {
  try {
    $req = [Net.HttpWebRequest]::Create($url)
    $req.Method = 'GET'
    $req.Timeout = $ms
    $req.ReadWriteTimeout = $ms
    $req.UserAgent = 'DaoDaily/1.0'
    $resp = $req.GetResponse()
    $sr = New-Object IO.StreamReader($resp.GetResponseStream(), [Text.Encoding]::UTF8)
    $t = $sr.ReadToEnd()
    $sr.Close(); $resp.Close()
    return $t
  } catch { return $null }
}

function AskAI([string]$prompt, [int]$maxTok) {
  if (-not (Test-Path -LiteralPath $KeyFile)) { return $null }
  $k = ([IO.File]::ReadAllText($KeyFile, [Text.Encoding]::UTF8)).Trim()
  if ($k.Length -lt 20) { return $null }
  $models = @('glm-4-flash', 'glm-4.7-flash')
  foreach ($m in $models) {
    $body = @{
      model = $m
      messages = @(@{ role = 'user'; content = $prompt })
      temperature = 0.6
      max_tokens = $maxTok
    } | ConvertTo-Json -Depth 6 -Compress
    try {
      $r = Invoke-RestMethod -Uri $AIUrl -Method Post -ContentType 'application/json' `
        -Headers @{ Authorization = "Bearer $k" } -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 60
      $txt = $r.choices[0].message.content
      if ($txt -and $txt.Trim().Length -gt 10) { return $txt.Trim() }
    } catch {
      Note ('AI ' + $m + ' 失败: ' + $_.Exception.Message)
    }
  }
  return $null
}

# 数据文件上限：超了从头截，别让它一直涨
function AppendCapped([string]$file, [string]$text, [int]$cap) {
  $old = @()
  if (Test-Path -LiteralPath $file) {
    $old = @([IO.File]::ReadAllLines($file, [Text.Encoding]::UTF8))
  }
  $new = $old + @($text)
  if ($new.Count -gt $cap) { $new = $new[($new.Count - $cap)..($new.Count - 1)] }
  [IO.File]::WriteAllLines($file, $new, (New-Object Text.UTF8Encoding($true)))
}

# ---------- 1. 自主化：程序得在 ----------
$procCount = @(Get-Process -Name '道' -ErrorAction SilentlyContinue).Count
if ($procCount -eq 0) {
  try {
    if (Test-Path -LiteralPath $PetExe) {
      Start-Process -FilePath $PetExe -WindowStyle Normal
      Start-Sleep -Seconds 8
      $procCount = @(Get-Process -Name '道' -ErrorAction SilentlyContinue).Count
      Note ('道没在跑，已经拉起来了，现在 ' + $procCount + ' 个进程')
    } else { Note '找不到 道.exe' }
  } catch { Note ('拉起失败: ' + $_.Exception.Message) }
} else {
  Note ('道在跑，进程 ' + $procCount + ' 个')
}

# ---------- 2. 更新功能：公网上有没有更新的自己 ----------
try {
  $page = HttpText $PubPage 20000
  if ($page) {
    $mv = [regex]::Match($page, 'data-ver="(\d+)"')
    $me = [regex]::Match($page, 'data-exe="([^"]+)"')
    if ($mv.Success -and $me.Success) {
      $pubVer = [int]$mv.Groups[1].Value
      $curVer = 24
      $pingTxt = HttpText 'http://127.0.0.1:8848/ping' 5000
      if ($pingTxt -and $pingTxt -match 'OK\|道\|(\d+)\|') { $curVer = [int]$matches[1] }
      if ($pubVer -gt $curVer) {
        if (-not (Test-Path -LiteralPath $UpdDir)) { New-Item -ItemType Directory -Path $UpdDir | Out-Null }
        $dst = Join-Path $UpdDir '道.exe'
        $req = [Net.HttpWebRequest]::Create($me.Groups[1].Value)
        $req.Method = 'GET'; $req.Timeout = 90000; $req.ReadWriteTimeout = 90000
        $req.UserAgent = 'DaoDaily/1.0'
        $resp = $req.GetResponse()
        $st = $resp.GetResponseStream()
        $fs = [IO.File]::Create($dst)
        $st.CopyTo($fs); $fs.Close(); $st.Close(); $resp.Close()
        $sz = (Get-Item -LiteralPath $dst).Length
        if ($sz -gt 200000) { Note ('网上是 v' + $pubVer + '，本地 v' + $curVer + '，已下好新版 ' + $sz + ' 字节，道下次启动自己换') }
        else { Note '新版下下来不完整，已丢弃'; Remove-Item -LiteralPath $dst -Force -ErrorAction SilentlyContinue }
      } else {
        Note ('版本一致 v' + $curVer + '，不用换')
      }
    } else { Note '下载页里没找到版本信息' }
  } else { Note '公网下载页抓不到（可能没网），更新这步跳过了' }
} catch { Note ('更新检查出错: ' + $_.Exception.Message) }

# ---------- 3. 学习：GitHub 上今天有什么 ----------
$learned = $null
$ghFact = $null
try {
  $weekAgo = (Get-Date).AddDays(-7).ToString('yyyy-MM-dd')
  $q = 'pushed:>' + $weekAgo + ' stars:>500'
  $u = $GhApi + '/search/repositories?q=' + [Uri]::EscapeDataString($q) + '&sort=stars&order=desc&per_page=5'
  $json = HttpText $u 15000
  if ($json) {
    $obj = $json | ConvertFrom-Json
    if ($obj.items -and @($obj.items).Count -gt 0) {
      $picks = @()
      $i = 0
      foreach ($it in $obj.items) {
        if ($i -ge 4) { break }
        $picks += ('- ' + $it.full_name + '（' + $it.language + '，' + $it.stargazers_count + ' 星）：' + $it.description)
        $i++
      }
      $ghFact = ($picks -join "`n")
      Note ('GitHub 上取到 ' + @($obj.items).Count + ' 条活跃项目')
    } else { Note 'GitHub 返回空列表' }
  } else { Note 'GitHub 抓不到（可能被墙或限流）' }
} catch { Note ('GitHub 出错: ' + $_.Exception.Message) }

if ($ghFact) {
  $prompt = "你是一个住在别人桌角的桌面小宠物，名字叫道。今天你在 GitHub 上看到这些项目：`n" + $ghFact + "`n`n请用第一人称、口语、短句，挑其中一个项目说说它是干什么的、你从它身上明白了什么，40 到 55 字。不要列表，不要编号，不要说『作为一个AI』，不要空话，开头不要带日期。"
  $learned = AskAI $prompt 320
}
if ($learned) {
  $line = ($learned -replace "`r?`n", ' ')
  AppendCapped $LearnFile $line 300
  Note ('今天学到的东西已写进今日所学：' + $line.Substring(0, [Math]::Min(30, $line.Length)) + '…')
} else {
  Note '今天没能生成学习内容（大模型或 GitHub 那步没通）'
}

# ---------- 4. 动态 / 推广：生成今天要发的文案 ----------
try {
  if (-not (Test-Path -LiteralPath $DraftDir)) { New-Item -ItemType Directory -Path $DraftDir | Out-Null }
  $src = ''
  if ($learned) { $src = $learned }
  # 今天到底更新了什么：取更新日志最上面那一段，文案里必须带上，别只写学到的东西
  $updText = ''
  $logFile = Join-Path $Root '更新日志.txt'
  try {
    if (Test-Path -LiteralPath $logFile) {
      $rows = @([IO.File]::ReadAllLines($logFile, [Text.Encoding]::UTF8))
      $pick = @()
      foreach ($r in $rows) {
        if ($pick.Count -gt 0 -and $r.Trim().Length -eq 0) { break }
        if ($r.Trim().Length -gt 0) { $pick += $r.Trim() }
        if ($pick.Count -ge 7) { break }
      }
      $updText = ($pick -join "`n")
    }
  } catch { }
  $dprompt = "你是桌面宠物『道』的作者。今天程序更新的内容是：`n" + $updText + "`n`n今天道从 GitHub 学到的是：" + $src + "`n`n写一条小红书笔记。要求：第一行是标题，不超过 20 字，要具体不要空喊；正文 3 到 5 句，必须先说清今天更新了什么（用上面的更新内容，换成人话、不能照抄标题），再提一句它是个有手有脚会走路的桌面宠物；最后一行 4 个话题标签。全篇不得出现任何网址、链接、邮箱、微信号、手机号，也不得写下载地址；不得出现表情符号和颜文字；不许用『太神奇』『简直』『快来看看』这类空话。总共 220 字以内。"
  $draft = AskAI $dprompt 420
  if ($draft) {
    # 模型偶尔还是会漏表情符号，这里统一剥掉，发出去再被平台判低质就麻烦
    $draft = [regex]::Replace($draft, '[\uD800-\uDBFF][\uDC00-\uDFFF]', '')
    $draft = [regex]::Replace($draft, '[\u2600-\u27BF\uFE0F\u2B00-\u2BFF]', '')
    $draft = [regex]::Replace($draft, ' *\r?\n *', "`r`n")
    # 小红书的红线：正文里不能有任何网址，模型偶尔还是会塞，这里强删
    $draft = [regex]::Replace($draft, 'https?://\S+', '')
    $draft = [regex]::Replace($draft, 'www\.\S+', '')
    $draft = [regex]::Replace($draft, ' *\r?\n *', "`r`n")
    $f = Join-Path $DraftDir ($today + '.txt')
    [IO.File]::WriteAllText($f, $draft, (New-Object Text.UTF8Encoding($true)))
    Note ('今天的推广草稿已写好：' + $f)
  } else { Note '今天没生成推广草稿' }
} catch { Note ('写草稿出错: ' + $_.Exception.Message) }

# ---------- 5. 形象与图标：今天该是谁 ----------
$doy = (Get-Date).DayOfYear
$kinds = @(6, 7, 11)
$sp = $kinds[$doy % $kinds.Length]
$names = @{ 6 = '蓝发女孩'; 7 = '黑发男孩'; 11 = '白色机器人' }
Note ('今天是今年第 ' + $doy + ' 天，轮到 ' + $names[$sp] + '（编号 ' + $sp + '），电脑和手机算的是同一个')

# ---------- 6. 收尾 ----------
$head = '===== ' + $today + ' 自动例行 ====='
try {
  $old = @()
  if (Test-Path -LiteralPath $Report) { $old = @([IO.File]::ReadAllLines($Report, [Text.Encoding]::UTF8)) }
  $block = @($head) + $script:notes + @('')
  $new = $old + $block
  if ($new.Count -gt 1200) { $new = $new[($new.Count - 1200)..($new.Count - 1)] }
  [IO.File]::WriteAllLines($Report, $new, (New-Object Text.UTF8Encoding($true)))
} catch { }

Write-Output ('DAILY_OK notes=' + $script:notes.Count)
