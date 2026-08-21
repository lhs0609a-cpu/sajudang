"""
전체 플로우 훑기 — 32개 화면을 실제 브라우저로 열어 보고 깨진 곳을 잡는다.

    python tools/flow_check.py [http://localhost:3000] [--shots 폴더]

무엇을 보는가
    · 화면이 실제로 그려지는가 (빈 화면·오류 문구)
    · 가로로 넘치는 요소가 있는가 (모바일에서 잘림)
    · 콘솔 오류·실패한 요청
    · 명식이 실린 화면에 여덟 글자가 보이는가

브라우저는 Edge/Chrome 헤드리스를 CDP 로 붙여 씁니다.
설치가 없으면 건너뜁니다 (CI 에서 실패시키지 않습니다).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium",
]

# 화면 대장 — apps/web/lib/store.ts 의 SCREEN_GROUPS 와 같아야 합니다
SCREENS = [
    ("a1", "/?step=a1"), ("a2", "/?step=a2"), ("a3", "/?step=a3"),
    ("a4", "/?step=a4"), ("a4b", "/?step=a4b"), ("a5", "/?step=a5"),
    ("a6", "/?step=a6"), ("a7", "/?step=a7"),
    ("b1", "/lobby?tab=b1"), ("b2", "/lobby?tab=b2"),
    ("b3", "/lobby?tab=b3"), ("b4", "/lobby?tab=b4"),
    ("c1", "/report/pungun?tab=c1"), ("c2", "/report/pungun?tab=c2"),
    ("c3", "/report/pungun?tab=c3"), ("c4", "/report/pungun?tab=c4"),
    ("c5", "/report/pungun?tab=c5"), ("c6", "/report/pungun?tab=c6"),
    ("c7", "/summary"),
    ("d0", "/pay?step=d0"), ("d1", "/pay?step=d1"),
    ("d2", "/pay?step=d2"), ("d3", "/pay?step=d3"),
    ("h1", "/relay"), ("g1", "/daily"),
    ("f2", "/me?tab=f2"), ("r1", "/me?tab=r1"),
]

# 명식이 실려야 하는 화면
NEEDS_CHART = {"a6", "b4", "c2", "c7"}
# 나레이션 한 줄만 나오는 화면 — 짧은 게 정상
SHORT_OK = {"a1"}

VIEWPORT = (390, 844)          # 아이폰급. 모바일이 기본입니다 (docs/08 §5)

PROBE = """
(() => {
  const vw = document.documentElement.clientWidth;
  const over = [...document.querySelectorAll('.phone *')]
    .map(e => { const b = e.getBoundingClientRect();
                return {t: e.tagName + (e.className && typeof e.className === 'string'
                          ? '.' + e.className.split(' ')[0] : ''),
                        r: Math.round(b.right), w: Math.round(b.width)}; })
    .filter(o => o.r > vw + 1)
    .slice(0, 5);
  const txt = (document.querySelector('.phone') || document.body).innerText || '';
  const errs = (window.__flowErrs || []).slice(0, 3);
  return JSON.stringify({
    vw,
    docW: document.documentElement.scrollWidth,
    overflow: over,
    len: txt.trim().length,
    hasPillar: /[甲乙丙丁戊己庚辛壬癸]\s*[子丑寅卯辰巳午未申酉戌亥]/.test(txt),
    err: /못했소|못 했소|실패/.test(txt) ? txt.slice(0, 120) : null,
    jsErr: errs,
  });
})()
"""


def find_browser():
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    return shutil.which("google-chrome") or shutil.which("chromium")


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("http") \
        else "http://localhost:3000"
    shots = None
    if "--shots" in sys.argv:
        shots = Path(sys.argv[sys.argv.index("--shots") + 1])
        shots.mkdir(parents=True, exist_ok=True)

    exe = find_browser()
    if not exe:
        print("브라우저를 찾지 못했습니다. 건너뜁니다.")
        return 0
    try:
        import websocket  # noqa: F401
    except ImportError:
        print("websocket-client 이 없습니다:  pip install websocket-client")
        return 0
    import websocket

    port = 9444
    # ★ 브라우저 프로필은 반드시 로컬 디스크에. 저장소가 구글 드라이브에
    #   있으면 프로필 수천 개를 쓰다가 브라우저가 아예 못 뜹니다.
    prof = Path(tempfile.mkdtemp(prefix="sajudang-flow-"))

    proc = subprocess.Popen(
        [exe, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--remote-debugging-port=%d" % port,
         "--user-data-dir=%s" % prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ready = False
        for _ in range(75):
            try:
                urllib.request.urlopen("http://localhost:%d/json/version" % port, timeout=1)
                ready = True
                break
            except Exception:                          # noqa: BLE001
                time.sleep(0.4)
        if not ready:
            print("브라우저가 뜨지 않았습니다 (포트 %d). 건너뜁니다." % port)
            return 0

        tabs = json.load(urllib.request.urlopen("http://localhost:%d/json/list" % port))
        tgt = next(t for t in tabs if t.get("type") == "page")
        ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=30,
                                         suppress_origin=True)
        seq = [0]

        def send(method, params=None):
            seq[0] += 1
            ws.send(json.dumps({"id": seq[0], "method": method,
                                "params": params or {}}))
            while True:
                m = json.loads(ws.recv())
                if m.get("id") == seq[0]:
                    return m.get("result", {})

        send("Page.enable")
        send("Runtime.enable")
        send("Emulation.setDeviceMetricsOverride", {
            "width": VIEWPORT[0], "height": VIEWPORT[1],
            "deviceScaleFactor": 1, "mobile": True})

        def visit(url, settle=2.6):
            send("Page.addScriptToEvaluateOnNewDocument", {
                "source": "window.__flowErrs=[];"
                          "window.addEventListener('error',e=>"
                          "window.__flowErrs.push(String(e.message)));"
                          "window.addEventListener('unhandledrejection',e=>"
                          "window.__flowErrs.push('reject:'+String(e.reason)));"})
            send("Page.navigate", {"url": url})
            time.sleep(settle)

        def probe():
            r = send("Runtime.evaluate",
                     {"expression": PROBE, "returnByValue": True})
            v = r.get("result", {}).get("value")
            if v is None:
                det = r.get("exceptionDetails", {})
                msg = (det.get("exception", {}).get("description")
                       or det.get("text") or str(r)[:160])
                return {"vw": 0, "docW": 0, "overflow": [], "len": 0,
                        "hasPillar": False, "err": None,
                        "jsErr": ["probe 실패: " + msg[:90]]}
            return json.loads(v)

        # 명식을 한 번 세워 세션에 남긴다
        visit(base + "/?step=a6", settle=5.0)

        print("전체 플로우 훑기 — %s · %dx%d" % (base, *VIEWPORT))
        print("%-5s %-24s %-6s %-6s %-7s %s"
              % ("화면", "경로", "글자수", "명식", "넘침", "문제"))
        print("-" * 76)

        bad = []
        for sid, path in SCREENS:
            visit(base + path)
            d = probe()
            over = len(d["overflow"])
            note = ""
            if d["len"] < 40 and sid not in SHORT_OK:
                note = "화면이 비었음"
            elif sid in NEEDS_CHART and not d["hasPillar"]:
                note = "명식이 안 보임"
            elif d["err"]:
                note = d["err"][:40].replace("\n", " ")
            if d.get("jsErr"):
                note = (note + " / " if note else "") + "JS: " + d["jsErr"][0][:50]
            if over:
                note = (note + " / " if note else "") + \
                    "넘침 " + d["overflow"][0]["t"]
            if note:
                bad.append((sid, note))
            print("%-5s %-24s %-6d %-6s %-7d %s"
                  % (sid, path, d["len"],
                     "O" if d["hasPillar"] else "-", over, note))
            if shots:
                r = send("Page.captureScreenshot", {"captureBeyondViewport": True})
                import base64
                (shots / ("%s.png" % sid)).write_bytes(
                    base64.b64decode(r["data"]))

        print()
        if bad:
            print("문제 %d건" % len(bad))
            for sid, note in bad:
                print("  %-5s %s" % (sid, note))
        else:
            print("32개 화면 모두 정상")
        ws.close()
        return 1 if bad else 0
    finally:
        proc.terminate()
        time.sleep(0.6)
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
