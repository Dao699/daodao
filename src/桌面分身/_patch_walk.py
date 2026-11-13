import re
p = r"E:\Daodao\src\桌面分身\pet.cs"
s = open(p, "rb").read().decode("utf-8-sig")
orig = s

# ---- 1. 字段 ----
old1 = "    Dictionary<int, Bitmap[]> poseMap = new Dictionary<int, Bitmap[]>();\n    int[] poseKinds = new int[0];\n"
new1 = old1 + """
    // ==== 八帧走路循环 ====
    // 每个形象单独一套：触地、下沉、交叉、抬起 x 左右各一遍。
    // 走的时候直接换帧，手脚在图里本来就摆开了，不靠切条位移去骗眼睛
    Dictionary<int, Bitmap[]> walkMap = new Dictionary<int, Bitmap[]>();
    Bitmap[] walkFrames = null;
"""
assert old1 in s, "field anchor missing"
s = s.replace(old1, new1, 1)

# ---- 2. LoadPoses 里加载八帧 ----
old2 = "            if (map.Count == 0) return;\n"
new2 = """            // 八帧走路：只有配了整套的形象才有，缺一张就整套不用
            for (int sp = 0; sp < 12; sp++)
            {
                Bitmap[] wf = new Bitmap[8];
                bool wok = true;
                for (int wi = 0; wi < 8; wi++)
                {
                    Bitmap wb = null;
                    try
                    {
                        Stream wes = ResStream("walk8_" + sp + "_" + (wi + 1) + ".png");
                        if (wes != null) { using (Stream ws2 = wes) { wb = new Bitmap(ws2); } }
                        else
                        {
                            string wp = Path.Combine(AppDir(), "_walk8_" + sp, "walk" + (wi + 1) + ".png");
                            if (File.Exists(wp))
                            {
                                using (Stream wfs = new FileStream(wp, FileMode.Open, FileAccess.Read))
                                {
                                    wb = new Bitmap(wfs);
                                }
                            }
                        }
                    }
                    catch { wb = null; }
                    if (wb == null) { wok = false; break; }
                    wf[wi] = wb;
                }
                if (wok) walkMap[sp] = wf;
            }
            if (map.Count == 0) return;
"""
assert old2 in s, "load anchor missing"
s = s.replace(old2, new2, 1)

# ---- 3. ApplyPose 里挂上 ----
old3 = """        poses = set2;
        poseOwner = sp;
        poseIdx = 0;
        posePrev = 0;
"""
new3 = """        poses = set2;
        poseOwner = sp;
        poseIdx = 0;
        posePrev = 0;
        Bitmap[] wset = null;
        if (walkMap != null && walkMap.TryGetValue(sp, out wset)) walkFrames = wset;
        else walkFrames = null;
"""
assert old3 in s, "applypose anchor missing"
s = s.replace(old3, new3, 1)

# ---- 4. DrawPosePicture 走路换帧 ----
old4 = """        float footY = cy + 68f;
        Bitmap pb = poses[poseIdx];"""
new4 = """        float footY = cy + 68f;
        Bitmap pb = poses[poseIdx];
        // 这个形象配了八帧走路：走起来直接换帧，手脚是画出来的
        // 11 帧/秒，八帧一圈约 0.72 秒，正好是正常步速
        if ((walkTicks > 0 || runTicks > 0) && walkFrames != null && walkFrames.Length >= 8)
        {
            int fi = (int)(t * 11.0f) % 8;
            if (fi < 0) fi += 8;
            pb = walkFrames[fi];
        }"""
assert old4 in s, "draw anchor missing"
s = s.replace(old4, new4, 1)

assert s != orig
open(p, "wb").write(s.encode("utf-8-sig"))
print("patched, len", len(s))