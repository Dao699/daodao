# -*- coding: utf-8 -*-
"""去 GitHub 看看星标多的项目，挑几个今天还没学过的写进 今日所学.txt。
同一天反复跑的时候是往下追加，不会把上午学的覆盖掉；见过的仓库名不再重复。"""
import json
import os
import random
import re
import urllib.parse
import urllib.request
import datetime

APP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(APP, "今日所学.txt")
KEYFILE = os.path.join(APP, "key.txt")

KEY = ""
try:
    if os.path.exists(KEYFILE):
        with open(KEYFILE, "r", encoding="utf-8", errors="ignore") as f:
            first = f.read().strip().splitlines()
            if first:
                KEY = first[0].strip()
except Exception:
    KEY = ""

# 主题池多放几个，每次随机抽三个，不然每天学到的都是同一批
QUERIES = [
    ("科技", "desktop pet in:name,description"),
    ("工具", "winforms in:name,description"),
    ("学习", "free programming course in:name,description"),
    ("动画", "gdi+ animation in:name,description"),
    ("语音", "text to speech chinese in:name,description"),
    ("安卓", "android sample app in:name,description"),
    ("效率", "powershell module in:name,description"),
    ("游戏", "pixel art game in:name,description"),
    ("绘图", "procedural drawing in:name,description"),
    ("小程序", "python desktop tool in:name,description"),
]

MAX_DAY = 24          # 一天最多留这么多条，免得文件越滚越大


def gh(q, n=8):
    url = ("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q)
           + "&sort=stars&order=desc&per_page=" + str(n))
    req = urllib.request.Request(url, headers={
        "User-Agent": "DaoPet/1.0",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def brain(text):
    if not KEY:
        return ""
    try:
        payload = json.dumps({
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content":
                 "把下面这个 GitHub 项目的介绍翻译成一句中文大白话，不超过 30 个字，不要英文，不要引号，只输出这一句。"},
                {"role": "user", "content": text},
            ],
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            data=payload,
            headers={"Authorization": "Bearer " + KEY,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
        s = d["choices"][0]["message"]["content"].strip()
        s = re.sub(r"[\r\n]+", " ", s).strip('"“” ')
        return s[:46]
    except Exception:
        return ""


def load_today(today):
    """今天的文件才认；不是今天的就当空的，从头记"""
    if not os.path.exists(OUT):
        return []
    try:
        with open(OUT, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f.read().splitlines()]
    except Exception:
        return []
    if not lines or lines[0] != today:
        return []
    return [l for l in lines if "|" in l]


def repo_of(line):
    m = re.search(r"（([^）]+)，", line)
    return m.group(1).strip() if m else ""


def main():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    have = load_today(today)
    if len(have) >= MAX_DAY:
        print("FULL|" + str(len(have)))
        return
    seen = set()
    for ln in have:
        r = repo_of(ln)
        if r:
            seen.add(r)

    picks = random.sample(QUERIES, min(3, len(QUERIES)))
    rows = []
    fail = 0
    for tag, q in picks:
        try:
            data = gh(q)
        except Exception:
            fail += 1
            continue
        for it in (data.get("items") or [])[:3]:
            name = (it.get("full_name") or "").strip()
            if not name or name in seen:
                continue
            stars = int(it.get("stargazers_count") or 0)
            desc = re.sub(r"\s+", " ", (it.get("description") or "")).strip()
            zh = brain(name + " (" + str(stars) + " stars): " + desc) if desc else ""
            if not zh:
                zh = desc[:60] if desc else "最近挺火的一个项目"
            seen.add(name)
            rows.append((tag, zh + "（" + name + "，⭐" + str(stars) + "）"))
            if len(rows) >= 6:
                break
        if len(rows) >= 6:
            break

    if not rows:
        print("EMPTY|fail=" + str(fail))
        return

    lines = [today, "道 · 今天从 GitHub 学到的"]
    lines += have
    for tag, body in rows:
        body = body.replace("|", "/").replace("\r", " ").replace("\n", " ")
        lines.append(tag + "|" + body)
    try:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("\r\n".join(lines) + "\r\n")
    except Exception as e:
        print("WERR|" + str(e))
        return
    print("OK|new=" + str(len(rows)) + "|total=" + str(len(have) + len(rows)))


if __name__ == "__main__":
    main()
