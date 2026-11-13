# 四宫格 → 八帧走路（逐格处理：本格泛洪去白底 + 只在脚下 25% 去浅白影子；底部接触区质心做水平锚点）
import io, os, urllib.request
from PIL import Image, ImageDraw
import numpy as np

URL = 'https://aka.doubaocdn.com/s/07CVXkHBRf'
STAGE = r'E:\Daodao\_待接入形象\12'
OUT = os.path.join(STAGE, '_walk8_12')
POSE = os.path.join(STAGE, '_poses_dev12')
TW, TH = 96, 152
OUTLINE = np.array([26, 34, 74, 255], dtype='uint8')
os.makedirs(OUT, exist_ok=True)
os.makedirs(POSE, exist_ok=True)

req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert('RGB')
W, H = im.size
print('源图', W, H)

def cut_cell(rgb_img):
    w, h = rgb_img.size
    f = rgb_img.copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        try:
            ImageDraw.floodfill(f, seed, (255, 0, 255), thresh=32)
        except Exception:
            pass
    a = np.array(f)
    filled = (a[:, :, 0] > 245) & (a[:, :, 1] < 15) & (a[:, :, 2] > 245)
    rgb = np.array(rgb_img).astype('float32')
    mx = rgb.max(axis=2); mn = rgb.min(axis=2)
    # 只在本格下方 25% 去掉浅白地面影子，头顶白发在这一带之外
    light = (mx > 190) & ((mx - mn) < 26)
    light[: int(h * 0.75), :] = False
    mask = filled | light
    rgba = np.dstack([np.array(rgb_img), np.where(mask, 0, 255).astype('uint8')])
    return Image.fromarray(rgba, 'RGBA')

cells = []
for row in range(2):
    for col in range(2):
        c = im.crop((col * W // 2, row * H // 2, (col + 1) * W // 2, (row + 1) * H // 2))
        cells.append(cut_cell(c))

bboxes = [c.getbbox() for c in cells]
maxW = max(b[2] - b[0] for b in bboxes)
maxH = max(b[3] - b[1] for b in bboxes)
sc = min(TW / maxW, TH / maxH)
print('统一比例', round(sc, 4))

def place(cell, bb, dy=0):
    fr = cell.crop(bb)
    nw, nh = max(1, int(round(fr.width * sc))), max(1, int(round(fr.height * sc)))
    fr = fr.resize((nw, nh), Image.LANCZOS)
    arr = np.array(fr)
    band = arr[int(nh * 0.8):, :, 3] > 0
    xs = np.where(band.any(axis=0))[0]
    anchor = int(xs.mean()) if xs.size else nw // 2
    cv = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
    cv.paste(fr, (TW // 2 - anchor, TH - nh + dy), fr)
    return cv

def finish(img0):
    arr = np.array(img0)
    al = np.where(arr[:, :, 3] >= 128, 255, 0).astype('uint8')
    arr[:, :, 3] = al
    solid = al > 0
    e = np.zeros_like(solid)
    e[1:, :] |= solid[:-1, :]; e[:-1, :] |= solid[1:, :]
    e[:, 1:] |= solid[:, :-1]; e[:, :-1] |= solid[:, 1:]
    arr[e & (~solid)] = OUTLINE
    arr[:, :, 3] = np.where(arr[:, :, 3] >= 128, 255, 0).astype('uint8')
    semi = int(((arr[:, :, 3] > 0) & (arr[:, :, 3] < 255)).sum())
    return Image.fromarray(arr, 'RGBA'), semi

base4 = [place(cells[i], bboxes[i]) for i in range(4)]
order = [(0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)]
total = 0
frames = []
for idx, (ci, dy) in enumerate(order, start=1):
    src = base4[ci] if dy == 0 else place(cells[ci], bboxes[ci], -dy)
    out, semi = finish(src)
    total += semi
    frames.append(out)
    out.save(os.path.join(OUT, 'walk%d.png' % idx))
    print('walk%d 半透明 %d' % (idx, semi))

frames[2].save(os.path.join(POSE, 'stand.png'))
frames[0].save(os.path.join(POSE, 'walk.png'))
print('总半透明', total)
for i in range(8):
    a1 = np.array(frames[i]).astype('int16'); a2 = np.array(frames[(i + 1) % 8]).astype('int16')
    print('帧%d→%d 差异 %d' % (i + 1, (i + 1) % 8 + 1, int((np.abs(a1 - a2).sum(axis=2) > 12).sum())))
