# -*- coding: utf-8 -*-
import os
exe = r"E:\Daodao\道.exe"
data = open(exe, "rb").read()
for k in (b"props_cape.png", b"props_sword.png", b"LoadProps"):
    print(k.decode(), b"FOUND" if k in data else b"MISSING")
print("exe size", os.path.getsize(exe))
for p in (r"E:\Daodao\props_cape.png", r"E:\Daodao\props_sword.png"):
    print(p, os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0)
