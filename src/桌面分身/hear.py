# -*- coding: utf-8 -*-
import sys, os, wave, json, threading, time, queue

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = r"E:\Daodao\voskmodel"
DEV_CACHE = os.path.join(BASE, "mic_dev.json")

GAIN = 3.5           # 笔记本内置麦本来就小声，先整体抬三倍半
NORM_TARGET_RMS = 6000  # 确认有人说话后，把整体响度拉到这个 rms 附近（比按峰值拉稳）
NORM_MIN_PEAK = 250  # 峰值低于这个当作真没说话，不放大（免得把底噪抬成噪声）
VAD_MIN = 95         # 这个机器底噪 rms 大约 54，门槛压到 95 才不会把正常说话当静音

FS_OUT = 16000


def _sd():
    import sounddevice as sd
    return sd


def _cands():
    """列出所有能录的输入设备，带上接口类型，方便挑最灵的那一路。"""
    sd = _sd()
    out = []
    try:
        devs = sd.query_devices()
        apis = sd.query_hostapis()
    except Exception:
        return out
    for i, d in enumerate(devs):
        try:
            if int(d["max_input_channels"]) < 1:
                continue
            api = apis[int(d["hostapi"])]["name"]
            out.append({
                "index": i,
                "name": d["name"],
                "api": api,
                "fs": int(d.get("default_samplerate") or 44100),
            })
        except Exception:
            continue
    return out


def _probe(dev, sec=0.3):
    """录一小段看电平。Windows 上同一支麦克风会挂出 MME/DirectSound/WASAPI 好几路，
    有的路根本没信号（这台机器 MME 那路实测 rms 只有 127），所以必须实测再选。"""
    sd = _sd()
    import numpy as np
    try:
        st = sd.InputStream(device=dev["index"], samplerate=dev["fs"], channels=1,
                            dtype="int16", blocksize=int(dev["fs"] * sec))
        st.start()
        data, _ = st.read(int(dev["fs"] * sec))
        st.stop(); st.close()
        x = data.reshape(-1).astype(np.float64)
        if x.size == 0:
            return 0.0, 0.0
        return float(np.sqrt((x ** 2).mean())), float(np.abs(x).max())
    except Exception:
        return -1.0, -1.0


def pick_device(force=False):
    """选一路真能收到声音的麦克风，结果缓存下来，避免每次开机都试一遍。"""
    cands = _cands()
    if not cands:
        return None, FS_OUT

    cached = None
    try:
        if os.path.exists(DEV_CACHE):
            cached = json.load(open(DEV_CACHE, "r", encoding="utf-8"))
    except Exception:
        cached = None
    if cached and not force:
        for c in cands:
            if c["name"] == cached.get("name") and c["api"] == cached.get("api"):
                return c["index"], c["fs"]

    best = None
    best_score = -1.0
    for c in cands:
        rms, peak = _probe(c)
        if rms < 0:
            continue
        score = rms + peak * 0.02
        if score > best_score:
            best_score = score
            best = c
    if best is None:
        return None, FS_OUT
    try:
        json.dump({"name": best["name"], "api": best["api"], "index": best["index"]},
                  open(DEV_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass
    return best["index"], best["fs"]


def _resample(x, fs_in, fs_out=FS_OUT):
    import numpy as np
    if fs_in == fs_out or x.size == 0:
        return x
    n = int(round(x.size * fs_out / float(fs_in)))
    if n <= 0:
        return x
    t_in = np.arange(x.size, dtype=np.float64)
    t_out = np.linspace(0, x.size - 1, n, dtype=np.float64)
    return np.interp(t_out, t_in, x).astype(np.int16)


def _load_model(box, ready):
    """后台线程先把识别模型读进内存。读模型要两秒，正好和你说这句话的时间重叠。"""
    try:
        from vosk import Model, KaldiRecognizer, SetLogLevel
        SetLogLevel(-1)
        m = Model(MODEL_DIR)
        box["rec"] = KaldiRecognizer(m, FS_OUT)
        box["rec"].SetWords(False)
    except Exception as e:
        box["err"] = repr(e)
    finally:
        ready.set()


def record_with_vad(max_sec, out_wav, fs=None, block=0.15, sil_sec=0.6, thresh=None,
                    live_rec=None):
    """边录边判断：说完了（静音 0.6 秒）就提前停，最多录 max_sec 秒。

    v24 改动：
    1) 先实测各路麦克风电平再选一路（默认的 MME 那路常是哑的，录进去只有底噪，
       识别结果就是空的——用户说的"录不进声音"）；
    2) 录音同时把已到的声音喂给识别引擎，说完时基本已经认完，不用再等几秒；
    3) 按设备原生采样率采集，存盘前重采样到 16k，按峰值归一化。
    """
    sd = _sd()
    import numpy as np

    if fs is None:
        dev_index, fs_in = pick_device()
    else:
        dev_index, fs_in = None, fs

    def _open(dev):
        return sd.InputStream(device=dev, samplerate=fs_in, channels=1, dtype="int16",
                              blocksize=int(fs_in * block))

    try:
        stream = _open(dev_index)
    except Exception:
        # 缓存里那一路已经不在了，重新挑
        dev_index, fs_in = pick_device(force=True)
        stream = _open(dev_index)
    stream.start()

    chunks = []
    fed = 0
    sil_blocks = 0
    need_sil = max(1, int(sil_sec / block))
    elapsed = 0.0
    floor_est = None
    spoke = False
    speech_peak = 0.0
    feed_err = [None]
    feed_q = queue.Queue()

    def _feeder():
        # 识别放到后台线程吃：主循环只管录，不能被解码拖住，
        # 否则音画/录音的时序都会往后拖，"说完了还在等"就是这么来的
        while True:
            item = feed_q.get()
            if item is None:
                return
            try:
                rec = live_rec.get("rec") if live_rec else None
                if rec is None:
                    time.sleep(0.02)   # 模型还没读好，先等一下再喂
                    rec = live_rec.get("rec")
                if rec is not None:
                    rec.AcceptWaveform(item.tobytes())
            except Exception as e:
                feed_err[0] = repr(e)

    feeder = None
    if live_rec is not None:
        feeder = threading.Thread(target=_feeder)
        feeder.daemon = True
        feeder.start()
    try:
        while elapsed < max_sec:
            data, overflowed = stream.read(int(fs_in * block))
            flat = data.reshape(-1)
            rms_raw = float(np.sqrt(np.mean(flat.astype(np.float64) ** 2))) if flat.size else 0.0
            chunks.append(flat)
            # 不再靠"比底噪响多少倍"判说话：这台机器的底噪（风扇+扬声器余音）
            # rms 就有两百多，和人说话只差三四倍，用相对门槛要么一直判在说话
            #（录满 max_sec，反馈就很慢），要么把话切掉。
            # 改成看频带分布：人声能量集中在 300~3400Hz（实测占比 7~10%），
            # 底噪集中 4k 以上（300~3400 只占 2~3%）。
            low_pct = 0.0
            if flat.size:
                sp = np.abs(np.fft.rfft(flat.astype(np.float64) * np.hanning(flat.size)) ** 2)
                fr = np.fft.rfftfreq(flat.size, 1.0 / fs_in)
                tot = float(sp.sum())
                if tot > 1e-6:
                    low_pct = 100.0 * float(sp[(fr >= 300) & (fr < 3400)].sum()) / tot
            if thresh is not None:
                voiced = rms_raw >= thresh
            else:
                voiced = (rms_raw > 400.0 and low_pct >= 4.0) or rms_raw > 1200.0
            if voiced:
                sil_blocks = 0
                spoke = True
                if rms_raw > speech_peak:
                    speech_peak = rms_raw
            else:
                sil_blocks += 1
            elapsed += block
            # 边录边认：先丢进队列，后台线程按顺序喂，读好模型之前的音频也不会漏
            if feeder is not None:
                feed_q.put(_resample(flat, fs_in))
            if os.environ.get("HEAR_DEBUG"):
                sys.stderr.write("DBG t=%.2f rms=%.0f low=%.1f%% peak=%.0f sil=%d spoke=%s\n"
                                 % (elapsed, rms_raw, low_pct, speech_peak, sil_blocks, spoke))
            # 必须真的听见过说话才允许"静音收尾"，否则一开场就停
            if spoke and sil_blocks >= need_sil and elapsed > 0.5:
                break
    finally:
        stream.stop()
        stream.close()
        if feeder is not None:
            feed_q.put(None)
            feeder.join(20)

    raw = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int16)
    audio = _resample(raw.astype(np.int16), fs_in)

    # 到底有没有人说话：全程峰值只有底噪的 1.8 倍以内，就当没出声，不放大
    speech = False
    if raw.size:
        blk = int(fs_in * block)
        pk = [float(np.abs(raw[i:i + blk]).max()) for i in range(0, raw.size, blk) if raw[i:i + blk].size]
        floor_pk = min(pk) if pk else 0.0
        speech = float(np.abs(raw).max()) > max(700.0, floor_pk * 1.8)

    if audio.size:
        # 先按固定倍数抬，确认有人说话再按"响度"拉齐：按 rms 拉比按峰值拉更稳，
        # 峰值只被少数几声咔哒占着的时候，按峰值归一化反而让正常说话还是很小声
        audio = audio.astype(np.float32) * GAIN
        if speech:
            rms = float(np.sqrt((audio ** 2).mean()))
            k = min(NORM_TARGET_RMS / max(rms, 1.0), 12.0)
            if k > 1.0:
                audio = audio * k
        peak = float(np.abs(audio).max())
        if peak > 30000.0:
            # 软限幅，硬裁会把语音削成方波，识别更差
            audio = 30000.0 * np.tanh(audio / 30000.0)
        audio = np.clip(audio, -32768.0, 32767.0).astype(np.int16)
    else:
        audio = np.zeros(0, dtype=np.int16)

    # 边录边认没喂完的尾巴（模型录完才读好的情况），这里一次补齐
    if live_rec is not None and feed_err is None:
        rec = live_rec.get("rec")
        if rec is not None and fed < len(chunks):
            try:
                for c in chunks[fed:]:
                    rec.AcceptWaveform(_resample(c, fs_in).tobytes())
            except Exception as e:
                feed_err = repr(e)

    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS_OUT)
        w.writeframes(audio.tobytes())

    return audio


def recognize(wav_path, fs=FS_OUT):
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)
    model = Model(MODEL_DIR)
    rec = KaldiRecognizer(model, fs)
    rec.SetWords(False)
    with wave.open(wav_path, "rb") as w:
        while True:
            data = w.readframes(4000)
            if not data:
                break
            rec.AcceptWaveform(data)
    res = json.loads(rec.FinalResult())
    return res.get("text", "")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if len(sys.argv) > 1 and sys.argv[1] == "--level":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
        wav = os.path.join(BASE, "mic_level.wav")
        t0 = time.time()
        dev_index, fs_in = pick_device()
        audio = record_with_vad(secs, wav, thresh=160)
        import numpy as np
        rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))) if audio.size else 0.0
        peak = int(np.abs(audio.astype(np.int32)).max()) if audio.size else 0
        print("LEVEL|rms=%d|peak=%d|sec=%.1f|gain=%.1f|fs=%d|dev=%s|ms=%d"
              % (rms, peak, audio.size / float(FS_OUT), GAIN, fs_in, dev_index,
                 int((time.time() - t0) * 1000)))
        return

    max_sec = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    out_wav = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "heard.wav")

    # 模型在后台读，别等到你说完才开始算
    box = {}
    ready = threading.Event()
    th = threading.Thread(target=_load_model, args=(box, ready))
    th.setDaemon(True)
    th.start()

    record_with_vad(max_sec, out_wav, live_rec=box)
    ready.wait(3.0)
    if box.get("err"):
        sys.stderr.write("ERR " + box["err"] + "\n")
        sys.exit(2)
    rec = box.get("rec")
    if rec is None:
        text = recognize(out_wav)
    else:
        text = json.loads(rec.FinalResult()).get("text", "")
    print(text)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write("ERR " + repr(e) + "\n")
        sys.exit(2)
