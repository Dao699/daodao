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
