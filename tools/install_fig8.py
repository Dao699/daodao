# 把剑客的 5 张姿势 + 8 帧走路装进源码：本地做白边祛除，并生成手机端要用的 base64 片段
import os, base64, shutil
import numpy as np
from PIL import Image

STAGE = r'E:\Daodao\_待接入形象\12'
POSE_SRC = os.path.join(STAGE, '_poses_dev12')
WALK_SRC = os.path.join(STAGE, '_walk8_12')
SRC = r'E:\Daodao\src\桌面分身'
POSE_DST = os.path.join(SRC, '_poses_dev8')
WALK_DST = os.path.join(SRC, '_walk8_8')
OUTLINE = np.array([26, 34, 74, 255], dtype='uint8')

os.makedirs(POSE_DST, exist_ok=True)
if os.path.isdir(WALK_DST) and not os.path.exists(WALK_DST + '.v25.bak'):
    shutil.copytree(WALK_DST, WALK_DST + '.v25.bak')
os.makedirs(WALK_DST, exist_ok=True)


def despill_and_binarize(im):
    a = np.array(im.convert('RGBA')).copy()
    al = np.where(a[:, :, 3] >= 128, 255, 0).astype('uint8')
    a[:, :, 3] = al
    solid = al > 0
    er = solid.copy()
    for _ in range(2):
        e2 = er.copy()
        e2[1:, :] &= er[:-1, :]
        e2[:-1, :] &= er[1:, :]
        e2[:, 1:] &= er[:, :-1]
        e2[:, :-1] &= er[:, 1:]
        er = e2
    out = a.copy()
    edge = solid & (~er)
    H, W = solid.shape
    for y, x in zip(*np.where(edge)):
        px = out[max(0, y - 3):min(H, y + 4), max(0, x - 3):min(W, x + 4), :3][
            er[max(0, y - 3):min(H, y + 4), max(0, x - 3):min(W, x + 4)]]
        if len(px):
            out[y, x, :3] = np.median(px, axis=0)
    e = np.zeros_like(solid)
    e[1:, :] |= solid[:-1, :]
    e[:-1, :] |= solid[1:, :]
    e[:, 1:] |= solid[:, :-1]
    e[:, :-1] |= solid[:, 1:]
    out[e & (~solid)] = OUTLINE
    out[:, :, 3] = np.where(solid, 255, 0).astype('uint8')
    return Image.fromarray(out, 'RGBA')


poses = {}
for nm in ('stand', 'wave', 'cheer', 'sit', 'walk'):
    im = Image.open(os.path.join(POSE_SRC, nm + '.png'))
    out = despill_and_binarize(im)
    out.save(os.path.join(POSE_DST, nm + '.png'))
    poses[nm] = (np.array(out)[:, :, 3] > 0).sum()
    print('pose %s 不透明像素 %d' % (nm, poses[nm]))

walks = []
for i in range(1, 9):
    im = Image.open(os.path.join(WALK_SRC, 'walk%d.png' % i))
    out = despill_and_binarize(im)
    out.save(os.path.join(WALK_DST, 'walk%d.png' % i))
    walks.append(base64.b64encode(open(os.path.join(WALK_DST, 'walk%d.png' % i), 'rb').read()).decode('ascii'))
print('八帧已写入 _walk8_8')

# 手机端要的片段
order = ['stand', 'wave', 'walk', 'cheer', 'sit']
frag = '   var POSES_8 = [\n'
for nm in order:
    b = base64.b64encode(open(os.path.join(POSE_DST, nm + '.png'), 'rb').read()).decode('ascii')
    frag += '     "data:image/png;base64,%s"' % b
    frag += ',\n' if nm != order[-1] else '\n'
frag += '   ];\n'

walkfrag = '   var WALKS_8 = [\n'
for i, b in enumerate(walks):
    walkfrag += '     "data:image/png;base64,%s"' % b
    walkfrag += ',\n' if i < 7 else '\n'
walkfrag += '   ];\n'

open(r'E:\Daodao\tools\_pos8_frag.js', 'w', encoding='utf-8').write(frag + '\n' + walkfrag)
print('片段长度 %d / %d' % (len(frag), len(walkfrag)))
