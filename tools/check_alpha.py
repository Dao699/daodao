# -*- coding: utf-8 -*-
from PIL import Image
import os

for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
    p = r"E:\Daodao\src\桌面分身\faces_cut4\face_%d.png" % i
    if not os.path.exists(p):
        print(i, "MISSING")
        continue
    im = Image.open(p).convert("RGBA")
    a = im.getchannel("A")
    lo, hi = a.getextrema()
    # 四角颜色
    w, h = im.size
    corners = [im.getpixel((2, 2)), im.getpixel((w - 3, 2)), im.getpixel((2, h - 3)), im.getpixel((w - 3, h - 3))]
    print(i, im.size, "alpha", lo, hi, "corners", corners)
