# alpha 形态学闭运算：把细发丝之间 1~2 像素的缝合并成整片，颜色不改，只动 alpha
import os
import numpy as np
from PIL import Image


def dilate(m):
    out = m.copy()
    out[1:, :] |= m[:-1, :]
    out[:-1, :] |= m[1:, :]
    out[:, 1:] |= m[:, :-1]
    out[:, :-1] |= m[:, 1:]
    out[1:, 1:] |= m[:-1, :-1]
    return out


def erode(m):
    out = m.copy()
    out[1:, :] &= m[:-1, :]
    out[:-1, :] &= m[1:, :]
    out[:, 1:] &= m[:, :-1]
    out[:, :-1] &= m[:, 1:]
    return out


root = r'E:\Daodao\_待接入形象\12'
for sub, pats in (('_walk8_12', ['walk%d.png' % i for i in range(1, 9)]),
                  ('_poses_dev12', ['stand.png', 'wave.png', 'cheer.png', 'sit.png'])):
    for f in pats:
        p = os.path.join(root, sub, f)
        a = np.array(Image.open(p).convert('RGBA'))
        solid = a[:, :, 3] > 0
        closed = erode(dilate(dilate(solid)))
        # 闭运算只允许往缝里长，不允许吃掉原有的实心
        final = solid | closed
        n_new = int((final & ~solid).sum())
        a2 = a.copy()
        a2[:, :, 3] = np.where(final, 255, 0).astype('uint8')
        Image.fromarray(a2, 'RGBA').save(p)
        semi = int(((a2[:, :, 3] > 0) & (a2[:, :, 3] < 255)).sum())
        print('%s/%s 收口 %d 像素 半透明 %d' % (sub, f, n_new, semi))
print('done')
