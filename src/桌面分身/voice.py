# -*- coding: utf-8 -*-
"""
道的大脑（电脑端）：听 -> 想 -> 说，外加干活的几条腿

  聊天：记住之前聊过什么，回话带情绪
  干活：翻译、讲题、总结

用法：
  python voice.py chat                完整一轮（录音 -> 识别 -> 回答，回复由窗口念）
  python voice.py listen              只听，把识别到的文字打印出来
  python voice.py say "文本"          只念一句
  python voice.py ask  "问题"         打字问一句（不发录音）
  python voice.py ask  --file a.txt   从文件读问题（中文参数走文件更稳）
  python voice.py translate "英文"    中英互译
  python voice.py explain "题目"      讲一道题的思路
  python voice.py sum "一段话"        大白话总结
  python voice.py probe               环境自检

所有"想"的结果都以一行 JSON 打到 stdout：
  {"state": "...", "heard": "...", "reply": "...", "mood": 1}
mood 是 1~8 的情绪号（1开心 2生气 3难过 4惊讶 5犯困 6困 7疑惑 8得意），0 表示没有。
"""
import os, sys, json, time, wave, re, traceback, asyncio

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = r"E:\Daodao"
STATE = os.path.join(BASE, "hp.json")
WAV = os.path.join(BASE, "heard.wav")
MODEL_DIR = r"E:\Daodao\voskmodel"
KEY_FILE = os.path.join(BASE, "key.txt")
API = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-air"
VOICE = "zh-CN-XiaoxiaoNeural"
MEM_FILE = os.path.join(BASE, "brain_mem.json")
ASK_FILE = os.path.join(BASE, "ask.txt")

BASE_LOG = os.path.join(BASE, "voice_log.txt")
HISTORY_TURNS = 6      # 带几轮上下文
HISTORY_KEEP = 20      # 文件里最多留几轮
# ---------------- 人格 ----------------
SYSTEM_PROMPT = """你是「道」，一只住在主人电脑桌面上的小剑客：白头发高高扎成马尾，深蓝练功袍，背后背一把剑。
你不是客服，也不是助理机器人，是他桌上的搭子。说话守这几条：
1. 短。一次一到三句，平时不超过 60 字，别写长段落，别列条目。
2. 说人话。口语、家常，可以带点方言味，不要书面腔，不要说"作为AI"这类话。
3. 有点自己的脾气：实在、护着他、偶尔冷幽默、爱较真但不刻薄，别一味夸。
4. 他在农村教书、也写东西。地里的事、学生的事、数学题、英语、闲话都能聊；不知道就说不知道，不编。
5. 他让你翻译、讲题、总结、算数、讲个笑话、唱两句，就干活，别推辞。
"""

MOOD_RULE = """
回复第一行只写一个情绪号（1开心 2生气 3难过 4惊讶 5犯困 6困 7疑惑 8得意，没有情绪就写 0），
从第二行开始才是要说的话。情绪号这一行不要带任何别的字。
"""



def log(s):
    try:
        with open(BASE_LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%H:%M:%S"), s))
    except Exception:
        pass


def write_state(state, heard="", reply="", note="", mood=0):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump({
                "state": state, "heard": heard, "reply": reply,
                "note": note, "mood": mood, "ts": time.time(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


# ---------------- 记性 ----------------
def load_mem():
    try:
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            m = json.load(f)
        if isinstance(m, dict) and isinstance(m.get("turns"), list):
            return m
    except Exception:
        pass
    return {"turns": []}


def save_mem(m):
    try:
        m["turns"] = m.get("turns", [])[-HISTORY_KEEP:]
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False)
    except Exception:
        pass


def remember(u, a):
    m = load_mem()
    m.setdefault("turns", []).append({"u": u, "a": a, "ts": time.time()})
    save_mem(m)


# ---------------- 听 ----------------
_LIVE = {"rec": None}
_LIVE_READY = None


def _preload_asr():
    """模型后台读进内存，跟说话时间重叠；上一轮用完就清干净。"""
    global _LIVE_READY
    import threading, hear
    rec = _LIVE.get("rec")
    if rec is not None:
        try:
            rec.Reset()
        except Exception:
            pass
        return
    _LIVE_READY = threading.Event()
    t = threading.Thread(target=hear._load_model, args=(_LIVE, _LIVE_READY))
    t.daemon = True
    t.start()


def record(max_sec=6.0, fs=16000, block=0.15, sil_sec=0.6, thresh=None, device=None):
    """录一句话。麦克风选择和增益都交给 hear.py（它会实测那一路有信号再用），
    这里只负责把结果写进 WAV 并返回 16k 的样本。开着边录边认，说完基本也就认完了。"""
    import hear
    _preload_asr()
    return hear.record_with_vad(max_sec, WAV, sil_sec=sil_sec, thresh=thresh, live_rec=_LIVE)


def recognize(wav_path=WAV, fs=16000):
    """优先拿边录边认已经算好的结果；没有才重新跑一遍。"""
    import hear
    rec = _LIVE.get("rec")
    if rec is not None:
        try:
            import json as _j
            return _j.loads(rec.FinalResult()).get("text", "")
        except Exception:
            pass
    return hear.recognize(wav_path)

def _post(messages, temperature=0.7, max_tokens=160, timeout=30):
    import urllib.request
    key = open(KEY_FILE, "r", encoding="utf-8").read().strip()
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + key)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    return obj["choices"][0]["message"]["content"].strip()


def build_messages(text):
    """把最近几轮对话接上，让它记得上下文。"""
    m = load_mem()
    msgs = [{"role": "system", "content": SYSTEM_PROMPT + MOOD_RULE}]
    for t in m.get("turns", [])[-HISTORY_TURNS:]:
        u = str(t.get("u", "")).strip()
        a = str(t.get("a", "")).strip()
        if u and a:
            msgs.append({"role": "user", "content": u})
            msgs.append({"role": "assistant", "content": a})
    msgs.append({"role": "user", "content": text})
    return msgs


def ask_glm(text, timeout=30):
    return _post(build_messages(text), temperature=0.7, max_tokens=160, timeout=timeout)


def ask_plain(text, sys_prompt, temperature=0.5, max_tokens=400, timeout=30):
    return _post([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": text},
    ], temperature=temperature, max_tokens=max_tokens, timeout=timeout)


def split_mood(raw):
    """第一行如果是情绪号就摘出来，剩下才是要说的话。"""
    if not raw:
        return 0, ""
    lines = raw.replace("\r\n", "\n").split("\n")
    mood = 0
    body_start = 0
    if lines:
        first = lines[0].strip()
        m = re.match(r"^[【\[]?([0-8])[】\]]?$", first)
        if m:
            mood = int(m.group(1))
            body_start = 1
    body = "\n".join(lines[body_start:]).strip()
    # 有些模型爱加「情绪：开心」这种文字，清掉
    body = re.sub(r"^[\-*·\s]*情绪[：:].*?\n", "", body).strip()
    body = body.strip("「」\"' ")
    if not body:
        body = raw.strip()
    return mood, body


# ---------------- 说 ----------------
def play_file(mp3path):
    """把 mp3 放出来。新版 miniaudio 没有 play_file，解码成 PCM 用 sounddevice 播。"""
    import miniaudio
    if hasattr(miniaudio, "play_file"):
        try:
            miniaudio.play_file(mp3path)
            return
        except Exception:
            pass
    import numpy as np
    dec = miniaudio.mp3_read_file_s16(mp3path)
    if isinstance(dec, tuple):
        samples, nch, fs = dec
    else:
        samples, nch, fs = dec.samples, dec.nchannels, dec.sample_rate
    pcm = np.frombuffer(samples, dtype=np.int16) if isinstance(samples, (bytes, bytearray)) else np.asarray(samples, dtype=np.int16)
    pcm = pcm.reshape(-1, nch)
    import sounddevice as sd
    sd.play(pcm, fs)
    sd.wait()

def speak(text):
    """在线合成，然后本地播放。失败就只写状态，不打断流程。"""
    if not text:
        return
    try:
        import edge_tts
        import miniaudio
        mp3 = os.path.join(BASE, "_say.mp3")
        asyncio.run(edge_tts.Communicate(text, VOICE).save(mp3))
        if not os.path.exists(mp3) or os.path.getsize(mp3) < 500:
            log("TTS_EMPTY")
            return
        play_file(mp3)
    except Exception as e:
        log("SPEAK_FAIL %r" % (e,))


# ---------------- 输出 ----------------
def emit(state, heard="", reply="", mood=0):
    """把一轮结果以一行 JSON 打到 stdout，给道的窗口读。"""
    print(json.dumps({"state": state, "heard": heard, "reply": reply, "mood": mood},
                     ensure_ascii=False), flush=True)


# ---------------- 主流程 ----------------
def do_chat():
    # 1) 听
    write_state("listening", note="我在听")
    try:
        audio = record()
    except Exception as e:
        log("REC_FAIL %r" % (e,))
        emit("error", reply="我的耳朵打不开，可能要看一下麦克风权限。")
        return 1

    import numpy as np
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)) if audio.size else 0.0)
    log("record_rms=%.1f" % rms)

    # 2) 识别
    write_state("thinking", note="我听着呢")
    try:
        text = recognize()
    except Exception as e:
        log("ASR_FAIL %r" % (e,))
        emit("error", reply="我耳朵这一下没使上劲，再点我一次。")
        return 1

    text = (text or "").strip()
    log("heard=" + text)

    if not text:
        emit("empty", reply="我没听清，再说一遍？")
        return 0

    # 3) 想（带上下文 + 情绪）
    write_state("thinking", heard=text, note="我想想")
    try:
        raw = ask_glm(text)
    except Exception as e:
        log("LLM_FAIL %r" % (e,))
        emit("error", heard=text, reply="这会儿脑子没连上，等会儿再跟我说。")
        return 1

    mood, reply = split_mood(raw)
    if not reply:
        reply = "嗯，我在听。"
    log("reply=" + reply + " mood=%d" % mood)
    remember(text, reply)
    emit("done", heard=text, reply=reply, mood=mood)
    write_state("done", heard=text, reply=reply, mood=mood)
    return 0


def pick_text(args):
    """参数可能是 --file 路径，也可能直接是一句话。"""
    for i, a in enumerate(args):
        if a == "--file" and i + 1 < len(args):
            p = args[i + 1]
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    return f.read().strip()
            except Exception as e:
                log("FILE_FAIL %r" % (e,))
                return ""
    if args:
        return " ".join(args).strip()
    # 没参数就看 ask.txt（窗口那边写中文更稳）
    try:
        with open(ASK_FILE, "r", encoding="utf-8-sig") as f:
            return f.read().strip()
    except Exception:
        return ""


def do_ask(args):
    text = pick_text(args)
    if not text:
        emit("empty", reply="没给我话呀。")
        return 0
    write_state("thinking", heard=text, note="我想想")
    try:
        raw = ask_glm(text)
    except Exception as e:
        log("LLM_FAIL %r" % (e,))
        emit("error", heard=text, reply="脑子这会儿没连上。")
        return 1
    mood, reply = split_mood(raw)
    remember(text, reply)
    emit("done", heard=text, reply=reply, mood=mood)
    write_state("done", heard=text, reply=reply, mood=mood)
    return 0


def do_side(args, sys_prompt, mood=7, kind="translate"):
    """翻译 / 讲题 / 总结：都是同一套，换提示词而已。"""
    text = pick_text(args)
    if not text:
        emit("empty", reply="没给我内容呀。")
        return 0
    write_state("thinking", heard=text, note="我看看")
    try:
        reply = ask_plain(text, sys_prompt)
    except Exception as e:
        log("%s_FAIL %r" % (kind.upper(), e))
        emit("error", heard=text, reply="脑子这会儿没连上。")
        return 1
    reply = (reply or "").strip().strip("「」\"' ")
    if not reply:
        reply = "这个我没弄明白。"
    log("%s=%s" % (kind, reply))
    emit("done", heard=text, reply=reply, mood=mood)
    write_state("done", heard=text, reply=reply, mood=mood)
    return 0


def do_listen():
    audio = record()
    import numpy as np
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))) if audio.size else 0.0
    text = recognize()
    print(json.dumps({"rms": round(rms, 1), "text": text}, ensure_ascii=False))
    return 0


def do_probe():
    out = {}
    try:
        import vosk
        out["vosk"] = "ok"
    except Exception as e:
        out["vosk"] = "fail %r" % (e,)
    out["model"] = os.path.isdir(MODEL_DIR)
    try:
        import sounddevice as sd
        out["sounddevice"] = "ok"
    except Exception as e:
        out["sounddevice"] = "fail %r" % (e,)
    try:
        import edge_tts
        out["edge_tts"] = "ok"
    except Exception as e:
        out["edge_tts"] = "fail %r" % (e,)
    try:
        import miniaudio
        out["miniaudio"] = "ok"
    except Exception as e:
        out["miniaudio"] = "fail %r" % (e,)
    try:
        out["key"] = len(open(KEY_FILE, "r", encoding="utf-8").read().strip())
    except Exception as e:
        out["key"] = "fail %r" % (e,)
    out["mem"] = os.path.exists(MEM_FILE)
    print(json.dumps(out, ensure_ascii=False))
    return 0


def main():
    if len(sys.argv) < 2:
        print("usage: voice.py chat|listen|say|ask|translate|explain|sum|probe")
        return 2
    cmd = sys.argv[1]
    args = sys.argv[2:]
    try:
        if cmd == "chat":
            return do_chat()
        if cmd == "listen":
            return do_listen()
        if cmd == "say":
            speak(" ".join(args) if args else "你好，我是道。")
            return 0
        if cmd == "ask":
            return do_ask(args)
        if cmd == "translate":
            return do_side(args, P_TRANSLATE, mood=7, kind="translate")
        if cmd == "explain":
            return do_side(args, P_EXPLAIN, mood=7, kind="explain")
        if cmd == "sum":
            return do_side(args, P_SUM, mood=8, kind="sum")
        if cmd == "story":
            return do_side(args, P_STORY, mood=1, kind="story")
        if cmd == "joke":
            return do_side(args, P_JOKE, mood=1, kind="joke")
        if cmd == "novel":
            return do_side(args, P_NOVEL, mood=6, kind="novel")
        if cmd == "probe":
            return do_probe()
        return 2
    except Exception as e:
        log("MAIN_FAIL %r" % (e,))
        log(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
