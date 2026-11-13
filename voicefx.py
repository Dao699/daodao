import sys, os, io, asyncio, wave, struct, math
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))


def synth(text, voice, mp3path):
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, voice).save(mp3path))


def load_mp3(path):
    import miniaudio
    d = miniaudio.decode_file(path, output_format=miniaudio.SampleFormat.FLOAT32)
    x = np.frombuffer(d.samples, dtype=np.float32).copy()
    return x, int(d.sample_rate), int(d.nchannels)


def pitch(x, ratio):
    if abs(ratio - 1.0) < 1e-3:
        return x
    n = max(1, int(len(x) * ratio))
    idx = np.linspace(0.0, len(x) - 1.0, n)
    return np.interp(idx, np.arange(len(x), dtype=np.float64), x).astype(np.float32)


def lowpass(x, k):
    if k <= 1:
        return x
    ker = np.ones(k, dtype=np.float32) / float(k)
    return np.convolve(x, ker, mode="same").astype(np.float32)


def ring(x, sr, f, depth):
    t = np.arange(len(x), dtype=np.float32) / float(sr)
    mod = (1.0 - depth) + depth * np.cos(2.0 * math.pi * f * t)
    return (x * mod).astype(np.float32)


def quantize(x, levels):
    return (np.round(x * levels) / float(levels)).astype(np.float32)


def echo(x, sr, delay_ms, decay, n):
    d = max(1, int(sr * delay_ms / 1000.0))
    out = x.copy()
    for i in range(1, n + 1):
        off = i * d
        if off >= len(x):
            break
        out[off:] += x[:len(x) - off] * (decay ** i)
    return out.astype(np.float32)


def tremolo(x, sr, f, depth):
    t = np.arange(len(x), dtype=np.float32) / float(sr)
    return (x * (1.0 - depth + depth * np.sin(2.0 * math.pi * f * t))).astype(np.float32)


def hum(x, sr, f, level):
    t = np.arange(len(x), dtype=np.float32) / float(sr)
    return (x + level * np.sin(2.0 * math.pi * f * t)).astype(np.float32)


def normalize(x, peak=0.92):
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    if m < 1e-6:
        return x
    return (x * (peak / m)).astype(np.float32)


FX = {
    "none": [],
    "cyber": [("pitch", 1.14), ("ring", 41, 0.70), ("quantize", 16),
              ("lowpass", 3), ("echo", 45, 0.30, 4), ("hum", 55, 0.05)],
    "old": [("pitch", 1.16), ("tremolo", 2.2, 0.12), ("lowpass", 5)],
    "tiny": [("pitch", 0.76), ("tremolo", 9.0, 0.22)],
    "beast": [("pitch", 1.38), ("lowpass", 7), ("echo", 140, 0.55, 3), ("hum", 42, 0.03)],
    "cat": [("pitch", 0.70), ("tremolo", 12.0, 0.38)],
    "comedy": [("pitch", 0.94), ("tremolo", 3.5, 0.10)],
    "echo": [("echo", 160, 0.50, 5)],
    "robot": [("pitch", 1.06), ("ring", 70, 0.45), ("quantize", 24), ("echo", 30, 0.25, 3)],
}


def apply_fx(x, sr, name):
    for step in FX.get(name, []):
        op = step[0]
        if op == "pitch":
            x = pitch(x, step[1])
        elif op == "lowpass":
            x = lowpass(x, step[1])
        elif op == "ring":
            x = ring(x, sr, step[1], step[2])
        elif op == "quantize":
            x = quantize(x, step[1])
        elif op == "echo":
            x = echo(x, sr, step[1], step[2], step[3])
        elif op == "tremolo":
            x = tremolo(x, sr, step[1], step[2])
        elif op == "hum":
            x = hum(x, sr, step[1], step[2])
    return x


def save_wav(path, x, sr):
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    args = {}
    i = 1
    while i < len(sys.argv) - 1:
        if sys.argv[i].startswith("--"):
            args[sys.argv[i][2:]] = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    txt = args.get("text", "")
    out = args.get("out", "")
    voice = args.get("voice", "zh-CN-XiaoxiaoNeural")
    fx = args.get("fx", "none")
    keep = args.get("keep", "")
    if not txt or not out:
        print("ERR|missing")
        return 2
    try:
        text = io.open(txt, "r", encoding="utf-8").read().strip()
    except Exception as e:
        print("ERR|read|" + repr(e))
        return 2
    if not text:
        print("ERR|empty")
        return 2
    tmp = keep or (out + ".mp3")
    try:
        synth(text, voice, tmp)
    except Exception as e:
        print("ERR|synth|" + repr(e))
        return 3
    try:
        x, sr, ch = load_mp3(tmp)
        if ch > 1:
            x = x.reshape(-1, ch).mean(axis=1)
        x = apply_fx(x, sr, fx)
        x = normalize(x)
        save_wav(out, x, sr)
    except Exception as e:
        print("ERR|fx|" + repr(e))
        return 4
    try:
        if not keep and os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        pass
    print("OK|" + str(len(x)) + "|" + str(sr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
