import io, re, base64
h = r"E:\Daodao\src\_apk\assets\dao.html"
s = io.open(h, encoding="utf-8", newline="").read()

m = re.search(r"var FACES = \[(.*?)\];", s, re.S)
if not m:
    raise SystemExit("FACES block not found")
body = m.group(1)
items = re.findall(r'"data:image/png;base64,([A-Za-z0-9+/=]+)"', body)
print("faces found:", len(items))
if len(items) != 12:
    raise SystemExit("expect 12 faces, got %d" % len(items))

def b64(path):
    return base64.b64encode(io.open(path, "rb").read()).decode("ascii")

new8 = b64(r"E:\Daodao\src\桌面分身\_fullbody\face_8_cut.png")
new10 = b64(r"E:\Daodao\src\桌面分身\_fullbody\face_10_cut.png")

old8, old10 = items[8], items[10]
assert len(old8) > 1000 and len(old10) > 1000
items[8] = new8
items[10] = new10

newbody = "\n" + ",\n".join('"data:image/png;base64,%s"' % it for it in items) + "\n"
s = s[:m.start(1)] + newbody + s[m.end(1):]
io.open(h, "w", encoding="utf-8", newline="").write(s)
print("html len", len(s))
print("old8", len(old8), "-> new8", len(new8))
print("old10", len(old10), "-> new10", len(new10))