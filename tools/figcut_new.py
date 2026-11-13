# 一行八格走路表 → 8 张 96x152 精灵帧（按列投影找角色，全局同倍数缩放，底部对齐）
import os, io, urllib.request, sys
from PIL import Image
import numpy as np

URL = 'https://aka.doubaocdn.com/s/LRiAhJE4c5'
OUT_DIR = r'E:\Daodao\src\桌面分身\_walk8_12'
POSES_DIR = r'E:\Daodao\src\桌面分身\_poses_dev12'
TARGET_W, TARGET_H = 96, 152
KEY = np.array([255, 0, 255], dtype=np.float32)
OUTLINE = np.array([26, 34, 74, 255], dtype=np.uint8)

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(POSES_DIR, exist_ok=True)

req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
src = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert('RGBA')
W, H = src.size
print('源图', W, H)

a = np.array(src).astype(np.int16)
rgb = a[:, :, :3].astype(np.float32)
dist = np.sqrt(((rgb - KEY) ** 2).sum(axis=2))
keyed = (dist < 110) | ((a[:, :, 0] > 140) & (a[:, :, 2] > 140) & (a[:, :, 1] < 115))

alpha = np.where(keyed, 0, 255).astype(np.uint8)
spill = (~keyed) & ((a[:, :, 0] - a[:, :, 1] > 35) & (a[:, :, 2] - a[:, :, 1] > 35))
a[:, :, 0][spill] = np.minimum(a[:, :, 1][spill] + 12, 255)
a[:, :, 2][spill] = np.minimum(a[:, :, 1][spill] + 12, 255)
a[:, :, 3] = alpha
img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

# 列投影：每列有多少不透明像素
mask = np.array(img)[:, :, 3] > 0
colsum = mask.sum(axis=0)
runs, cur = [], None
for x in range(W):
    if colsum[x] > 3:
        if cur is None: cur = x
    else:
        if cur is not None:
            if x - cur > 8: runs.append((cur, x - 1))
            cur = None
if cur is not None: runs.append((cur, W - 1))
print('找到角色段', len(runs), runs[:12])
if len(runs) != 8:
    print('段数不是 8，先退出'); sys.exit(2)

boxes = []
for (x0, x1) in runs:
    sub = mask[:, x0:x1 + 1]
    rows = np.where(sub.sum(axis=1) > 0)[0]
    boxes.append((x0, int(rows.min()), x1 + 1, int(rows.max()) + 1))

maxW = max(b[2] - b[0] for b in boxes)
maxH = max(b[3] - b[1] for b in boxes)
sc = min(TARGET_W / maxW, TARGET_H / maxH)
print('最大', maxW, maxH, '统一比例', round(sc, 4))

def finish(im):
    arr = np.array(im)
    al = np.where(arr[:, :, 3] >= 128, 255, 0).astype(np.uint8)
    arr[:, :, 3] = al
    solid = al > 0
    edge = np.zeros_like(solid)
    edge[1:, :] |= solid[:-1, :]
    edge[:-1, :] |= solid[1:, :]
    edge[:, 1:] |= solid[:, :-1]
    edge[:, :-1] |= solid[:, 1:]
    ring = edge & (~solid)
    arr[ring] = OUTLINE
    arr[:, :, 3] = np.where(arr[:, :, 3] >= 128, 255, 0).astype(np.uint8)
    semi = int(((arr[:, :, 3] > 0) & (arr[:, :, 3] < 255)).sum())
    return Image.fromarray(arr, 'RGBA'), semi

total = 0
frames = []
for i, b in enumerate(boxes, start=1):
    fr = img.crop(b)
    nw, nh = max(1, int(round(fr.width * sc))), max(1, int(round(fr.height * sc)))
    fr = fr.resize((nw, nh), Image.LANCZOS)
    cv = Image.new('RGBA', (TARGET_W, TARGET_H), (0, 0, 0, 0))
    cv.paste(fr, ((TARGET_W - nw) // 2, TARGET_H - nh), fr)
    out, semi = finish(cv)
    total += semi
    frames.append(out)
    out.save(os.path.join(OUT_DIR, 'walk%d.png' % i))
    print('walk%d 尺寸 %dx%d 半透明 %d' % (i, nw, nh, semi))

frames[3].save(os.path.join(POSES_DIR, 'stand.png'))
print('总半透明像素', total)
