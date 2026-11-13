# -*- coding: utf-8 -*-
from PIL import Image

im = Image.open(r"C:\Users\Administrator\Doubao\chats\2026-11-06\_s_sc9_tea.jpg").convert("RGB")
print("size", im.size)
pts = [(450, 190), (480, 230), (520, 380), (430, 160), (600, 250), (700, 300), (300, 200)]
for p in pts:
    print(p, im.getpixel(p))
