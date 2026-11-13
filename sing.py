# -*- coding: utf-8 -*-
"""哼一段小星星：用正弦加谐波合成"La"的音节，听起来像在唱，不是念。
输出 sing.wav，交给 play_audio.py 放。"""
import math
import os
import sys

import numpy as np

APP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(APP, "sing.wav")
SR = 22050

# 小星星：每段是 (音名, 拍数)
NOTE = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
}
MELODY = [
    ("C4", 1), ("C4", 1), ("G4", 1), ("G4", 1), ("A4", 1), ("A4", 1), ("G4", 2),
    ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 1), ("D4", 1), ("C4", 2),
    ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 2),
    ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 2),
    ("C4", 1), ("C4", 1), ("G4", 1), ("G4", 1), ("A4", 1), ("A4", 1), ("G4", 2),
    ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 1), ("D4", 1), ("C4", 2),
]


def voice_note(freq, dur, beat=0.42):
    """一个带谐波和颤音的"唱"音节"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    # 颤音：真人唱的时候音高一直在轻轻晃
    vib = 1.0 + 0.012 * np.sin(2 * math.pi * 5.2 * t)
    w = np.zeros(n, dtype=np.float64)
    for k, amp in ((1, 1.0), (2, 0.42), (3, 0.20), (4, 0.09)):
        w += amp * np.sin(2 * math.pi * freq * k * t * vib + k * 0.6)
    w /= 1.71
    # 音头音尾都收一下，不然每个字都像被切断
    a = int(n * 0.10) + 1
    r = int(n * 0.18) + 1
    env = np.ones(n)
    env[:a] = np.linspace(0, 1, a) ** 0.7
    env[-r:] = np.linspace(1, 0, r) ** 1.4
    return (w * env).astype(np.float64)


def main():
    parts = [voice_note(NOTE[nm], d * 0.42) for nm, d in MELODY]
    gap = np.zeros(int(SR * 0.03))
    sig = np.concatenate([np.concatenate([p, gap]) for p in parts])
    # 整体再淡入淡出一层，开头结尾不生硬
    n = len(sig)
    f = int(SR * 0.12)
    sig[:f] *= np.linspace(0, 1, f)
    sig[-f:] *= np.linspace(1, 0, f)
    peak = float(np.max(np.abs(sig))) or 1.0
    sig = sig / peak * 0.72
    pcm = (sig * 32767).astype(np.int16)
    try:
        import wave
        with wave.open(OUT, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm.tobytes())
        print("OK|%.1fs|%dB" % (n / SR, os.path.getsize(OUT)))
    except Exception as e:
        print("ERR|" + repr(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
