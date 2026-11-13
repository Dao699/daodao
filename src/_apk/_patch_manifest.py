p = r"E:\Daodao\src\_apk\AndroidManifest.xml"
s = open(p, "rb").read().decode("utf-8")
s = s.replace('android:versionCode="7"', 'android:versionCode="8"')
s = s.replace('android:versionName="7.0"', 'android:versionName="8.0"')
open(p, "wb").write(s.encode("utf-8"))
print("manifest -> 8")