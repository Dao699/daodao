# -*- coding: utf-8 -*-
"""播放一句合成好的语音：mp3/wav 都行，走系统默认扬声器。"""
import sys
import miniaudio
import numpy as np
import sounddevice as sd


def play_file(path):
    d = miniaudio.decode_file(path, output_format=miniaudio.SampleFormat.FLOAT32)
    a = np.frombuffer(d.samples, dtype=np.float32).copy()
    ch = int(d.nchannels)
    if ch > 1:
        a = a.reshape(-1, ch)
    sd.play(a, int(d.sample_rate))
    sd.wait()


def main():
    if len(sys.argv) < 2:
        print("USAGE: play_audio.py <file.mp3|file.wav>")
        sys.exit(1)
    try:
        play_file(sys.argv[1])
        print("PLAYED")
    except Exception as e:
        print("ERR " + repr(e))
        sys.exit(2)


if __name__ == "__main__":
    main()
