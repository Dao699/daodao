# -*- coding: utf-8 -*-
"""把模型生成的披风/长剑白底图抠成透明底，裁紧凑，缩放，alpha 二值化。"""
from collections import deque
import numpy as np
from PIL import Image


def cut(path, out_path, target_w=None, target_h=None):
    im = Image.open(path).convert("RGB")
    a = np.array(im).astype(np.int16)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    # 背景判定：够亮而且几乎不发色（纯白/灰白）
    white = (mn >= 222) & ((mx - mn) <= 18)
    H, W = white.shape
    bg = np.zeros((H, W), bool)
    dq = deque()
    for x in range(W):
        for y in (0, H - 1):
            if white[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if white[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and white[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                dq.append((ny, nx))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([np.array(im), alpha]), "RGBA")
    bb = img.getchannel("A").getbbox()
    if bb:
        img = img.crop(bb)
    if target_h:
        tw = max(1, int(img.width * target_h / img.height))
        img = img.resize((tw, target_h), Image.LANCZOS)
    elif target_w:
        th = max(1, int(img.height * target_w / img.width))
        img = img.resize((target_w, th), Image.LANCZOS)
    arr = np.array(img)
    a2 = np.where(arr[..., 3] >= 128, 255, 0).astype(np.uint8)
    # 暗部提亮：AI 图的下半幅是深红阴影，贴到窗口里跟壁纸颜色糊成一块
    rgb = arr[..., :3].astype(np.float32) / 255.0
    rgb = np.power(rgb, 0.82) * 255.0
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    arr[..., :3] = np.where(a2[..., None] == 0, 255, rgb)
    img = Image.fromarray(np.dstack([arr[..., :3], a2]).astype(np.uint8), "RGBA")
    img.save(out_path)
    print(out_path, img.size, "alpha0=", int((a2 == 0).sum()))


if __name__ == "__main__":
    cut(r"E:\Daodao\raw_cape.png", r"E:\Daodao\props_cape.png", target_h=760)
    cut(r"E:\Daodao\raw_sword.png", r"E:\Daodao\props_sword.png", target_w=1200)
    cut(r"E:\Daodao\raw_capewind.png", r"E:\Daodao\props_capewind.png", target_w=1200)
