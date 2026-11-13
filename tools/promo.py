# -*- coding: utf-8 -*-
"""每天给「道」生成一份宣传物料：三个平台的文案 + 当天配图。
只用标准库，4GB 老机器也能跑。"""
import json
import os
import random
import re
import ssl
import sys
import time
import urllib.request
from datetime import datetime

APP = r"E:\Daodao"
OUT = os.path.join(APP, "宣传")
SHOT_DIR = r"C:\Users\Administrator\Doubao\chats\2026-11-06"
LOG = os.path.join(OUT, "log.txt")

# 卖点按程序实际能力写，不要吹
POINTS = """1. 12 个形象随机出现：橘猫、赤狐、银发剑客、小机器人、熊猫、汉服女子、紫袍女巫、绿恐龙、企鹅、蓝发双马尾、黑发男孩等
2. 会说话，多套嗓音（男声、女声、萝莉、御姐、机器人腔），早中晚自动把音量压小，不吵人
3. 会背古诗（35 首）、会唱歌（小星星）、会教英语（60 句），还会讲故事、说笑话、念小说
4. 会披着红披风被风吹着飞、会御剑踩剑而行、会骑坐骑赶路、会跳舞、会喝茶喝咖啡（手握着杯子端起来喝）、会看电视、会滑板轮滑
5. 五个场景会自己换：城市车流路灯、乡野田垄、海边日落沙滩、花丛蝴蝶、屋里
6. 接了大模型当导演：你说一句话，它自己判断该干什么，不是死板的关键字
7. 电脑端是单文件 exe，4GB 老笔记本也能跑；手机端有随身版和网页版，电脑手机通着
8. 一块钱就能用"""

TOPICS = [
    "披着红披风被风吹着飞",
    "踩剑而行，御剑飞行",
    "手握着咖啡杯，端起来喝一口",
    "随口背一首古诗",
    "唱歌（小星星）",
    "一句一句教英语",
    "五个场景自动换：城市车流、乡野田垄、海边日落、花丛蝴蝶、屋里",
    "你说一句话，它自己判断该干什么",
    "手机端随身版，电脑手机通着",
    "滑板和轮滑",
    "坐在电视前看电视",
    "跟着节拍跳舞",
]

SHOTS = {    "fly": "_s_cw4_fly.jpg",
    "sword": "_s_cw4_sword.jpg",
    "coffee": "_s_cup4a_tea.jpg",
    "coffee2": "_s_cup4c.jpg",
    "poem": "_s_pm1_poem.jpg",
    "sing": "_s_sg1_sing.jpg",
    "tv": "_s_tv3_tv.jpg",
    "skate": "_s_sk4_skate.jpg",
    "scene": "_s_sc6_walk.jpg",
    "sea": "_s_sc6_fly.jpg",
    "ai": "_s_ai4_fly.jpg",
}


def read_key():
    p = os.path.join(APP, "key.txt")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def ask(prompt, key):
    body = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "system", "content": "你是给一款桌面宠物写宣传文案的人，写得实在、口语、不夸张，不用套话，不加无关话题。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 900,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    ctx = ssl._create_unverified_context()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=150, context=ctx) as r:
                obj = json.loads(r.read().decode("utf-8"))
            return obj["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last = e
            time.sleep(3)
    raise last


def clean(txt, topic):
    txt = txt.replace("！", "。").replace("!", "。")
    txt = txt.replace("“", "").replace("”", "").replace("「", "").replace("」", "")
    txt = txt.replace("『", "").replace("』", "")
    # 模型爱加表情符号，统一清掉
    txt = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u2190-\u21FF]",
                 "", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    lines = [l.rstrip() for l in txt.splitlines()]
    lines = [l for l in lines if l.strip()]
    out = []
    for i, l in enumerate(lines):
        out.append(l)
        # 小红书段：后面第一行太长就当正文，前面补一行标题
        if l.startswith("【小红书】") or l.strip() == "【小红书】":
            if i + 1 < len(lines) and len(lines[i + 1].strip()) > 25:
                out.append("标题：" + topic)
    return "\n".join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    d = os.path.join(OUT, day)
    os.makedirs(d, exist_ok=True)

    line = ""
    key = ""
    try:
        key = read_key()
    except Exception as e:
        line += "KEY_FAIL %s\n" % e
    if key:
        base_day = datetime(2026, 11, 8)
        topic = TOPICS[(datetime.now() - base_day).days % len(TOPICS)]
        prompt = (
            "这是我要宣传的桌面宠物应用「道」，它的真实功能如下：\n" + POINTS +
            "\n\n今天的宣传主题是：" + topic + "，三段都围绕这个主题写。\n"
            "请写三段中文文案，直接给内容，不要解释，不要加方括号之外的标注：\n"
            "第一段以【小红书】开头，下一行是标题（二十字内），再下一行开始是正文（一百到一百五十字），"
            "先讲一个具体的使用场景，再落到今天的主题上，顺带点出一两项别的功能。\n"
            "第二段以【抖音口播】开头，必须是一整段连贯的话，八十到一百字，二十秒能念完，"
            "开头一句让人想看，中间讲今天这个动作，结尾一句引导试玩，不要分成开头结尾两截。\n"
            "第三段以【朋友圈】开头，一句话，四十字内，像自己用着随口推荐。\n"
            "语气像真人分享，句子里不要用惊叹号，不要用表情符号，不要出现具体形象名字，统一说它。"
        )
        try:
            txt = ask(prompt, key)
            txt = clean(txt, topic)
        except Exception as e:
            txt = "AI_FAIL %s\n\n" % e
        line += txt + "\n"
    else:
        line += "今天没拿到文案。\n"

    # 今天的配图：两张最出效果的 + 一张场景
    hero = ["fly", "sword", "coffee", "coffee2", "tv", "poem"]
    scene = ["scene", "sea", "sing", "skate", "ai"]
    picks = random.sample(hero, 2) + random.sample(scene, 1)
    names = []
    for tag in picks:
        fn = SHOTS[tag]
        src = os.path.join(SHOT_DIR, fn)
        if os.path.exists(src):
            dst = os.path.join(d, tag + ".jpg")
            try:
                with open(src, "rb") as a, open(dst, "wb") as b:
                    b.write(a.read())
                names.append(tag + ".jpg")
            except Exception:
                pass
    line += "\n配图：" + "、".join(names) + "\n"

    with open(os.path.join(d, "文案.txt"), "w", encoding="utf-8") as f:
        f.write(line)
    latest = os.path.join(OUT, "最新.txt")
    with open(latest, "w", encoding="utf-8") as f:
        f.write(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("%s OK dir=%s\n" % (time.strftime("%H:%M:%S"), day))
    print("OK " + d)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        os.makedirs(OUT, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s ERR %s\n" % (time.strftime("%H:%M:%S"), e))
        print("ERR " + str(e))
        sys.exit(0)
