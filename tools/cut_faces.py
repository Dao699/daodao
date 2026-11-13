# -*- coding: utf-8 -*-
"""对 12 张形象图做四边泛洪去白底：只吃“与图像边缘连通、且接近纯白”的区域，
角色身体内部的白色（比如机器人）因为被轮廓隔开，不会被吃掉。"""
from PIL import Image
from collections import deque
import os

SRC = r"E:\Daodao\src\桌面分身\faces_cut4"
DST = r"E:\Daodao\src\桌面分身\faces_cut5"
os.makedirs(DST, exist_ok=True)


def near_white(p):
    r, g, b, a = p
    if a < 20:
        return False
    mn = min(r, g, b)
    mx = max(r, g, b)
    return mn >= 222 and (mx - mn) <= 18


for i in range(12):
    p = os.path.join(SRC, "face_%d.png" % i)
    if not os.path.exists(p):
        print(i, "MISSING")
        continue
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()

    def push(x, y):
        if 0 <= x < w and 0 <= y < h:
            k = y * w + x
            if not seen[k]:
                seen[k] = 1
                if near_white(px[x, y]):
                    q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    removed = 0
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        removed += 1
        push(x + 1, y)
        push(x - 1, y)
        push(x, y + 1)
        push(x, y - 1)

    im.save(os.path.join(DST, "face_%d.png" % i), "PNG")
    print(i, im.size, "removed", removed)
