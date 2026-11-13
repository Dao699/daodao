# 每天给「道」生成一份宣传物料：三个平台的文案 + 当天配图
# 全部用 PowerShell 实现，不依赖 python 路径，计划任务直接跑得起来
$ErrorImportance = $null
$APP = 'E:\Daodao'
$OUT = Join-Path $APP '宣传'
$SHOT = 'C:\Users\Administrator\Doubao\chats\2026-11-06'
$LOG = Join-Path $OUT 'log.txt'

$POINTS = @"
1. 12 个形象随机出现：橘猫、赤狐、银发剑客、小机器人、熊猫、汉服女子、紫袍女巫、绿恐龙、企鹅、蓝发双马尾、黑发男孩等
2. 会说话，多套嗓音（男声、女声、萝莉、御姐、机器人腔），早中晚自动把音量压小，不吵人
3. 会背古诗（35 首）、会唱歌（小星星）、会教英语（60 句），还会讲故事、说笑话、念小说
4. 会披着红披风被风吹着飞、会御剑踩剑而行、会骑坐骑赶路、会跳舞、会喝茶喝咖啡（手握着杯子端起来喝）、会看电视、会滑板轮滑
5. 五个场景会自己换：城市车流路灯、乡野田垄、海边日落沙滩、花丛蝴蝶、屋里
6. 接了大模型当导演：你说一句话，它自己判断该干什么，不是死板的关键字
7. 电脑端是单文件 exe，4GB 老笔记本也能跑；手机端有随身版和网页版，电脑手机通着
8. 一块钱就能用
"@

$TOPICS = @(
  '披着红披风被风吹着飞',
  '踩剑而行，御剑飞行',
  '手握着咖啡杯，端起来喝一口',
  '随口背一首古诗',
  '唱歌',
  '一句一句教英语',
  '五个场景自动换：城市车流、乡野田垄、海边日落、花丛蝴蝶、屋里',
  '你说一句话，它自己判断该干什么',
  '手机端随身版，电脑手机通着',
  '滑板和轮滑',
  '坐在电视前看电视',
  '跟着节拍跳舞'
)

$HERO = @{
  fly = '_s_cw4_fly.jpg'; sword = '_s_cw4_sword.jpg'; coffee = '_s_cup4a_tea.jpg';
  coffee2 = '_s_cup4c.jpg'; tv = '_s_tv3_tv.jpg'; poem = '_s_pm1_poem.jpg'
}
$SCENE = @{
  scene = '_s_sc6_walk.jpg'; sea = '_s_sc6_fly.jpg'; sing = '_s_sg1_sing.jpg';
  skate = '_s_sk4_skate.jpg'; ai = '_s_ai4_fly.jpg'
}

New-Item -ItemType Directory -Force -Path $OUT | Out-Null
$day = Get-Date -Format 'yyyy-MM-dd'
$dir = Join-Path $OUT $day
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$text = ''

try {
  $key = (Get-Content -LiteralPath (Join-Path $APP 'key.txt') -Raw -Encoding UTF8).Trim()
} catch {
  $key = ''
}

if ($key) {
  $idx = [int](((Get-Date) - [datetime]'2026-11-08').Days % $TOPICS.Count)
  if ($idx -lt 0) { $idx = 0 }
  $topic = $TOPICS[$idx]
  $prompt = "这是我要宣传的桌面宠物应用「道」，它的真实功能如下：`n$POINTS`n`n今天的宣传主题是：$topic，三段都围绕这个主题写。`n请写三段中文文案，直接给内容，不要解释：`n第一段以【小红书】开头，下一行是标题（二十字内），再下一行开始是正文（一百到一百五十字），先讲一个具体的使用场景，再落到今天的主题上，顺带点出一两项别的功能。`n第二段以【抖音口播】开头，必须是一整段连贯的话，八十到一百字，二十秒能念完，开头一句让人想看，中间讲今天这个动作，结尾一句引导试玩。`n第三段以【朋友圈】开头，一句话，四十字内，像自己用着随口推荐。`n语气像真人分享，句子里不要用惊叹号，不要用表情符号，不要出现具体形象名字，统一说它。"
  $body = @{
    model = 'glm-4-flash'
    messages = @(
      @{ role = 'system'; content = '你是给一款桌面宠物写宣传文案的人，写得实在、口语、不夸张，不用套话。' },
      @{ role = 'user'; content = $prompt }
    )
    temperature = 0.7
    max_tokens = 900
  } | ConvertTo-Json -Depth 6 -Compress
  $ok = $false
  for ($i = 0; $i -lt 3 -and -not $ok; $i++) {
    try {
      $r = Invoke-RestMethod -Uri 'https://open.bigmodel.cn/api/paas/v4/chat/completions' -Method Post `
        -Headers @{ Authorization = "Bearer $key" } -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 180
      $text = $r.choices[0].message.content.Trim()
      $ok = $true
    } catch {
      Start-Sleep -Seconds 3
    }
  }
  if (-not $ok) { $text = 'AI_FAIL 今天没拿到文案。' }
} else {
  $text = 'KEY_FAIL 没读到 key.txt。'
}

# 清洗：惊叹号、引号、表情符号
$text = $text -replace '！', '。' -replace '!', '。'
$text = $text -replace '"', '' -replace '“', '' -replace '”', '' -replace '「', '' -replace '」', ''
$text = $text -replace '『', '' -replace '』', ''
$text = [regex]::Replace($text, '[\uD800-\uDBFF][\uDC00-\uDFFF]', '')
$text = [regex]::Replace($text, '[\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]', '')
$text = $text -replace '[ \t]{2,}', ' '

# 小红书缺标题时补一行
$lines = $text -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
$built = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
  $built += $lines[$i]
  if ($lines[$i] -match '^【小红书】') {
    if ($i + 1 -lt $lines.Count -and $lines[$i + 1].Trim().Length -gt 25) {
      $built += "标题：$topic"
    }
  }
}
$text = ($built -join "`r`n")

# 前一天配图不重复：从两张主图 + 一张场景挑
$heroKeys = @($HERO.Keys | Sort-Object { Get-Random })
$sceneKeys = @($SCENE.Keys | Sort-Object { Get-Random })
$picked = @($heroKeys[0], $heroKeys[1], $sceneKeys[0])
$names = @()
foreach ($k in $picked) {
  $fn = if ($HERO.ContainsKey($k)) { $HERO[$k] } else { $SCENE[$k] }
  $src = Join-Path $SHOT $fn
  if (Test-Path -LiteralPath $src) {
    try {
      Copy-Item -LiteralPath $src -Destination (Join-Path $dir ($k + '.jpg')) -Force
      $names += ($k + '.jpg')
    } catch {}
  }
}

$text = $text + "`r`n`r`n配图：" + ($names -join '、')
$enc = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $dir '文案.txt'), $text, $enc)
[IO.File]::WriteAllText((Join-Path $OUT '最新.txt'), $text, $enc)
Add-Content -LiteralPath $LOG -Value ((Get-Date -Format 'HH:mm:ss') + ' OK ' + $day) -Encoding utf8
