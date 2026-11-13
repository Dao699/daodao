import os
import subprocess
import sys
import time
import glob

TOOL = r"E:\Daodao\tools\micvol.exe"
PLAY = r"E:\Daodao\play_audio.py"
TEMP_VOICE = os.path.join(os.environ["TEMP"], "daovoice")

mp3s = sorted(glob.glob(os.path.join(TEMP_VOICE, "*.mp3")) + glob.glob(os.path.join(TEMP_VOICE, "*.wav")),
              key=os.path.getmtime, reverse=True)
print("found", len(mp3s))
if not mp3s:
    sys.exit(0)
sample = mp3s[0]
print("play:", os.path.basename(sample), os.path.getsize(sample), "B")

p = subprocess.Popen([sys.executable, "-X", "utf8", PLAY, sample],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
time.sleep(0.6)

m = subprocess.run([TOOL, "spk", "level", "4"], capture_output=True, text=True, encoding="utf-8")
for line in m.stdout.strip().splitlines():
    if line.startswith("peak="):
        print("speaker_peak ->", line)

out, err = p.communicate(timeout=30)
print("rc:", p.returncode)
print("stdout:", (out or "").strip()[:200])
if err:
    print("stderr:", err.strip()[:300])
