# 把精灵图内部被围住的透明缝隙补实（发缝透底色 → 补成实心），轮廓不变
import os, sys
from collections import deque
import numpy as np
from PIL import Image


def enclosed(free):
    h, w = free.shape
    seen = np.zeros_like(free, dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if free[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if free[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return free & (~seen)


def fill(path):
    im = Image.open(path).convert('RGBA')
    a = np.array(im)
    solid = a[:, :, 3] > 0
    hole = enclosed(~solid)
    n = int(hole.sum())
    if n == 0:
        return 0
    # 从实心向内一层层长，颜色取四邻实心均值，几轮就把缝填实
    work = a.astype('float32')
    cur = solid.copy()
    for _ in range(40):
        if not (hole & ~cur).any():
            break
        grown = cur.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            src = np.roll(cur, (dy, dx), axis=(0, 1))
            col = np.roll(work[:, :, :3], (dy, dx), axis=(0, 1))
            cand = (hole & ~cur & src)
            work[:, :, :3][cand] = col[cand]
            grown |= cand
        cur = grown
    a2 = np.zeros_like(a)
    a2[:, :, :3] = work[:, :, :3].astype('uint8')
    a2[:, :, 3] = np.where(solid | hole, 255, 0).astype('uint8')
    Image.fromarray(a2, 'RGBA').save(path)
    return n


root = r'E:\Daodao\_待接入形象\12'
tot = 0
for sub, pats in (('_walk8_12', ['walk%d.png' % i for i in range(1, 9)]),
                  ('_poses_dev12', ['stand.png', 'wave.png', 'cheer.png', 'sit.png'])):
    for f in pats:
        p = os.path.join(root, sub, f)
        k = fill(p)
        tot += k
        print('%s/%s 补缝 %d 像素' % (sub, f, k))
print('合计补缝', tot)
