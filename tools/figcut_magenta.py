# 品红底 → 精灵帧：色键去背 + 反解品红渗色 + 二值 alpha + 描边 + 底部质心对齐
import io, urllib.request, os, sys
import numpy as np
from PIL import Image

TW, TH = 96, 152
OUTLINE = np.array([26, 34, 74, 255], dtype='uint8')


def load(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=90).read())).convert('RGB')


def key_magenta(cell):
    a = np.array(cell).astype('float32')
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    # 品红判据：R、B 都高，G 明显低
    mag = (R > 120) & (B > 120) & (G < 0.62 * np.minimum(R, B)) & ((np.minimum(R, B) - G) > 45)
    alpha = np.where(mag, 0, 255).astype('uint8')
    rgb = a.copy()
    # 反解渗色：边缘带品红的像素，把 G 抬到 R/B 的水平，紫边就没了
    spill = (alpha > 0) & ((np.minimum(R, B) - G) > 12)
    rgb[..., 1][spill] = np.minimum(255, G[spill] + (np.minimum(R, B)[spill] - G[spill]) * 0.9)
    rgb[..., 0][spill] = np.clip(R[spill] * 0.92, 0, 255)
    rgb[..., 2][spill] = np.clip(B[spill] * 0.92, 0, 255)
    return Image.fromarray(np.dstack([rgb, alpha]).astype('uint8'), 'RGBA')


def holes(mask):
    """被实心围住的透明洞数量（评估有没有把头发抠出洞）"""
    from collections import deque
    h, w = mask.shape
    free = ~mask
    seen = np.zeros_like(free)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if free[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if free[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    enclosed = free & (~seen)
    # 小于 3 像素的小洞算噪点，忽略
    return int(enclosed.sum())


def build(url, tag):
    im = load(url)
    W, H = im.size
    cells = [key_magenta(im.crop((c * W // 2, r * H // 2, (c + 1) * W // 2, (r + 1) * H // 2)))
             for r in range(2) for c in range(2)]
    bbs = [c.getbbox() for c in cells]
    maxW = max(b[2] - b[0] for b in bbs)
    maxH = max(b[3] - b[1] for b in bbs)
    sc = min(TW / maxW, TH / maxH)
    print('%s 统一比例 %.4f' % (tag, sc))

    def place(cell, bb, dy=0):
        fr = cell.crop(bb)
        nw, nh = max(1, round(fr.width * sc)), max(1, round(fr.height * sc))
        fr = fr.resize((nw, nh), Image.LANCZOS)
        arr = np.array(fr)
        band = arr[int(nh * 0.8):, :, 3] > 0
        xs = np.where(band.any(axis=0))[0]
        anc = int(xs.mean()) if xs.size else nw // 2
        cv = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
        cv.paste(fr, (TW // 2 - anc, TH - nh + dy), fr)
        return cv

    def finish(cv):
        a = np.array(cv)
        al = np.where(a[:, :, 3] >= 128, 255, 0).astype('uint8')
        a[:, :, 3] = al
        solid = al > 0
        e = np.zeros_like(solid)
        e[1:, :] |= solid[:-1, :]; e[:-1, :] |= solid[1:, :]
        e[:, 1:] |= solid[:, :-1]; e[:, :-1] |= solid[:, 1:]
        a[e & (~solid)] = OUTLINE
        a[:, :, 3] = np.where(solid, 255, 0).astype('uint8')
        semi = int(((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).sum())
        return Image.fromarray(a, 'RGBA'), semi, solid

    return cells, bbs, place, finish


def run():
    src = r'E:\Daodao\_待接入形象\12'
    for sub in ('_walk8_12', '_poses_dev12'):
        os.makedirs(os.path.join(src, sub), exist_ok=True)

    cells, bbs, place, finish = build('https://aka.doubaocdn.com/s/gncRtQaG8G', '走路图')
    order = [(0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)]
    total = 0
    for i, (ci, dy) in enumerate(order, 1):
        img, semi, solid = finish(place(cells[ci], bbs[ci], -dy) if dy else place(cells[ci], bbs[ci]))
        total += semi
        img.save(os.path.join(src, '_walk8_12', 'walk%d.png' % i))
        print('walk%d 半透明 %d 洞像素 %d' % (i, semi, holes(solid)))
    print('走路八帧半透明合计', total)
    finish(place(cells[1], bbs[1])[0] if False else place(cells[1], bbs[1]))[0].save(
        os.path.join(src, '_poses_dev12', 'stand.png'))

    cells2, bbs2, place2, finish2 = build('https://aka.doubaocdn.com/s/pNkGpMULps', '姿势图')
    names = ['stand', 'wave', 'cheer', 'sit']
    for i, nm in enumerate(names):
        img, semi, solid = finish2(place2(cells2[i], bbs2[i]))
        img.save(os.path.join(src, '_poses_dev12', nm + '.png'))
        print('%s 半透明 %d 洞像素 %d' % (nm, semi, holes(solid)))
    print('done')


run()
