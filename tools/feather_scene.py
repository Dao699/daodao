# -*- coding: utf-8 -*-
"""场景图不做柔边（透明键窗口里半透明会被染成洋红），改成"不规则硬边"轮廓：
上缘走一道波浪，四角收圆，下面直着贴住桌面。贴出来是一片景，不是一块长方形画框。
alpha 只有 0 或 255，一个中间值都不留。
"""
import numpy as np
from PIL import Image

W, H = 380, 205

def build_mask(indoor=False):
    m = np.zeros((H, W), dtype=bool)
    xs = np.arange(W)
    if indoor:
        # 屋里本来就是个方方正正的房间，不做波浪，只把四角轻轻收圆
        m[:] = True
        r = 14
    else:
        # 上缘：两条正弦叠一道缓弯，看着像云边/山脊，不像一条直边
        y0 = 12.0 + 5.0 * np.sin(2.3 * np.pi * xs / W) + 3.0 * np.sin(5.4 * np.pi * xs / W + 1.1)
        for x in range(W):
            top = int(round(y0[x]))
            m[max(0, top):, x] = True
        r = 16
    # 四条角切圆，免得四个尖角太硬
    yy, xx = np.mgrid[0:H, 0:W]
    for cy, cx, sy, sx in [(0, 0, 1, 1), (0, W - 1, 1, -1), (H - 1, 0, -1, 1), (H - 1, W - 1, -1, -1)]:
        inside_corner = (sy * (yy - cy) < r) & (sx * (xx - cx) < r)
        d = np.sqrt(((yy - cy) * 1.0) ** 2 + ((xx - cx) * 1.0) ** 2)
        m[inside_corner & (d > r)] = False
    return m

masks = {"indoor": build_mask(True), "outdoor": build_mask(False)}

SRC = [
    ("scene_city_s.png", "outdoor"),
    ("scene_field_s.png", "outdoor"),
    ("scene_sea_s.png", "outdoor"),
    ("scene_flower_s.png", "outdoor"),
    ("scene_xianxia_s.png", "outdoor"),
    ("scene_home_s.png", "indoor"),
]

for name, kind in SRC:
    mask = masks[kind]
    alpha = np.where(mask, 255, 0).astype(np.uint8)
    src = "E:\\Daodao\\" + name
    dst = src.replace("_s.png", "_v.png")
    im = Image.open(src).convert("RGBA")
    arr = np.array(im)
    arr[:, :, 3] = alpha
    Image.fromarray(arr, "RGBA").save(dst, "PNG")
    print("OK", dst, kind, "solid%=", round(mask.sum() * 100.0 / (W * H), 1))
