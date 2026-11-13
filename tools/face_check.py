# -*- coding: utf-8 -*-
"""按程序当前使用的归一化坐标，在 12 张形象上画准星，看表情画到哪儿去了。"""
from PIL import Image, ImageDraw

BASE = r"E:\Daodao\src\桌面分身\faces_cut4"
OUT = r"C:\Users\Administrator\Doubao\chats\2026-11-06\face_anchor_check5.png"

FX = [0.485, 0.492, 0.50, 0.465, 0.50, 0.50, 0.486, 0.498, 0.49, 0.50, 0.51, 0.50]
FY = [0.250, 0.248, 0.215, 0.248, 0.203, 0.179, 0.219, 0.285, 0.371, 0.430, 0.254, 0.166]
FW = [0.40, 0.42, 0.46, 0.40, 0.46, 0.42, 0.30, 0.38, 0.16, 0.24, 0.22, 0.40]

cell = 280
cols, rows = 4, 3
sheet = Image.new("RGB", (cols * cell, rows * cell), (248, 248, 248))
d = ImageDraw.Draw(sheet)

for i in range(12):
    im = Image.open(BASE + r"\face_%d.png" % i).convert("RGBA")
    sc = min((cell - 16) / im.width, (cell - 20) / im.height)
    im2 = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    ox = (i % cols) * cell + (cell - im2.width) // 2
    oy = (i // cols) * cell + (cell - im2.height) // 2 + 14
    bg = Image.new("RGB", im2.size, (255, 255, 255))
    bg.paste(im2, (0, 0), im2)
    sheet.paste(bg, (ox, oy))
    cx = ox + int(FX[i] * im2.width)
    cy = oy + int(FY[i] * im2.height)
    fr = FW[i] * im2.width / 2
    d.line([(cx - 18, cy), (cx + 18, cy)], fill=(255, 0, 0), width=2)
    d.line([(cx, cy - 18), (cx, cy + 18)], fill=(255, 0, 0), width=2)
    d.ellipse([cx - fr, cy - fr * 0.34, cx + fr, cy + fr * 0.52], outline=(0, 110, 255), width=2)
    d.text((ox + 4, oy - 13), "#%d" % i, fill=(20, 20, 20))

sheet.save(OUT)
print("saved %s %dx%d" % (OUT, sheet.width, sheet.height))
