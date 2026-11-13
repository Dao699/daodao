p = r"E:\Daodao\src\_apk\build_pc.ps1"
s = open(p, "rb").read().decode("utf-8-sig")
old = """foreach ($n in @('names.txt', 'voices.txt')) {"""
new = """# 八帧走路循环：按形象分目录放，进了 exe 才是自包含的，拷到哪都能走
for ($sp = 0; $sp -lt 12; $sp++) {
    for ($wi = 1; $wi -le 8; $wi++) {
        $p = "_walk8_$sp\\walk$wi.png"
        if (Test-Path -LiteralPath $p) { $cargs += "/resource:$p,walk8_${sp}_$wi.png" }
    }
}
foreach ($n in @('names.txt', 'voices.txt')) {"""
assert old in s, "anchor missing"
s = s.replace(old, new, 1)
open(p, "wb").write(s.encode("utf-8-sig"))
print("ok", len(s))