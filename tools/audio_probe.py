import sounddevice as sd
import numpy as np

print("=== default devices ===")
print("default:", sd.query_devices(kind="output"))
print()
print("=== all devices ===")
for i, d in enumerate(sd.query_devices()):
    if d["max_output_channels"] > 0:
        print(i, "|OUT|", d["name"], "| ch=", d["max_output_channels"], " sr=", int(d["default_samplerate"]))
print()
print("=== tone test (440Hz 1.5s) ===")
fs = 44100
t = np.linspace(0, 1.5, int(fs * 1.5), endpoint=False)
amp = 0.35
wave = (amp * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
try:
    sd.play(wave, fs)
    sd.wait()
    print("tone played ok")
except Exception as e:
    print("tone failed:", repr(e))
