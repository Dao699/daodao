import io, re, sys
p = r"E:\Daodao\src\桌面分身\pet.cs"
s = io.open(p, encoding="utf-8-sig").read()

# 1) 构造函数里不再无条件重做图标
old1 = "        dayStamp = DateTime.Today;\r\n        MakeDailyIcon();                                 // 今天这个形象的图标也摆上桌面"
if old1 not in s:
    old1 = old1.replace("\r\n", "\n")
new1 = "        dayStamp = DateTime.Today;\r\n        // 同一天反复重启不再重做图标。以前每次启动都重写 ico 并 Save 一遍 lnk，\r\n        // Explorer 的图标缓存被一次次击穿，桌面上就会出现那个两个方块叠着的默认占位图标。\r\n        EnsureDailyIcon();"
if old1 not in s:
    old1 = "        dayStamp = DateTime.Today;\n        MakeDailyIcon();                                 // 今天这个形象的图标也摆上桌面"
    new1 = new1.replace("\r\n", "\n")
assert old1 in s, "constructor anchor missing"
s = s.replace(old1, new1, 1)

# 2) 新增 EnsureDailyIcon
anchor = "    void MakeDailyIcon()\n    {"
if anchor not in s:
    anchor = "    void MakeDailyIcon()\r\n    {"
    adder = ("    // 今天这份 ico 已经在就不再重做：重做会连带重写 lnk，Explorer 又要重画一遍图标。\r\n"
             "    void EnsureDailyIcon()\r\n"
             "    {\r\n"
             "        try\r\n"
             "        {\r\n"
             "            string dir = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), \"icons\");\r\n"
             "            string today = Path.Combine(dir, \"dao_\" + DateTime.Today.ToString(\"yyyyMMdd\") + \".ico\");\r\n"
             "            if (File.Exists(today))\r\n"
             "            {\r\n"
             "                SetShortcutIcon(today);   // 文件在就只校准快捷方式，不重写文件\r\n"
             "                return;\r\n"
             "            }\r\n"
             "            MakeDailyIcon();\r\n"
             "        }\r\n"
             "        catch { MakeDailyIcon(); }\r\n"
             "    }\r\n\r\n")
else:
    adder = ("    // 今天这份 ico 已经在就不再重做：重做会连带重写 lnk，Explorer 又要重画一遍图标。\n"
             "    void EnsureDailyIcon()\n"
             "    {\n"
             "        try\n"
             "        {\n"
             "            string dir = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), \"icons\");\n"
             "            string today = Path.Combine(dir, \"dao_\" + DateTime.Today.ToString(\"yyyyMMdd\") + \".ico\");\n"
             "            if (File.Exists(today))\n"
             "            {\n"
             "                SetShortcutIcon(today);   // 文件在就只校准快捷方式，不重写文件\n"
             "                return;\n"
             "            }\n"
             "            MakeDailyIcon();\n"
             "        }\n"
             "        catch { MakeDailyIcon(); }\n"
             "    }\n\n")
assert anchor in s, "MakeDailyIcon anchor missing"
s = s.replace(anchor, adder + anchor, 1)

# 3) SetShortcutIcon 里，图标没变就不 Save
s3_old = "            object sc = sh.InvokeMember(\"CreateShortcut\", System.Reflection.BindingFlags.InvokeMethod, null, shell, new object[] { lnk });\r\n"
if s3_old not in s:
    s3_old = s3_old.replace("\r\n", "\n")
nl = "\r\n" if "\r\n" in s[s.find("object sc = sh.InvokeMember"):s.find("object sc = sh.InvokeMember")+200] else "\n"
s3_new = (s3_old
    + "            string want = icoPath + \",0\";" + nl
    + "            // 同一个图标就别再 Save：每 Save 一次都会让 Explorer 丢掉缓存重画桌面图标" + nl
    + "            object cur = sh.InvokeMember(\"IconLocation\", System.Reflection.BindingFlags.GetProperty, null, sc, null);" + nl
    + "            if (cur != null && Convert.ToString(cur) == want) return;" + nl)
assert s3_old in s, "shortcut anchor missing"
s = s.replace(s3_old, s3_new, 1)
s = s.replace('new object[] { icoPath + \",0\" }', 'new object[] { want }', 1)

io.open(p, "w", encoding="utf-8-sig", newline="").write(s)
print("patched ok, len=", len(s))