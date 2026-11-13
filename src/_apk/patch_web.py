# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path

SRC = Path(r"E:\Daodao\道-随身版.html")
DST = Path(r"C:\Users\Administrator\Doubao\chats\2026-11-06\_apk\assets\dao.html")
REP = Path(r"C:\Users\Administrator\Doubao\chats\2026-11-06\_patch.txt")

t = SRC.read_text(encoding="utf-8")
log = []

def rep(old, new, name, must=1):
    global t
    n = t.count(old)
    if n != must:
        log.append("FAIL %s count=%d (expect %d)" % (name, n, must))
        return False
    t = t.replace(old, new, must)
    log.append("OK %s" % name)
    return True

# 1) CSS 追加
old_css = "  #hint {\n"
new_css = """  #bar { padding: 10px 4px 14px; }
  #bar button { width: 23%; margin: 0 1%; padding: 11px 0; font-size: 12.5px; }
  #ask {
    position: fixed; left: 0; right: 0; bottom: 0; padding: 10px 10px 14px;
    background: rgba(10,16,32,.96); display: none; gap: 8px;
    border-top: 1px solid rgba(130,170,255,.22);
    z-index: 20;
  }
  #ask.show { display: flex; }
  #askInput {
    flex: 1; min-width: 0; padding: 11px 13px; border-radius: 12px; font-size: 15px;
    background: rgba(255,255,255,.08); border: 1px solid rgba(130,170,255,.32);
    color: #e6edff; outline: none; font-family: inherit; user-select: text;
  }
  #askSend {
    width: auto; margin: 0; padding: 11px 18px; border-radius: 12px;
    background: rgba(118,158,255,.30); flex: none;
  }
  #hint {
"""
rep(old_css, new_css, "css")

# 2) 底部按钮
old_bar = """  <div id="bar">
    <button id="btnTalk">说句话</button>
    <button id="btnMood">换表情</button>
    <button id="btnSwap">换形象</button>
  </div>"""
new_bar = """  <div id="bar">
    <button id="btnTalk">跟它说话</button>
    <button id="btnMood">换表情</button>
    <button id="btnSwap">换形象</button>
    <button id="btnKnow">看知识</button>
  </div>
  <div id="ask">
    <input id="askInput" type="text" placeholder="跟道说句话……" autocomplete="off">
    <button id="askSend">发送</button>
  </div>"""
rep(old_bar, new_bar, "bar")

# 3) 说话按钮改为打开输入
old_btn = """  document.getElementById('btnTalk').addEventListener('click', function () {
    say(LINES[Math.floor(Math.random() * LINES.length)]);
    waveLeft = 1.4; mode = 'wave';
  });"""
new_btn = """  document.getElementById('btnTalk').addEventListener('click', function () {
    openAsk();
  });"""
rep(old_btn, new_btn, "btnTalk")

# 4) 点它时的话术改用全量池
old_say = "    say(LINES[Math.floor(Math.random() * LINES.length)]);"
new_say = "    say(allLines()[Math.floor(Math.random() * allLines().length)]);"
rep(old_say, new_say, "poke_say")

# 5) 插入大脑逻辑
old_tail = "\n  resize();\n})();"
new_tail = """
  /* ========== 大脑 & 自我更新 ========== */
  var extraLines = [];
  var waitingIds = {};
  var seq = 0;
  var askBox = document.getElementById('ask');
  var askInput = document.getElementById('askInput');

  function allLines() { return LINES.concat(extraLines); }

  function loadExtras() {
    if (!window.DaoNative) return;
    try {
      var a = JSON.parse(DaoNative.getLines());
      if (a && a.length) extraLines = a;
    } catch (e) {}
  }

  function openAsk() {
    if (!askBox) return;
    askBox.classList.add('show');
    try { askInput.value = ''; askInput.focus(); } catch (e) {}
  }

  function closeAsk() { if (askBox) askBox.classList.remove('show'); }

  function setMoodByCode(m) {
    if (!m) { mood = 0; moodLeft = 0; return; }
    mood = (m === 7 || m === 8) ? (m === 8 ? 1 : 4) : m;
    moodLeft = 3.4;
  }

  function askBrain(text) {
    if (!window.DaoNative) { say('我这会儿没有大脑，得回电脑上才行。'); return; }
    var id = 'q' + (++seq);
    waitingIds[id] = 1;
    bubble.classList.add('show');
    bubble.textContent = '……';
    waveLeft = 1.8; mode = 'wave';
    DaoNative.chat(text, id);
  }

  window.__daoReply = function (id, reply, m) {
    if (!waitingIds[id]) return;
    delete waitingIds[id];
    setMoodByCode(m);
    say(reply || '嗯……');
  };

  window.__daoUpdated = function (changed) {
    loadExtras();
    if (changed) say('我又学了点新东西，点「看知识」能瞧见。');
  };

  function showKnow() {
    if (!window.DaoNative) { say('知识库要在手机 App 里才看得到。'); return; }
    var d = {};
    try { d = JSON.parse(DaoNative.getKnowledge()); } catch (e) {}
    var cnt = d.count || 0, ln = d.lines || 0, today = d.today || '';
    var txt = '我已经学了 ' + cnt + ' 条，话也多了 ' + ln + ' 句。';
    if (today) txt += '今天学到：' + today;
    else txt += '今天还没学到新的，等会儿我再去看看。';
    say(txt);
    waveLeft = 1.4; mode = 'wave';
  }

  if (askBox) {
    document.getElementById('askSend').addEventListener('click', function () {
      var v = askInput.value.trim();
      if (!v) return;
      closeAsk(); askBrain(v);
    });
    askInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var v = askInput.value.trim();
        if (!v) return;
        closeAsk(); askBrain(v);
      }
    });
  }

  document.getElementById('btnKnow').addEventListener('click', showKnow);

  setTimeout(function () {
    loadExtras();
    if (window.DaoNative) { try { DaoNative.autoUpdate(); } catch (e) {} }
  }, 1500);

  resize();
})();"""
rep(old_tail, new_tail, "tail")

log.append("final_len=%d" % len(t))

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(t, encoding="utf-8")

good = (len([x for x in log if x.startswith("OK")]) == 5)
log.append("RESULT=%s" % ("PASS" if good else "FAIL"))
REP.write_text("\r\n".join(log), encoding="utf-8-sig")
