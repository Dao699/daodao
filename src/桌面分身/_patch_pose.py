import io
p = r"E:\Daodao\src\桌面分身\pet.cs"
s = io.open(p, encoding="utf-8-sig").read()
NL = "\r\n" if "\r\n" in s[:4000] else "\n"

def rep(old, new, tag):
    global s
    old2, new2 = old.replace("\n", NL), new.replace("\n", NL)
    if old2 not in s:
        raise SystemExit("ANCHOR MISS: " + tag)
    s = s.replace(old2, new2, 1)
    print("ok:", tag)

# 1) 躺下：不再压成纸片
rep(
"""        if (lieAmt > 0.02f)
        {
            sy *= 1f - 0.52f * lieAmt;
            sx *= 1f + 0.10f * lieAmt;
            bob -= 40f * lieAmt;
            cx -= 60f * lieAmt;
        }""",
"""        if (lieAmt > 0.02f)
        {
            // 以前压到 0.48 高，整个人成了被拍扁的一张纸；现在只轻压 0.20，
            // 主要靠往下沉一点、往枕头那边挪一点来表达"侧躺"，身形还立得住
            sy *= 1f - 0.20f * lieAmt;
            sx *= 1f + 0.05f * lieAmt;
            bob -= 22f * lieAmt;
            cx -= 34f * lieAmt;
        }""", "lie")

# 2) 坐骑收窄
rep(
"""                float my = 10f + slide;
                float mw = targetH * 1.55f;
                float mh = targetH * 0.40f;""",
"""                float my = 10f + slide;
                // 以前按 1.55 倍身高画，宽得像一张大坐垫把整个人裹进去；
                // 收到 1.05 倍、矮一点，才像一匹驮着人的矮脚兽
                float mw = targetH * 1.05f;
                float mh = targetH * 0.36f;""", "mount")

# 3) 披风贴图版收窄、不盖头
rep(
"""                    float cpw = Math.Max(baseW * 2.0f, targetH * 1.25f);
                    float cph = targetH * 0.92f;
                    float ctop = -targetH * 0.80f + slide * 0.4f;""",
"""                    // 原来按 1.25 倍身高铺，套在剑客这种瘦长角色身上就宽出一大圈，读成一对翅膀；
                    // 收到 0.80 倍身高，肩线从 -0.58 起算，刚好搭在肩上、不顶到头顶
                    float cpw = Math.Max(baseW * 1.30f, targetH * 0.80f);
                    float cph = targetH * 0.80f;
                    float ctop = -targetH * 0.58f + slide * 0.4f;""", "cape")

io.open(p, "w", encoding="utf-8-sig", newline="").write(s)
print("written", len(s))