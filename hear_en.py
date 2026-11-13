import sys, os, wave, json

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = r"E:\Daodao\voskmodel_en"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    out_wav = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "heard_en.wav")

    import sounddevice as sd
    import numpy as np

    fs = 16000
    rec = sd.rec(int(dur * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()

    # v22：和中文那条一样，先按固定倍数放大再按峰值归一化，免得声音小到识别不出来
    GAIN = 3.5
    NORM_TARGET = 20000
    a = rec.reshape(-1).astype(np.float32) * GAIN
    peak = float(np.abs(a).max()) if a.size else 0.0
    if peak > 250:
        k = min(NORM_TARGET / peak, 20.0)
        if k > 1.0:
            a = a * k
    rec = np.clip(a, -32768.0, 32767.0).astype(np.int16)

    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes(rec.tobytes())

    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)
    model = Model(MODEL_DIR)
    rec2 = KaldiRecognizer(model, fs)
    rec2.SetWords(False)
    with wave.open(out_wav, "rb") as w:
        while True:
            data = w.readframes(4000)
            if not data:
                break
            rec2.AcceptWaveform(data)
    res = json.loads(rec2.FinalResult())
    print(res.get("text", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write("ERR " + repr(e) + "\n")
        sys.exit(2)
