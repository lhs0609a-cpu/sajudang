# -*- coding: utf-8 -*-
"""
장면의 소리를 **짓는다** — 돌아도 이음새가 안 생기게.

★ 왜 지어야 했나 (2026-09-07)

  손님이 말했습니다 — "어떤 페이지던 애니메이션 들어간건 다 소리가
  나와야해". 그래서 재 보니 들어온 클립 열셋 중 **소리가 붙은 것은
  하나**(도령의 첫인사)뿐이었습니다. 나머지 열둘은 트랙 자체가
  없어서, 스위치를 켜도 켜지는 것이 없었습니다.

      char/pungun/greet.webm   소리 opus
      scene/*/clip.webm        소리 없음   ← 열둘 전부

  소리를 발주해서 받아 넣을 수도 있지만, 그때까지 열두 화면이
  조용합니다. 배경의 결(room tone)은 가락이 아니라 **결**이라
  지을 수 있습니다. 지어 넣고, 나중에 진짜 녹음이 오면 같은
  이름으로 덮으면 됩니다.

★ 소리는 영상에 안 굽습니다 — 따로 냅니다

  영상에 트랙을 붙이면 `<video loop>` 가 되도는 자리에서 소리가
  빕니다. 그 까닭은 `lib/sound.ts` 머리에 적어 두었습니다 —
  인코더가 앞뒤에 무음을 붙이고, 되도는 자리를 브라우저가 늦게
  잡습니다. 4.5초짜리 배경이면 한 시간에 **팔백 번** 딸깍합니다.

  그래서 그림은 영상이 돌리고 소리는 Web Audio 가 돌립니다.
  샘플 단위로 도니 한 톨도 안 빕니다. 덤으로 영상 길이(4.5초)와
  소리 길이(24초)가 달라도 됩니다 — 오히려 그래야 4.5초마다
  같은 소리가 나는 걸 손님이 못 알아챕니다.

★ 어떻게 이음새를 없애나 — 자르지 않고 **처음부터 원으로 짓는다**

  받아서 자르면 자른 자리가 남습니다. 그래서 파형을 아예 주기가
  N 샘플인 원으로 만듭니다. 세 가지 재료가 다 원입니다.

    ① 결(노이즈)   흰 소음을 주파수로 풀어(rfft) 결을 입히고 다시
                   묶습니다(irfft). 되묶은 파형은 **정의상 순환**
                   입니다 — 끝과 처음이 이어집니다.
    ② 알갱이(삐걱·달그락·바스락)
                   자리를 잡고 **원을 돌려서**(modulo) 얹습니다.
                   끝을 넘으면 처음으로 넘어갑니다.
    ③ 드론(제단의 울림)
                   주파수를 k/N 로만 씁니다. 정수 k 면 한 바퀴에
                   딱 k 번 돕니다.

  ★ 시간에 따라 변하는 필터는 **안 씁니다.** 그건 원을 깹니다.
    대신 결이 다른 두 벌을 만들어 놓고 **주기가 맞는 LFO 로
    오갑니다** — 바람이 불었다 잦아드는 것이 이렇게 나옵니다.

  다 짓고 나서 이음새를 잽니다. 끝과 처음의 단차가 이웃한 두 샘플의
  보통 단차보다 크면 안 됩니다 (`--check` 가 찍습니다).

★ 결이 여섯 벌인 까닭 — 장면마다가 아니라 **자리마다**

  장면은 스물여섯인데 결은 여섯입니다. 소리는 그림과 달라서, 같은
  방에서 찍은 다른 컷은 **같은 방 소리**가 나야 맞습니다. 컷마다
  소리를 갈면 손님은 방을 옮겨 다니는 것처럼 듣습니다.

      hall     대청 — 넓은 나무 방, 먼 삐걱임
      study    서재 — 종이 바스락, 붓, 아주 가까운 방
      outside  바깥 — 바람이 불었다 잦아들고, 먼 풀벌레
      altar    제단 — 낮은 울림과 이따금 종
      tray     상   — 사기 달그락, 물, 가까운 방
      card     문양 — 결만 남은 반짝임 (거의 무음)

★ 쓰는 법

    python tools/make_ambience.py            # 여섯 벌을 짓는다
    python tools/make_ambience.py --check    # 이음새만 잰다
    python tools/make_ambience.py --only hall

  넣는 곳은 `apps/web/public/audio/bgm/{이름}.mp3` 입니다
  (`lib/sound.ts` 의 `src()` 가 보는 자리).

  numpy 와 ffmpeg 이 필요합니다. 배포 이미지에는 안 들어갑니다 —
  requirements-dev.txt 쪽입니다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:                                      # pragma: no cover
    print("numpy 가 필요하오:  uv pip install --python <venv> numpy")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps" / "web" / "public" / "audio" / "bgm"
# 잰 값을 적어 두는 자리. 검사는 ffmpeg 없이 이 기록과 파일만 봅니다
# (이 저장소는 skip 0 입니다 — 검사가 도구를 부르면 없는 데서 건너뜁니다).
RECORD = ROOT / "seed" / "ambience.json"

SR = 44100
DUR = 24.0                     # 한 바퀴(초). 영상(2~10초)과 안 맞아야 좋습니다
N = int(SR * DUR)
BITRATE = "96k"

# 배경은 깔리는 것이라 낮게 냅니다. 화면에서 다시 0.22 를 곱합니다
# (`lib/sound.ts` VOL_BGM) — 여기서는 **파형이 안 깨질 만큼**만.
PEAK = 0.72


# ══════════════════════════════════════════════════════════════
#   원을 깨지 않는 재료 셋
# ══════════════════════════════════════════════════════════════

def _rng(seed: int) -> np.random.Generator:
    """씨앗을 박습니다 — 다시 지으면 같은 소리가 나와야 합니다."""
    return np.random.default_rng(seed)


def circ_noise(seed: int, tilt: float, lo: float, hi: float,
               rolloff: float = 2.0) -> np.ndarray:
    """
    **순환하는** 소음 한 벌.

    흰 소음을 주파수로 풀어 결을 입히고 되묶습니다. 되묶은 파형은
    주기가 N 인 원이라, 끝에서 처음으로 넘어가도 파형이 안 끊깁니다.

    tilt      1/f^tilt — 클수록 낮은 쪽으로 기웁니다 (0=흰, 2=붉은)
    lo, hi    이 바깥은 부드럽게 깎습니다 (Hz)
    rolloff   깎는 기울기. 클수록 급합니다
    """
    r = _rng(seed)
    spec = r.normal(size=N // 2 + 1) + 1j * r.normal(size=N // 2 + 1)
    f = np.fft.rfftfreq(N, 1.0 / SR)
    f[0] = f[1]                                   # 0Hz 에서 나눗셈을 피합니다

    env = f ** (-tilt)
    # 아래·위를 부드럽게 깎습니다. 벽처럼 자르면 그 자리가 「웅」 합니다.
    env *= 1.0 / (1.0 + (lo / f) ** (2 * rolloff))
    env *= 1.0 / (1.0 + (f / hi) ** (2 * rolloff))

    spec *= env
    spec[0] = 0.0                                 # 직류는 뺍니다
    x = np.fft.irfft(spec, n=N)
    return _unit(x)


def lfo(cycles: int, phase: float = 0.0) -> np.ndarray:
    """
    한 바퀴에 **정확히 `cycles` 번** 도는 물결. 0~1 사이.

    정수라야 원이 안 깨집니다. 1.5 번 돌면 끝과 처음이 어긋납니다.
    """
    t = np.arange(N) / float(N)
    return 0.5 + 0.5 * np.sin(2.0 * np.pi * cycles * t + phase)


def partial(cycles: int, amp: float = 1.0, phase: float = 0.0) -> np.ndarray:
    """한 바퀴에 `cycles` 번 도는 사인. 주파수는 cycles/DUR Hz 입니다."""
    t = np.arange(N) / float(N)
    return amp * np.sin(2.0 * np.pi * cycles * t + phase)


def hz(freq: float) -> int:
    """Hz 를 **원이 안 깨지는** 가장 가까운 값으로 접습니다."""
    return max(1, int(round(freq * DUR)))


def scatter(buf: np.ndarray, grain: np.ndarray, at: int) -> None:
    """
    알갱이 하나를 **원을 돌려서** 얹습니다.

    끝을 넘으면 처음으로 넘어갑니다. 그래서 이음새 근처에 떨어진
    소리도 잘리지 않고 넘어가서 이어집니다 — 자른 소리가 하나라도
    있으면 거기서 딸깍합니다.
    """
    idx = (at + np.arange(grain.size)) % N
    np.add.at(buf, idx, grain)


def grain_noise(seed: int, secs: float, lo: float, hi: float,
                attack: float = 0.02, tilt: float = 0.0) -> np.ndarray:
    """바스락·쉬익 — 띠를 좁힌 소음 한 알갱이."""
    r = _rng(seed)
    n = max(8, int(secs * SR))
    spec = r.normal(size=n // 2 + 1) + 1j * r.normal(size=n // 2 + 1)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f[0] = f[1]
    env = f ** (-tilt)
    env *= 1.0 / (1.0 + (lo / f) ** 4)
    env *= 1.0 / (1.0 + (f / hi) ** 4)
    spec *= env
    spec[0] = 0.0
    g = np.fft.irfft(spec, n=n)

    t = np.arange(n) / float(SR)
    a = max(1e-4, attack * secs)
    shape = np.minimum(t / a, 1.0) * np.exp(-t / (secs * 0.32))
    return _unit(g) * shape


def grain_tone(secs: float, freqs, decays, amps) -> np.ndarray:
    """
    달그락·종·삐걱 — 몇 개의 부분음이 각자 다르게 잦아드는 알갱이.

    부분음 사이가 정수배가 아니어야 쇠·사기 소리가 납니다. 정수배로
    맞추면 그건 악기 소리가 됩니다.
    """
    n = max(8, int(secs * SR))
    t = np.arange(n) / float(SR)
    g = np.zeros(n)
    for fr, dc, am in zip(freqs, decays, amps):
        g += am * np.sin(2.0 * np.pi * fr * t) * np.exp(-t / dc)
    g *= np.minimum(t / 0.002, 1.0)               # 딸깍을 막는 아주 짧은 어택
    return _unit(g)


def _unit(x: np.ndarray) -> np.ndarray:
    m = float(np.max(np.abs(x)))
    return x / m if m > 1e-12 else x


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x * x)))


def at(level: float, x: np.ndarray) -> np.ndarray:
    """이 결을 이만한 크기(RMS)로 맞춥니다."""
    r = rms(x)
    return x * (level / r) if r > 1e-12 else x


# ══════════════════════════════════════════════════════════════
#   결 여섯 벌
# ══════════════════════════════════════════════════════════════

def bed_hall() -> np.ndarray:
    """대청 — 넓은 나무 방. 낮게 숨 쉬고, 이따금 먼 데서 삐걱."""
    # 방의 결 두 벌을 오갑니다 — 넓은 데서 공기가 도는 느낌
    a = circ_noise(101, tilt=1.7, lo=38, hi=380)
    b = circ_noise(102, tilt=1.9, lo=30, hi=210)
    sway = lfo(1)
    room = at(0.085, a * sway + b * (1.0 - sway))

    air = at(0.011, circ_noise(103, tilt=0.6, lo=1800, hi=9000))

    creak = np.zeros(N)
    r = _rng(104)
    for i in range(5):
        f0 = float(r.uniform(150.0, 330.0))
        g = grain_tone(0.45,
                       freqs=[f0, f0 * 2.41, f0 * 3.77],
                       decays=[0.16, 0.09, 0.05],
                       amps=[1.0, 0.42, 0.18])
        scatter(creak, g * float(r.uniform(0.30, 0.62)), int(r.integers(0, N)))
    creak = at(0.020, creak)

    return room + air + creak


def bed_study() -> np.ndarray:
    """서재 — 아주 가까운 방. 종이가 바스락거리고 이따금 붓이 지나감."""
    a = circ_noise(201, tilt=2.0, lo=32, hi=240)
    b = circ_noise(202, tilt=1.8, lo=45, hi=160)
    sway = lfo(2)
    room = at(0.055, a * sway + b * (1.0 - sway))

    paper = np.zeros(N)
    r = _rng(203)
    for i in range(16):
        g = grain_noise(300 + i, float(r.uniform(0.09, 0.26)),
                        lo=1200.0, hi=7200.0, attack=0.12, tilt=-0.3)
        scatter(paper, g * float(r.uniform(0.35, 1.0)), int(r.integers(0, N)))
    paper = at(0.030, paper)

    brush = np.zeros(N)
    r = _rng(204)
    for i in range(3):
        g = grain_noise(400 + i, float(r.uniform(0.42, 0.68)),
                        lo=380.0, hi=2600.0, attack=0.35, tilt=0.4)
        scatter(brush, g * 0.8, int(r.integers(0, N)))
    brush = at(0.018, brush)

    air = at(0.006, circ_noise(205, tilt=0.5, lo=2600, hi=10000))
    return room + paper + brush + air


def bed_outside() -> np.ndarray:
    """바깥 — 바람이 불었다 잦아들고, 아주 먼 데서 풀벌레."""
    # ★ 바람은 **필터를 흔들어** 만드는 것이 보통인데 그러면 원이
    #   깨집니다. 그래서 결이 다른 두 벌을 주기가 맞는 물결로 오갑니다.
    calm = circ_noise(501, tilt=1.5, lo=60, hi=900)
    gust = circ_noise(502, tilt=0.9, lo=90, hi=2800)
    w = 0.30 * lfo(1) + 0.45 * lfo(2, 1.1) + 0.25 * lfo(3, 2.3)
    wind = at(0.090, calm * (1.0 - w) + gust * w)

    rumble = at(0.030, circ_noise(503, tilt=2.2, lo=22, hi=110))

    bugs = np.zeros(N)
    r = _rng(504)
    for i in range(9):
        f0 = float(r.uniform(5200.0, 8200.0))
        g = grain_tone(0.05, freqs=[f0, f0 * 1.51],
                       decays=[0.012, 0.008], amps=[1.0, 0.5])
        scatter(bugs, g * float(r.uniform(0.4, 1.0)), int(r.integers(0, N)))
    bugs = at(0.0055, bugs)

    return wind + rumble + bugs


def bed_altar() -> np.ndarray:
    """제단 — 낮게 깔린 울림. 맥놀이가 아주 느리게 오가고 이따금 종."""
    # 부분음을 k/DUR 로만 씁니다. 두 개를 조금 벌려 놓으면 맥놀이가
    # 생깁니다 — 벌린 만큼(Δk/DUR Hz)이 곧 맥놀이 빠르기입니다.
    base = hz(98.0)
    drone = (partial(base, 1.00)
             + partial(base + 34, 0.62)            # 34/24 ≈ 1.4Hz 맥놀이
             + partial(base * 2, 0.34)
             + partial(base * 2 + 51, 0.20)
             + partial(base * 3, 0.13))
    breathe = 0.55 + 0.45 * lfo(1)
    drone = at(0.070, drone * breathe)

    room = at(0.030, circ_noise(601, tilt=1.9, lo=34, hi=300))

    bell = np.zeros(N)
    r = _rng(602)
    for i in range(2):
        f0 = float(r.uniform(430.0, 520.0))
        g = grain_tone(3.6,
                       freqs=[f0, f0 * 2.76, f0 * 5.40, f0 * 8.93],
                       decays=[1.9, 1.1, 0.62, 0.30],
                       amps=[1.0, 0.5, 0.26, 0.12])
        scatter(bell, g * 0.55, int(r.integers(0, N)))
    bell = at(0.022, bell)

    return drone + room + bell


def bed_tray() -> np.ndarray:
    """상 — 가까운 방. 사기가 달그락, 물이 아주 낮게."""
    room = at(0.050, circ_noise(701, tilt=1.9, lo=36, hi=260))

    a = circ_noise(702, tilt=0.8, lo=320, hi=1500)
    b = circ_noise(703, tilt=1.1, lo=260, hi=900)
    sway = lfo(2, 0.7)
    water = at(0.024, a * sway + b * (1.0 - sway))

    clink = np.zeros(N)
    r = _rng(704)
    for i in range(11):
        f0 = float(r.uniform(1500.0, 4200.0))
        g = grain_tone(0.30,
                       freqs=[f0, f0 * 2.13, f0 * 3.41],
                       decays=[0.11, 0.06, 0.035],
                       amps=[1.0, 0.44, 0.20])
        scatter(clink, g * float(r.uniform(0.22, 0.60)), int(r.integers(0, N)))
    clink = at(0.020, clink)

    return room + water + clink


def bed_card() -> np.ndarray:
    """문양 — 결만 남은 반짝임. 거의 무음이라야 합니다."""
    shimmer = np.zeros(N)
    for k, amp, ph in ((hz(3100), 1.00, 0.0), (hz(4180), 0.62, 1.3),
                       (hz(5470), 0.40, 2.6), (hz(7020), 0.24, 0.4)):
        shimmer += partial(k, amp, ph) * (0.35 + 0.65 * lfo(2 + (k % 3), ph))
    shimmer = at(0.011, shimmer)

    room = at(0.020, circ_noise(801, tilt=2.0, lo=30, hi=180))
    return shimmer + room


BEDS = {
    "hall": bed_hall,
    "study": bed_study,
    "outside": bed_outside,
    "altar": bed_altar,
    "tray": bed_tray,
    "card": bed_card,
}


# ══════════════════════════════════════════════════════════════
#   재고 · 굽고
# ══════════════════════════════════════════════════════════════

def seam(x: np.ndarray) -> tuple[float, float, float]:
    """
    이음새를 잽니다 — 끝에서 처음으로 넘어가는 단차가 **이웃한 두
    샘플의 보통 단차**보다 크면 거기서 딸깍합니다.

    돌아오는 값: (넘어가는 단차, 보통 단차, 그 배수)
    """
    step = float(np.median(np.abs(np.diff(x))))
    wrap = float(abs(x[0] - x[-1]))
    return wrap, step, (wrap / step if step > 1e-12 else 0.0)


def stereo(mono: np.ndarray, seed: int) -> np.ndarray:
    """
    좌우를 아주 조금 벌립니다. 벌린 쪽도 **원**이라야 합니다.

    한쪽을 늦추는 것으로 벌리면 이음새가 깨지므로, 결이 다른 한 벌을
    조금 섞습니다.
    """
    side = circ_noise(seed, tilt=1.4, lo=120, hi=6000) * rms(mono) * 0.16
    return np.stack([mono + side, mono - side], axis=1)


def bake(name: str, check_only: bool) -> bool:
    x = BEDS[name]()
    wrap, step, ratio = seam(x)
    ok = ratio <= 4.0
    mark = "이어짐" if ok else "★ 끊김"
    print("  %-8s %s  이음새 %.2e / 보통 %.2e = %.2f배  RMS %.3f"
          % (name, mark, wrap, step, ratio, rms(x)))
    if not ok or check_only:
        return ok

    st = stereo(x, seed=hash(name) % 9973 + 900)
    peak = float(np.max(np.abs(st)))
    if peak > 1e-9:
        st = st * (PEAK / peak)

    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / ("%s.mp3" % name)
    raw = st.astype("<f4").tobytes()
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "pipe:0",
           "-c:a", "libmp3lame", "-b:a", BITRATE, str(dst)]
    p = subprocess.run(cmd, input=raw, capture_output=True)
    if p.returncode != 0:
        print("     ffmpeg 이 넘어졌소: %s" % p.stderr.decode("utf-8", "replace")[-300:])
        return False
    print("     → %s  %.0fKB" % (dst.relative_to(ROOT), dst.stat().st_size / 1024))
    return True


def measure(path: Path) -> dict:
    """
    구워 놓은 것을 **되풀어서** 다시 잽니다.

    ★ 왜 짓고 나서 또 재나 (2026-09-07)

      원(파형)이 아무리 완벽해도 mp3 로 굽는 순간 달라집니다. 인코더가
      프레임을 1152 샘플로 끊고 앞뒤에 없던 무음을 붙입니다. 지을 때
      잰 값은 **구운 것의 값이 아닙니다.** 손님이 듣는 것은 구운
      쪽이니 그쪽을 재야 합니다.

    ★ 무엇과 견주나 — **파형 안 아무 데나 자른 것**

      「이음새가 작다」는 그 자체로는 뜻이 없습니다. 낮은 드론은 이웃
      샘플 차가 원래 작아서 조금만 어긋나도 배수가 커 보이고, 소음은
      그 반대입니다.

      그래서 **한 바퀴 도는 자리의 단차**를 **파형 안에서 아무 데나
      잘랐을 때 생기는 단차(99퍼센타일)**와 견줍니다. 도는 자리가
      안쪽 아무 데보다 얌전하면, 그 자리는 특별한 데가 아닙니다.
      귀에는 그게 「안 끊긴다」입니다.
    """
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le",
         "-ac", "1", "-ar", str(SR), "pipe:1"],
        capture_output=True).stdout
    x = np.frombuffer(raw, "<f4").astype(np.float64)
    if x.size < SR:
        return {"error": "되풀지 못했소"}
    level = float(np.sqrt(np.mean(x * x)))
    inside = float(np.percentile(np.abs(np.diff(x)), 99))
    wrap = float(abs(x[0] - x[-1]))
    return {
        "seconds": round(x.size / float(SR), 3),
        "wrap": round(wrap / level, 4),        # 도는 자리의 단차
        "inside": round(inside / level, 4),    # 안쪽 아무 데의 단차
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def record(names: list[str]) -> int:
    got = {}
    for n in names:
        p = OUT / ("%s.mp3" % n)
        if not p.exists():
            print("  %-8s ★ 파일이 없소 — 먼저 구우시오" % n)
            return 1
        m = measure(p)
        if "error" in m:
            print("  %-8s ★ %s" % (n, m["error"]))
            return 1
        ok = m["wrap"] <= m["inside"]
        print("  %-8s %s  도는 자리 %.4f ≤ 안쪽 %.4f  %.1f초 %.0fKB"
              % (n, "이어짐" if ok else "★ 끊김",
                 m["wrap"], m["inside"], m["seconds"], m["bytes"] / 1024))
        if not ok:
            print("     구운 뒤에 도는 자리가 안쪽보다 거칠어졌소.")
            return 1
        got[n] = m

    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps({"beds": got, "seconds": DUR, "rate": SR},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("\n기록: %s" % RECORD.relative_to(ROOT))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="이음새만 재고 안 굽는다")
    ap.add_argument("--record", action="store_true",
                    help="구워 둔 것을 되풀어 재고 seed/ambience.json 에 적는다")
    ap.add_argument("--only", help="이 결 하나만")
    a = ap.parse_args()

    names = [a.only] if a.only else list(BEDS)
    for n in names:
        if n not in BEDS:
            print("그런 결은 없소: %s (있는 것: %s)" % (n, " ".join(BEDS)))
            return 1

    if a.record:
        print("구운 소리를 되풀어 재오")
        return record(names)

    print("장면 소리 — 한 바퀴 %.0f초 · %dHz" % (DUR, SR))
    bad = [n for n in names if not bake(n, a.check)]
    if bad:
        print("\n끊기는 결: %s" % " ".join(bad))
        return 1
    if a.check:
        print("\n%d 벌 쟀소" % len(names))
        return 0
    print("\n%d 벌 구웠소 — 이제 되풀어 잽니다" % len(names))
    return record(names)


if __name__ == "__main__":
    sys.exit(main())
