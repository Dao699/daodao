from PIL import Image
import numpy as np, time, os

sp = r'E:\Daodao\src\桌面分身\_poses_dev8\stand.png'
dmp = r'E:\Daodao\src\桌面分身\selfcheck_p8_stand.png'
mt1 = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(sp)))
mt2 = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(dmp)))
print('stand.png', mt1)
print('dump', mt2)

a = np.array(Image.open(sp).convert('RGBA')).astype(int)
solid = a[:, :, 3] > 0
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
pink = (np.minimum(R, B) - G) > 25
n1 = int((solid & pink).sum())
print('素材实心', int(solid.sum()), '粉像素', n1)

b = np.array(Image.open(dmp).convert('RGB')).astype(int)
m = ~((b[:, :, 0] > 240) & (b[:, :, 1] < 25) & (b[:, :, 2] > 240))
Rb, Gb, Bb = b[:, :, 0], b[:, :, 1], b[:, :, 2]
pb = (np.minimum(Rb, Bb) - Gb) > 25
n2 = int((m & pb).sum())
print('dump非背景', int(m.sum()), '粉像素', n2)
ys, xs = np.where(m)
print('dump bbox', xs.min(), ys.min(), xs.max(), ys.max(), b.shape)
