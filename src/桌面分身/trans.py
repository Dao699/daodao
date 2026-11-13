import sys, re, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def lookup(text):
    url = "https://cn.bing.com/dict/search?q=" + urllib.parse.quote(text)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        html = r.read().decode("utf-8", errors="ignore")
    m = re.search(r'<meta name="description" content="([^"]+)"', html)
    if not m:
        return None
    desc = m.group(1)
    if "必应词典" not in desc:
        return None
    # 去掉前缀
    desc = re.sub(r'^必应词典为您提供.*?的释义[，,]?', '', desc)
    # 去掉音标/拼音
    desc = re.sub(r'[英美]\[[^\]]*\]', '', desc)
    desc = re.sub(r'拼音\[[^\]]*\]', '', desc)
    desc = desc.strip(" ；;，,")

    net = ""
    mi = desc.find("网络释义")
    if mi >= 0:
        net = desc[mi + 4:].lstrip(" ：:").strip(" ；;，,")
        desc = desc[:mi].strip(" ；;，,")

    std = desc.strip()
    # 标准释义里清掉词性标记，只留中文/英文词条
    if std:
        return std, net
    if net:
        return net, ""
    return None, None


def pick(text):
    r = lookup(text)
    if r is None:
        return None
    std, net = r
    if std:
        # 只保留第一组
        first = re.split(r'[；;]', std)[0].strip()
        # 去掉开头的词性缩写，如 int. na. n. v.
        first = re.sub(r'^[a-zA-Z]{1,5}\.\s*', '', first).strip()
        if first:
            return first
    if net:
        first = re.split(r'[；;]', net)[0].strip()
        if first:
            return first
    return None


def main():
    if len(sys.argv) < 2:
        print("")
        return
    text = sys.argv[1].strip()
    if not text:
        print("")
        return
    try:
        out = pick(text)
    except Exception:
        out = None
    print(out if out else "")


if __name__ == "__main__":
    main()
