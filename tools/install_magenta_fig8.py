# 品红底新素材装进源码并写回手机端（替换已有的 POSES_8 / WALKS_8 内容）
import os, re, base64, shutil
import numpy as np
from PIL import Image

STAGE = r'E:\Daodao\_待接入形象\12'
POSES_DIR = os.path.join(STAGE, '_poses_dev12')
WALKS_DIR = os.path.join(STAGE, '_walk8_12')
SRC = r'E:\Daodao\src\桌面分身'
POSE_DST = os.path.join(SRC, '_poses_dev8')
WALK_DST = os.path.join(SRC, '_walk8_8')

os.makedirs(POSE_DST, exist_ok=True)
os.makedirs(WALK_DST, exist_ok=True)

# 走路第一帧当作“走路姿势”
shutil.copy(os.path.join(WALKS_DIR, 'walk1.png'), os.path.join(POSE_DST, 'walk.png'))
for nm in ('stand', 'wave', 'cheer', 'sit'):
    shutil.copy(os.path.join(POSES_DIR, nm + '.png'), os.path.join(POSE_DST, nm + '.png'))
for i in range(1, 9):
    shutil.copy(os.path.join(WALKS_DIR, 'walk%d.png' % i), os.path.join(WALK_DST, 'walk%d.png' % i))

order = ['stand', 'wave', 'walk', 'cheer', 'sit']
poses_js = '   var POSES_8 = [\n'
for i, nm in enumerate(order):
    b = base64.b64encode(open(os.path.join(POSE_DST, nm + '.png'), 'rb').read()).decode('ascii')
    poses_js += '     "data:image/png;base64,%s"' % b + (',\n' if i < len(order) - 1 else '\n')
poses_js += '   ];'

walks_js = '   var WALKS_8 = [\n'
for i in range(1, 9):
    b = base64.b64encode(open(os.path.join(WALK_DST, 'walk%d.png' % i), 'rb').read()).decode('ascii')
    walks_js += '     "data:image/png;base64,%s"' % b + (',\n' if i < 7 else '\n')
walks_js += '   ];'

P = os.path.join(SRC, 'dao.html')
raw = open(P, encoding='utf-8').read()
n_pos = len(re.findall(r'var POSES_8 = \[.*?\];', raw, re.S))
n_walk = len(re.findall(r'var WALKS_8 = \[.*?\];', raw, re.S))
print('替换前 POSES_8=%d WALKS_8=%d' % (n_pos, n_walk))
raw = re.sub(r'var POSES_8 = \[.*?\];', lambda m: poses_js, raw, count=1, flags=re.S)
raw = re.sub(r'var WALKS_8 = \[.*?\];', lambda m: walks_js, raw, count=1, flags=re.S)
open(P, 'w', encoding='utf-8', newline='\n').write(raw)
shutil.copy(P, r'E:\Daodao\道-随身版.html')

chk = open(P, encoding='utf-8').read()
print('替换后 POSES_8=%d WALKS_8=%d 大小 %.2fMB' % (
    len(re.findall(r'var POSES_8 = \[.*?\];', chk, re.S)),
    len(re.findall(r'var WALKS_8 = \[.*?\];', chk, re.S)),
    os.path.getsize(P) / 1024 / 1024))
print('手办残留', chk.count('手办'))
