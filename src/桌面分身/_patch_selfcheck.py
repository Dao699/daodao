p = r"E:\Daodao\src\桌面分身\pet.cs"
s = open(p, "rb").read().decode("utf-8-sig")
old = """        p.walkTicks = 80;
        p.walkDirX = 1;
        for (int wi = 0; wi < 4; wi++)
        {
            p.t = 0.40f + wi * 0.19f;
            DumpOne(p, Path.Combine(dir, "selfcheck_walk" + wi + ".png"));
        }"""
new = """        // 走路专门测八帧的形象（黑发少年 = 7），抓满八帧才看得出整圈
        p.species = 7;
        p.ApplyPose(7);
        p.walkTicks = 80;
        p.walkDirX = 1;
        for (int wi = 0; wi < 8; wi++)
        {
            p.t = 0.36f + wi * 0.09f;
            DumpOne(p, Path.Combine(dir, "selfcheck_walk" + wi + ".png"));
        }"""
assert old in s, "walk selfcheck anchor missing"
s = s.replace(old, new, 1)
open(p, "wb").write(s.encode("utf-8-sig"))
print("ok", len(s))