# -*- coding: utf-8 -*-
"""12 张形象拼成一张：透明区涂绿，一眼看出哪张还带白底。"""
from PIL import Image

cols = 6
cw, ch = 180, 260
rows = 2
out = Image.new("RGB", (cols * cw, rows * ch), (0, 0, 0))
for i in range(12):
    p = r"E:\Daodao\src\桌面分身\faces_cut4\face_%d.png" % i
    im = Image.open(p).convert("RGBA")
    im.thumbnail((cw - 8, ch - 8), Image.LANCZOS)
    tile = Image.new("RGB", (cw - 4, ch - 4), (0, 255, 0))
    px = im.load()
    op = tile.load()
    ox = (cw - 4 - im.width) // 2
    oy = (ch - 4 - im.height) // 2
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a >= 200:
                op[ox + x, oy + y] = (r, g, b)
    col = i % cols
    row = i // cols
    out.paste(tile, (col * cw + 2, row * ch + 2))
out.save(r"E:\Daodao\_vis_all.png", "PNG")
print("OK")
