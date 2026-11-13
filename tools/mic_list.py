import sounddevice as sd
import numpy as np

print("DEFAULT_INPUT:", sd.query_devices(kind="input"))
print("--- inputs ---")
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0:
        print("IDX %d | %s | ch=%d | sr=%s" % (i, d["name"], d["max_input_channels"], d["default_samplerate"]))

fs = 16000
rec = sd.rec(int(fs * 3), samplerate=fs, channels=1, dtype="int16")
sd.wait()
flat = rec.reshape(-1).astype(np.float64)
rms = float(np.sqrt(np.mean(flat ** 2))) if flat.size else 0.0
peak = int(np.abs(flat).max()) if flat.size else 0
print("QUIET_TEST rms=%.1f peak=%d" % (rms, peak))
