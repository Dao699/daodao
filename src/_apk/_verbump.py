import io, re
# 1) AndroidManifest
mf = r"E:\Daodao\src\_apk\AndroidManifest.xml"
t = io.open(mf, encoding="utf-8", newline="").read()
t2 = t.replace('android:versionCode="8"', 'android:versionCode="9"').replace('android:versionName="8.0"', 'android:versionName="9.0"')
if t2 == t:
    raise SystemExit("manifest unchanged")
io.open(mf, "w", encoding="utf-8", newline="").write(t2)
print("manifest -> 9")

# 2) pet.cs APP_VER
p = r"E:\Daodao\src\桌面分身\pet.cs"
s = io.open(p, encoding="utf-8-sig", newline="").read()
old = "public const int APP_VER = 8;"
if old not in s:
    raise SystemExit("APP_VER anchor miss")
s = s.replace(old, "public const int APP_VER = 9;", 1)
io.open(p, "w", encoding="utf-8-sig", newline="").write(s)
print("pet.cs APP_VER -> 9, len", len(s))