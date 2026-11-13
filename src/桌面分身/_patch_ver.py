p = r"E:\Daodao\src\桌面分身\pet.cs"
s = open(p, "rb").read().decode("utf-8-sig")
old = "    public const int APP_VER = 7;"
new = "    public const int APP_VER = 8;"
assert old in s, "APP_VER anchor missing"
s = s.replace(old, new, 1)
open(p, "wb").write(s.encode("utf-8-sig"))
print("APP_VER -> 8")