# -*- coding: utf-8 -*-
"""场景背景按窗口 380x205 预先缩好（2 倍像素用于高 DPI），程序里 1:1 贴，避免运行时插值。"""
from PIL import Image

W, H = 380, 205
SRC = [
    ("scene_city.png", "scene_city_s.png"),
    ("scene_field.png", "scene_field_s.png"),
    ("scene_sea.png", "scene_sea_s.png"),
    ("scene_flower.png", "scene_flower_s.png"),
    ("scene_xianxia.png", "scene_xianxia_s.png"),
    ("scene_home.png", "scene_home_s.png"),
]

for src, dst in SRC:
    im = Image.open(r"E:\Daodao\\" + src).convert("RGB")
    # 按目标比例居中裁切，避免拉伸变形
    tr = W / H
    r = im.width / im.height
    if r > tr:
        nw = int(im.height * tr)
        left = (im.width - nw) // 2
        im = im.crop((left, 0, left + nw, im.height))
    else:
        nh = int(im.width / tr)
        top = int((im.height - nh) * 0.62)   # 略偏下取，保住地面
        im = im.crop((0, top, im.width, top + nh))
    im = im.resize((W, H), Image.LANCZOS)
    im.save(r"E:\Daodao\\" + dst, "PNG")
    print("OK", dst, im.width, im.height)
