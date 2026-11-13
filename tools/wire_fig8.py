# 把 8 号银发剑客接进手机端：新增 POSES_8、登记进 POSE_SETS/POSE_KINDS，并换掉走路八帧
import re, io, os

P = r'E:\Daodao\src\桌面分身\dao.html'
FRAG = r'E:\Daodao\tools\_pos8_frag.js'
raw = open(P, encoding='utf-8').read()
frag = open(FRAG, encoding='utf-8').read()
bom = open(P, 'rb').read(3) == b'\xef\xbb\xbf'
print('原文件 BOM', bom, '长度', len(raw))

# 片段拆成两半：POSES_8 和 WALKS_8
i = frag.index('   var WALKS_8')
poses8 = frag[:i].rstrip() + '\n'
walks8 = frag[i:]

# 1) 换掉旧的 WALKS_8 数组（从 var WALKS_8 = [ 到第一个 ];
m = re.search(r'var WALKS_8 = \[.*?\];', raw, re.S)
print('旧 WALKS_8 长度', m.end() - m.start() if m else None)
raw = raw[:m.start()] + walks8.rstrip() + raw[m.end():]

# 2) 在 POSE_SETS 前插入 POSES_8 定义
ps = raw.index('var POSE_SETS = {')
raw = raw[:ps] + poses8 + raw[ps:]

# 3) 登记进 POSE_SETS
raw = raw.replace('var POSE_SETS = { 4: POSES, 7: POSES_7, 11: POSES_11 };',
                  'var POSE_SETS = { 4: POSES, 7: POSES_7, 8: POSES_8, 11: POSES_11 };')

# 4) 今日形象列表加上 8
raw = raw.replace('var POSE_KINDS = [6, 7, 11];', 'var POSE_KINDS = [6, 7, 8, 11];')
raw = raw.replace("else if (TODAY_SP === 11) { POSES = POSES_11; }",
                  "else if (TODAY_SP === 8) { POSES = POSES_8; }\n   else if (TODAY_SP === 11) { POSES = POSES_11; }")

open(P, 'w', encoding='utf-8', newline='\n').write(raw)

chk = open(P, encoding='utf-8').read()
print('POSES_8 定义', chk.count('var POSES_8'), '| POSE_SETS 含 8:', '8: POSES_8' in chk,
      '| KINDS', 'var POSE_KINDS = [6, 7, 8, 11];' in chk,
      '| 分支', 'TODAY_SP === 8' in chk, '| 大小', round(os.path.getsize(P) / 1024 / 1024, 2), 'MB')
print('仍含 手办:', chk.count('手办'))
