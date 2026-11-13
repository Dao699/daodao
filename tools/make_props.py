# -*- coding: utf-8 -*-
"""给桌面宠物生成两件道具贴图：红披风、横置长剑。
画法要点：4 倍超采样画完再缩，最后把 alpha 二值化，
这样在透明键窗口里贴上去不会出现半透明紫边。
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4  # 超采样倍数


def save_flat(img, path):
    """alpha 二值化后再存，避免半透明像素。"""
    a = np.array(img.getchannel("A"))
    a2 = np.where(a >= 128, 255, 0).astype(np.uint8)
    out = img.copy()
    out.putalpha(Image.fromarray(a2))
    # 完全透明处把颜色也清成纯白，免得描边采样时带出脏色
    arr = np.array(out)
    arr[..., :3] = np.where(arr[..., 3:4] == 0, 255, arr[..., :3])
    Image.fromarray(arr, "RGBA").save(path)
    print(path, Image.fromarray(arr, "RGBA").size)


# ---------------- 披风 ----------------
W, H = 512, 620
w, h = W * SS, H * SS


def cape_pts():
    """披风外形：肩部收窄、下摆张开成 A 字，底边三个大波浪。"""
    pts = []
    # 顶边：从左肩拱到右肩（肩宽 240）
    n = 60
    for i in range(n):
        x = 136 + (376 - 136) * i / (n - 1)
        y = 68 - 12 * math.sin(math.pi * i / (n - 1))
        pts.append((x, y))
    # 右边：从肩弧线外扩到下摆
    n2 = 50
    for i in range(n2):
        t = i / (n2 - 1)
        x = 376 + 90 * (t ** 1.6)
        y = 68 + (552 - 68) * t
        pts.append((x, y))
    # 底边：三个大波浪，从右到左
    n3 = 110
    for i in range(n3):
        t = i / (n3 - 1)
        x = 466 - (466 - 46) * t
        y = 552 + 34 * math.sin(t * math.pi * 3 + 0.6)
        pts.append((x, y))
    # 左边：从下摆收回肩
    n4 = 50
    for i in range(n4):
        t = i / (n4 - 1)
        x = 46 - 90 * (t ** 1.6)
        y = 552 - (552 - 68) * t
        pts.append((x, y))
    return [(x * SS, y * SS) for x, y in pts]


def make_cape(out_path):
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(cape_pts(), fill=255)

    # 竖向渐变：肩亮红，下摆压深
    ys = np.linspace(0, 1, h)[:, None]
    ys = np.repeat(ys, w, axis=1)
    top = np.array([250, 86, 92], dtype=float)
    bot = np.array([150, 20, 40], dtype=float)
    rgb = top[None, None, :] + (bot - top)[None, None, :] * ys[..., None]
    # 两侧压暗，中间留亮，做出布卷起来的立体感
    xs = np.linspace(-1, 1, w)[None, :]
    xs = np.repeat(xs, h, axis=0)
    shade = 1.0 - 0.22 * np.abs(xs) ** 2
    rgb = rgb * shade[..., None]

    color = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    color.putalpha(mask)
    d = ImageDraw.Draw(color)

    # 褶皱：几条顺着垂势的深红/亮红线，往下摆外张
    for sx, drift in ((162, -52), (232, -16), (300, 16), (352, 52)):
        d.line([(sx * SS, 100 * SS), ((sx + drift * 0.45) * SS, 330 * SS),
                ((sx + drift) * SS, 540 * SS)], fill=(168, 34, 48, 255), width=5 * SS)
        d.line([((sx + 9) * SS, 110 * SS), ((sx + drift * 0.45 + 9) * SS, 330 * SS),
                ((sx + drift + 9) * SS, 540 * SS)], fill=(255, 132, 136, 255), width=2 * SS)

    # 左侧布边被卷起来的一道亮边
    d.line([(104 * SS, 130 * SS), (72 * SS, 300 * SS), (62 * SS, 520 * SS)],
           fill=(255, 158, 160, 255), width=3 * SS)

    # 金滚边：用腐蚀求轮廓差
    er = mask.filter(ImageFilter.MinFilter(9 * SS - 1))
    edge = np.array(mask) .astype(np.int16) - np.array(er).astype(np.int16)
    edge_img = Image.fromarray(np.where(edge > 40, 255, 0).astype(np.uint8), "L")
    gold = Image.new("RGBA", (w, h), (255, 206, 118, 255))
    color = Image.composite(gold, color, edge_img)

    # 领口：一条金带 + 两颗扣
    d = ImageDraw.Draw(color)
    d.polygon([(110 * SS, 58 * SS), (402 * SS, 58 * SS), (400 * SS, 80 * SS), (112 * SS, 80 * SS)],
              fill=(255, 208, 120, 255))
    for cx in (134, 378):
        d.ellipse([(cx - 11) * SS, 58 * SS, (cx + 11) * SS, 80 * SS], fill=(250, 196, 96, 255))

    final = color.resize((W, H), Image.LANCZOS)
    save_flat(final, out_path)


# ---------------- 长剑 ----------------
SW, SH = 900, 150


def make_sword(out_path):
    sw, sh = SW * SS, SH * SS
    img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 剑身：靠剑格厚、往剑尖收成一点（贴图缩到屏幕只有十几像素高，太薄会像根签子）
    blade = [(170 * SS, 50 * SS), (812 * SS, 63 * SS), (884 * SS, 75 * SS),
             (812 * SS, 87 * SS), (170 * SS, 100 * SS)]
    d.polygon(blade, fill=(236, 242, 252, 255))
    # 剑身下半压一层钢青，做出刃面
    d.polygon([(172 * SS, 75 * SS), (812 * SS, 75 * SS), (878 * SS, 75 * SS),
               (812 * SS, 87 * SS), (170 * SS, 100 * SS)], fill=(126, 156, 200, 255))
    # 中线高光
    d.line([(180 * SS, 72 * SS), (830 * SS, 74 * SS)], fill=(255, 255, 255, 255), width=4 * SS)
    # 剑身描边
    d.line([(170 * SS, 50 * SS), (812 * SS, 63 * SS), (884 * SS, 75 * SS),
            (812 * SS, 87 * SS), (170 * SS, 100 * SS), (170 * SS, 50 * SS)],
           fill=(74, 96, 140, 255), width=2 * SS)

    # 剑格：金色，上下出角
    d.polygon([(136 * SS, 28 * SS), (180 * SS, 32 * SS), (180 * SS, 118 * SS), (136 * SS, 122 * SS)],
              fill=(228, 178, 74, 255))
    d.line([(136 * SS, 28 * SS), (180 * SS, 32 * SS), (180 * SS, 118 * SS), (136 * SS, 122 * SS)],
           fill=(168, 122, 40, 255), width=2 * SS)

    # 剑柄：铜色，缠两道绳
    d.rectangle([(48 * SS, 62 * SS), (140 * SS, 90 * SS)], fill=(168, 118, 74, 255))
    for sx in (66, 90, 114):
        d.line([(sx * SS, 62 * SS), ((sx + 14) * SS, 90 * SS)], fill=(128, 84, 52, 255), width=3 * SS)
    d.rectangle([(48 * SS, 62 * SS), (140 * SS, 90 * SS)], outline=(110, 72, 44, 255), width=2 * SS)

    # 柄尾红玉
    d.ellipse([(22 * SS, 56 * SS), (52 * SS, 96 * SS)], fill=(240, 84, 96, 255))
    d.ellipse([(30 * SS, 64 * SS), (44 * SS, 78 * SS)], fill=(255, 160, 168, 255))

    final = img.resize((SW, SH), Image.LANCZOS)
    save_flat(final, out_path)


if __name__ == "__main__":
    make_cape(r"E:\Daodao\props_cape.png")
    make_sword(r"E:\Daodao\props_sword.png")
