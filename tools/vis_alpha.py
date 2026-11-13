# -*- coding: utf-8 -*-
"""把 alpha 通道可视化：透明区涂亮绿，其余保持原样，用来看白底到底在不在图里。"""
from PIL import Image

for i in [0, 2, 11]:
    p = r"E:\Daodao\src\桌面分身\faces_cut4\face_%d.png" % i
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    out = Image.new("RGB", (w, h), (0, 255, 0))
    px = im.load()
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a >= 200:
                op[x, y] = (r, g, b)
            elif a > 0:
                op[x, y] = (255, 140, 0)   # 半透明涂橙
            # a==0 保留绿
    out.save(r"E:\Daodao\_vis_%d.png" % i, "PNG")
    print("OK", i, im.size)
