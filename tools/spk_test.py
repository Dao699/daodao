import subprocess
import sys
import os
import time
import glob

TEMP_VOICE = os.path.join(os.environ["TEMP"], "daovoice")
TOOL = r"E:\Daodao\tools\micvol.exe"

print("=== speaker volume ===")
r = subprocess.run([TOOL, "spk"], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.strip())

mp3s = sorted(glob.glob(os.path.join(TEMP_VOICE, "*.mp3")), key=os.path.getmtime, reverse=True)
if not mp3s:
    print("NO_MP3")
    sys.exit(0)

sample = mp3s[0]
print("play:", os.path.basename(sample), os.path.getsize(sample), "B")
play = os.path.join(TEMP_VOICE, "play.ps1")
print("play.ps1 exists:", os.path.exists(play))

p = subprocess.Popen(
    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", play, "-f", sample],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(1.2)

m = subprocess.run([TOOL, "spk", "level", "4"], capture_output=True, text=True, encoding="utf-8")
print("=== speaker level while playing ===")
print(m.stdout.strip())

try:
    p.wait(timeout=20)
    print("player exit code:", p.returncode)
except subprocess.TimeoutExpired:
    print("player still running (long audio)")
    p.kill()
