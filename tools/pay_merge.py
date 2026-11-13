# -*- coding: utf-8 -*-
"""把微信、支付宝两张收款码拼成一张竖版收款图，尺寸按社媒习惯。"""
from PIL import Image, ImageDraw

W = 1080
GAP = 24
PAD = 24
BG = (250, 250, 251)

wx = Image.open(r"E:\Daodao\pay_wx.png").convert("RGB")
zfb = Image.open(r"E:\Daodao\pay_zfb.png").convert("RGB")

# 并排：各占一半宽度
half = (W - PAD * 3) // 2
def fit(im, w):
    h = int(im.height * w / im.width)
    return im.resize((w, h), Image.LANCZOS)

a = fit(wx, half)
b = fit(zfb, half)
H = max(a.height, b.height) + PAD * 2

canvas = Image.new("RGB", (W, H), BG)
canvas.paste(a, (PAD, PAD))
canvas.paste(b, (PAD * 2 + half, PAD))

d = ImageDraw.Draw(canvas)
d.rectangle([0, 0, W - 1, H - 1], outline=(226, 228, 233))
out = r"E:\Daodao\宣传\收款码.png"
canvas.save(out, "PNG")
print("OK %s %dx%d" % (out, canvas.width, canvas.height))
