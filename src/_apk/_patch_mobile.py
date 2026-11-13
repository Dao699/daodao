p = r"E:\Daodao\src\_apk\assets\dao.html"
raw = open(p, "rb").read()
s = raw.decode("utf-8-sig")
print("CRLF count", s.count("\r\n"), "LF count", s.count("\n"))
s = s.replace("\r\n", "\n")
orig = s

old1 = """  var poseImgs = [];
  (function () {
    for (var _pi = 0; _pi < POSES.length; _pi++) {
      var _pim = new Image();
      _pim.src = POSES[_pi];
      poseImgs.push(_pim);
    }
  })();"""
new1 = """  var poseImgs = [];
  // 三套姿势图分开预加载：恐龙用 POSES，黑发少年用 POSES_7，银发剑客用 POSES_11。
  // 以前这里只加载了 POSES 一套，POSES_7 / POSES_11 算出来也没人用，等于白算
  var POSE_SETS = { 4: POSES, 7: POSES_7, 11: POSES_11 };
  var poseImgsBySp = {};
  (function () {
    Object.keys(POSE_SETS).forEach(function (k) {
      var arr = [];
      var list = POSE_SETS[k];
      for (var _pi = 0; _pi < list.length; _pi++) {
        var _pim = new Image();
        _pim.src = list[_pi];
        arr.push(_pim);
      }
      poseImgsBySp[k] = arr;
      if (k === '4') poseImgs = arr;
    });
  })();"""
assert old1 in s, "pose preload anchor missing"
s = s.replace(old1, new1, 1)

old2 = "    var poseP = -1;\n    if (POSES.length >= 5 && species === 4 && lieAmt < 0.40) {"
new2 = "    var poseP = -1;\n    var curPose = poseImgsBySp[species];\n    if (curPose && curPose.length >= 5 && lieAmt < 0.40) {"
assert old2 in s, "pose select anchor missing"
s = s.replace(old2, new2, 1)

old3 = "    if (poseP >= 0 && poseImgs[poseP] && poseImgs[poseP].complete && poseImgs[poseP].naturalWidth) {\n      var pim2 = poseImgs[poseP];"
new3 = "    if (poseP >= 0 && curPose && curPose[poseP] && curPose[poseP].complete && curPose[poseP].naturalWidth) {\n      var pim2 = curPose[poseP];"
assert old3 in s, "pose draw anchor missing"
s = s.replace(old3, new3, 1)

old4 = "        var _d = new Date();\n        species = Math.floor((_d - new Date(_d.getFullYear(), 0, 0)) / 86400000) % total;"
new4 = "        var _d = new Date();\n        // 和电脑端完全同一套规则：只在 6 / 7 / 11 这三个有整套动作的形象里轮，\n        // 同一天两端是同一个形象\n        var _kinds = [6, 7, 11];\n        species = _kinds[Math.floor((_d - new Date(_d.getFullYear(), 0, 0)) / 86400000) % _kinds.length];"
assert old4 in s, "species rotation anchor missing"
s = s.replace(old4, new4, 1)

old5 = "    species = (species + 1 + Math.floor(Math.random() * (imgs.length - 1))) % imgs.length;"
new5 = "    var _ks = [6, 7, 11];\n    var _ci = _ks.indexOf(species);\n    species = _ks[(_ci + 1 + Math.floor(Math.random() * (_ks.length - 1))) % _ks.length];"
assert old5 in s, "swap anchor missing"
s = s.replace(old5, new5, 1)

assert s != orig
open(p, "wb").write(s.encode("utf-8-sig"))
print("patched ok, len", len(s))