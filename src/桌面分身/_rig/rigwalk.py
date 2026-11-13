# -*- coding: utf-8 -*-
"""用一套极简骨骼 + 正交投影，逐帧算出 8 帧走路，关节角度由相位决定，不再让 AI 猜四肢。"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 384, 608
S = 360.0            # 每单位多少像素
CX, CY = 0.52 * W, 0.92 * H   # 脚底大约落在哪

D2R = math.radians

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)

class Node:
    """一个关节：局部坐标里带着静态偏移，再绕自己的轴转。"""
    def __init__(self, pos=(0, 0, 0), rot=None):
        self.pos = np.array(pos, float)
        self.rot = rot if rot is not None else np.eye(3)

class Costume:
    def __init__(self):
        # 颜色（平涂 + 兰伯特光）
        self.skin = (240, 205, 180)
        self.hair = (236, 235, 228)
        self.robe = (38, 53, 92)
        self.robe2 = (52, 73, 120)
        self.sash = (150, 60, 46)
        self.boot = (42, 40, 50)
        self.steel = (196, 205, 214)
        self.hilt = (118, 82, 46)

SH = Costume()

def box(center, size):
    cx, cy, cz = center
    sx, sy, sz = size
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    v = np.array([
        [cx - hx, cy - hy, cz - hz], [cx + hx, cy - hy, cz - hz],
        [cx + hx, cy + hy, cz - hz], [cx - hx, cy + hy, cz - hz],
        [cx - hx, cy - hy, cz + hz], [cx + hx, cy - hy, cz + hz],
        [cx + hx, cy + hy, cz + hz], [cx - hx, cy + hy, cz + hz],
    ], float)
    quads = [(0, 1, 2, 3), (5, 4, 7, 6), (1, 5, 6, 2), (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)]
    return v, quads

def frustum(y0, y1, w0, d0, w1, d1):
    """上窄下宽的裙摆/袖子，y0 在下、y1 在上。"""
    v = np.array([
        [-w0, y0, -d0], [w0, y0, -d0], [w1, y1, -d1], [-w1, y1, -d1],
        [-w0, y0, d0], [w0, y0, d0], [w1, y1, d1], [-w1, y1, d1],
    ], float)
    quads = [(0, 1, 2, 3), (5, 4, 7, 6), (1, 5, 6, 2), (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)]
    return v, quads

def place(verts, M=np.eye(3), t=(0, 0, 0)):
    return (verts @ M.T) + np.array(t, float)

def shade(faces, base, light=np.array([-0.34, 0.66, -0.66])):
    light = light / np.linalg.norm(light)
    cols = []
    for f in faces:
        n = np.cross(f[1] - f[0], f[2] - f[0])
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            k = 0.8
        else:
            n = n / ln
            k = 0.40 + 0.62 * max(0.0, float(np.dot(n, light))) + 0.10 * abs(float(np.dot(n, [0, 0, 1])))
        cols.append(tuple(int(min(255, c * k)) for c in base))
    return cols

QUADS = [(0, 1, 2, 3), (5, 4, 7, 6), (1, 5, 6, 2), (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)]

def add_part(buf, verts_world, base):
    faces = []
    for (i0, i1, i2, i3) in QUADS:
        faces.append((verts_world[i0], verts_world[i1], verts_world[i2], verts_world[i3]))
    cols = shade(faces, base)
    for f, c in zip(faces, cols):
        z = float(np.mean([p[2] for p in f]))
        buf.append((z, f, c))

YAW = rot_y(math.radians(-14.0))

def proj(p):
    q = YAW @ np.array(p, float)
    return (CX + q[0] * S, CY - q[1] * S)

def frame(phase, lean_deg=-7.0):
    buf = []
    # ---- 根：髋 ----
    bob = -0.020 * math.cos(2 * phase) - 0.004
    hipy = 0.62 + bob
    lean = D2R(lean_deg)
    M_torso = rot_z(lean); t_torso = np.array([0, hipy, 0])

    def T_torso(verts):
        return place(verts, M_torso, t_torso)

    # 躯干
    v, _ = frustum(0.02, 0.22, 0.10, 0.075, 0.13, 0.085)
    buf_part(buf, T_torso(v), SH.robe)
    v, _ = frustum(0.20, 0.42, 0.135, 0.090, 0.115, 0.080)
    buf_part(buf, T_torso(v), SH.robe2)
    # 腰封
    v, _ = box((0, 0.185, 0), (0.28, 0.055, 0.19))
    buf_part(buf, T_torso(v), SH.sash)
    # 长袍下摆：跟着髋，别跟着腿，摆一摆
    sw = 0.055 * math.sin(phase + 0.6)
    v, _ = frustum(-0.34, 0.04, 0.175, 0.125, 0.115, 0.085)
    buf_part(buf, T_torso(place(v, rot_z(sw), (0, 0, 0))), SH.robe)
    # 领口
    v, _ = box((0.045, 0.43, 0), (0.14, 0.05, 0.16))
    buf_part(buf, T_torso(v), SH.robe2)

    # ---- 脖子 + 头 ----
    v, _ = box((0.02, 0.455, 0), (0.08, 0.06, 0.08))
    buf_part(buf, T_torso(v), SH.skin)
    M_head = M_torso @ rot_z(D2R(2.0 * math.sin(phase)))
    t_head = t_torso + np.array([0.0, 0.0, 0.0])
    v, _ = box((0.028, 0.548, 0), (0.215, 0.198, 0.192))
    buf_part(buf, place(v, M_head, t_head), SH.skin)
    # 头发：后脑一大块 + 顶盖 + 垂到背上的长发
    v, _ = box((-0.115, 0.560, 0), (0.075, 0.245, 0.225))
    buf_part(buf, place(v, M_head, t_head), SH.hair)
    v, _ = box((-0.03, 0.655, 0), (0.255, 0.055, 0.225))
    buf_part(buf, place(v, M_head, t_head), SH.hair)
    v, _ = box((-0.155, 0.430, 0.0), (0.060, 0.190, 0.16))
    buf_part(buf, place(v, M_head, t_head), SH.hair)
    # 眼（侧脸一只，纯色）
    v, _ = box((0.118, 0.575, 0.052), (0.014, 0.034, 0.034))
    buf_part(buf, place(v, M_head, t_head), (30, 34, 48))
    # 刘海：从头顶斜下来盖住额头
    v, _ = box((0.055, 0.638, 0.0), (0.085, 0.070, 0.215))
    buf_part(buf, place(v, M_head, t_head), SH.hair)
    # 眉 + 眼白 + 瞳 + 嘴：侧脸只画一只，够小尺寸读得出来
    v, _ = box((0.118, 0.612, 0.052), (0.012, 0.016, 0.052))
    buf_part(buf, place(v, M_head, t_head), (58, 52, 58))
    v, _ = box((0.118, 0.588, 0.052), (0.012, 0.026, 0.044))
    buf_part(buf, place(v, M_head, t_head), (250, 248, 244))
    v, _ = box((0.121, 0.588, 0.052), (0.012, 0.020, 0.022))
    buf_part(buf, place(v, M_head, t_head), (34, 36, 46))
    v, _ = box((0.128, 0.522, 0.030), (0.010, 0.008, 0.030))
    buf_part(buf, place(v, M_head, t_head), (146, 96, 88))
    # 鼻尖
    v, _ = box((0.152, 0.560, 0.02), (0.030, 0.036, 0.040))
    buf_part(buf, place(v, M_head, t_head), (232, 190, 168))

    # ---- 背上的剑（斜插在背后）----
    ang = D2R(-16)
    M_sw = M_torso @ rot_z(ang)
    off = np.array([-0.115, 0.20, -0.095])
    v, _ = box((0, 0.40, 0), (0.048, 0.80, 0.020))
    buf_part(buf, place(v, M_sw, t_torso + off), SH.steel)
    v, _ = box((0, 0.03, 0), (0.055, 0.10, 0.028))
    buf_part(buf, place(v, M_sw, t_torso + off), SH.hilt)
    v, _ = box((0, 0.085, 0), (0.155, 0.024, 0.046))
    buf_part(buf, place(v, M_sw, t_torso + off), SH.hilt)

    # ---- 腿 ----
    A = D2R(24)          # 大腿摆幅
    K = D2R(46)          # 屈膝幅度
    for side, sg in (("L", 1.0), ("R", -1.0)):
        thigh = A * math.cos(phase) * sg        # + 为向前
        swing = math.sin(phase) * sg            # >0 表示这条腿在往后蹬（支撑期）
        knee = K * max(0.0, -swing) + D2R(3.0)  # 前摆时才屈膝
        # 髋 -> 膝
        M_th = M_torso @ rot_z(-thigh)
        hip = np.array([0.0, 0.62 + bob, 0.0])
        v, _ = box((0, -0.14, 0), (0.125, 0.285, 0.130))
        buf_part(buf, place(v, M_th, hip), SH.robe)
        # 膝 -> 踝
        knee_pt = hip + (M_th @ np.array([0, -0.285, 0]))
        M_sh = M_th @ rot_z(knee)
        v, _ = box((0, -0.14, 0), (0.105, 0.270, 0.110))
        buf_part(buf, place(v, M_sh, knee_pt), SH.robe)
        # 靴子
        ankle = knee_pt + (M_sh @ np.array([0, -0.265, 0]))
        ang_sh = -thigh + knee
        M_ft = rot_z(-ang_sh)
        v, _ = box((0.052, -0.028, 0), (0.185, 0.058, 0.105))
        buf_part(buf, place(v, M_ft, ankle), SH.boot)

    # ---- 手臂 ----
    Aa = D2R(27)
    for side, sg in (("L", 1.0), ("R", -1.0)):
        up = -Aa * math.cos(phase) * sg          # 与同侧腿反相
        M_up = M_torso @ rot_z(up)
        sh = np.array([0.012, 0.900, 0.055])
        v, _ = box((0, -0.115, 0), (0.092, 0.245, 0.092))
        buf_part(buf, place(v, M_up, sh), SH.robe2)
        el = sh + (M_up @ np.array([0, -0.235, 0]))
        M_fo = M_up @ rot_z(D2R(26) + D2R(10) * math.cos(phase) * sg)
        v, _ = box((0, -0.105, 0), (0.074, 0.215, 0.074))
        buf_part(buf, place(v, M_fo, el), SH.robe)
        wr = el + (M_fo @ np.array([0, -0.205, 0]))
        v, _ = box((0.006, -0.032, 0), (0.070, 0.080, 0.062))
        buf_part(buf, place(v, M_fo, wr), SH.skin)
    return buf

def buf_part(buf, verts, base):
    add_part(buf, verts, base)

def render(phase):
    buf = frame(phase)
    buf.sort(key=lambda it: it[0])
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for z, f, c in buf:
        pts = [proj(p) for p in f]
        d.polygon(pts, fill=c)
    return img

def outline_and_harden(img, threshold=110):
    a = img.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    # 外描边 1px：膨胀后的 α 减去原 α
    grown = a.filter(ImageFilter.MaxFilter(3))
    from PIL import ImageChops as IC
    edge = IC.subtract(grown, a)
    line = Image.new("RGBA", img.size, (16, 18, 26, 255))
    line.putalpha(edge)
    img2 = Image.alpha_composite(line, img)
    # 收成硬边：色键窗口里不能有半透明
    al = img2.getchannel("A").point(lambda v: 255 if v >= threshold else 0)
    img2.putalpha(al)
    rgb = img2.convert("RGB")
    return rgb, al

if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
    for i in range(8):
        ph = 2 * math.pi * i / 8.0
        img = render(ph)
        rgb, al = outline_and_harden(img)
        # 缩到成品尺寸 96×152，再硬化一次
        small = rgb.resize((96, 152), Image.LANCZOS)
        am = al.resize((96, 152), Image.LANCZOS).point(lambda v: 255 if v >= 128 else 0)
        out = Image.new("RGBA", (96, 152), (0, 0, 0, 0))
        out.paste(small, (0, 0), am)
        out.putalpha(am)
        out.save(os.path.join(OUT, "frames", "w%d.png" % (i + 1)))
        print("frame", i + 1, "ok")
