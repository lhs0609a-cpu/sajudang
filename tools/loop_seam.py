#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
루프 이음새 — 배경 영상이 다시 돌 때 튀는가.

★ 왜 이 도구가 필요한가

  화면의 배경은 전부 `loop` 로 **영원히** 돕니다. 그래서 손님이 실제로
  보는 것은 「5초짜리 그림」이 아니라 **이음새**입니다. 끝 프레임과 첫
  프레임이 다르면 5초마다 한 번씩 화면이 툭 끊깁니다.

  발주서(docs/10 §7)에 「루프는 첫·끝 프레임 일치」라고 적혀 있지만
  적어 두기만 해서는 지켜지지 않았습니다. **재는 자리가 없었습니다.**

★ 이음새를 만드는 방법 둘 — 그리고 **장면마다 답이 다릅니다**

  겹쳐 넘기기(xfade)  끝자락을 첫머리에 **겹쳐서** 넘깁니다. 앞으로만
                      갑니다. 겹치는 동안 두 그림이 포개지는데, 카메라가
                      안 움직이는 장면은 같은 자리에 같은 등불이 있고
                      불티만 다르므로 사람 눈에는 「불티가 좀 많은 순간」
                      으로 보입니다.
                      ← **가만히 있는 장면**은 이걸 씁니다.

  되감기(ping-pong)   앞으로 갔다가 되돌아옵니다. 첫·끝이 정확히 맞아
                      겹침이 아예 없습니다. 대신 시간이 거꾸로 흘러,
                      오르던 불티가 내려앉고 피던 연기가 빨려 들어갑니다.
                      그런데 **카메라가 미는 장면**(Dolly In)은 겹쳐
                      넘길 수가 없습니다 — 첫머리와 끝자락의 배율이
                      달라서 사람이 둘로 겹쳐 보입니다. 대청을 재보니
                      첫 프레임과 끝 프레임이 30.6이나 벌어져 있었고,
                      40프레임만 잘라도 18.1이었습니다. 밀고 들어간
                      만큼은 어떻게 잘라도 안 맞습니다.
                      ← **미는 장면**은 이걸 씁니다. 밀었다 물러나는
                        숨 쉬는 카메라가 되지, 튀지는 않습니다.

  ★ 되감을 때 **양 끝 프레임을 빼서** 되돕니다. 지금 들어와 있는 일곱은
    `f0‥f120 + f120‥f0` 이라 되도는 자리에서 같은 프레임이 두 번 나옵니다.
    24분의 1초씩 멈추는 것이라, 이것도 「끊긴다」의 한 조각입니다.

★ 나가는 길이

  겹쳐 넘기기  프레임 N 에서 F 를 겹치면 **N-F**.
    나가는 순서:  [F ‥ N-F-1]  그다음  blend([N-F ‥ N-1], [0 ‥ F-1])
      · 첫 프레임 = f(F)
      · 본문 끝 f(N-F-1) → 겹침 첫 f(N-F)          이어짐
      · 겹침 끝 ≈ f(F-1) → 다시 첫 프레임 f(F)      이어짐

  되감기      f0‥f(N-1) 그다음 f(N-2)‥f1 → **2N-2**. 멈추는 프레임 없음.

★ 되감겨 들어온 클립을 다시 손볼 때

  이미 되감긴 클립(241·242·252프레임)은 **앞 절반만** 원본으로 봅니다.
  뒤 절반은 앞 절반의 거울이라 버려도 잃는 것이 없습니다.

쓰기
    python tools/loop_seam.py                    # 전부 재기
    python tools/loop_seam.py --fix gate hall    # 지정한 것만 고치기
    python tools/loop_seam.py --fix --all        # 튀거나 거꾸로 가는 것 전부
    python tools/loop_seam.py --fix ink --mode pingpong --fade 18
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "apps" / "web" / "public"

# 이 위로 벌어지면 눈에 보입니다. 이어진 클립들이 1.1~1.9 였고
# 튀는 클립들이 12.9~34.8 이었습니다. 그 사이에 문턱을 둡니다.
SEAM_OK = 4.0

# 겹치는 프레임 수 (0.5초). 이보다 길면 포개진 그림이 눈에 띕니다.
FADE_DEFAULT = 12

# 카메라가 미는 장면 — 겹쳐 넘길 수 없어 되감습니다 (머리말 참고).
# docs/10 §3 의 preset 이 Dolly 인 것들입니다.
DOLLY = {"gate", "hall", "handle", "roadmap"}

# 클립 하나에 허용하는 크기 (docs/10 §7)
MAX_BYTES = 600 * 1024

# 무엇을 어떻게 구웠는지 적어 두는 자리.
#
# ★ 왜 적어 두나 — 이음새는 **눈으로만** 잽니다(ffmpeg + 픽셀). 그건
#   테스트가 매번 돌릴 수 있는 값이 아닙니다. 그래서 여기 찍어 두고,
#   `tests/test_loop_seam.py` 는 **디스크의 클립이 찍힌 그것인지**만
#   봅니다 — ffmpeg 없이 돕니다. 안 구운 클립을 새로 넣으면 걸립니다.
RECORD = ROOT / "seed" / "loop_seam.json"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if p.returncode != 0:
        raise RuntimeError(cmd[0] + " 실패:\n" + (p.stderr or "")[-2000:])
    return p.stdout


def probe(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-count_frames", "-show_entries",
               "stream=width,height,r_frame_rate,nb_read_frames",
               "-of", "json", str(path)])
    st = json.loads(out)["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {
        "w": int(st["width"]),
        "h": int(st["height"]),
        "fps": int(round(int(num) / int(den))),
        "n": int(st["nb_read_frames"]),
    }


def _frame(src: Path, idx: int, dst: Path, wide: int = 64) -> None:
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-vf", "select=eq(n\\,{}),scale={}:-1".format(idx, wide),
         "-frames:v", "1", "-fps_mode", "passthrough", str(dst)])


def _diff(a: Path, b: Path) -> float:
    """두 그림의 평균 채널차 (0~255). 사람 눈은 4 근처부터 알아봅니다."""
    from PIL import Image
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB").resize(ia.size)
    pa, pb = list(ia.getdata()), list(ib.getdata())
    tot = sum(abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2])
              for x, y in zip(pa, pb))
    return tot / (len(pa) * 3)


def measure(clip: Path, meta: dict, tmp: Path) -> dict:
    """이음새 · 되감기 여부.

    ★ 되감기 판정은 「f(k) 와 f(n-1-k) 가 같은가」만 봐서는 안 됩니다.
      거의 안 움직이는 클립은 **아무 두 프레임이나 같아서** 전부
      되감기로 잡힙니다(갈림길이 그랬습니다 — 6프레임 사이 움직임이
      0.44로 코덱 잡음보다 작습니다).

      그래서 **다른 위상**과 대 봅니다. 거울쌍이 다른 위상보다 뚜렷하게
      더 같아야 되감기입니다. 애초에 움직임이 잡음에 묻히는 클립은
      되감아도 티가 안 나므로 판정하지 않습니다.
    """
    n = meta["n"]
    a, b = tmp / "a.png", tmp / "b.png"
    _frame(clip, 0, a)
    _frame(clip, n - 1, b)
    seam = _diff(a, b)

    pingpong = False
    if n >= 16:
        c, d = tmp / "c.png", tmp / "d.png"
        hits = 0
        for k in (n // 8, n // 4, 3 * n // 8):
            _frame(clip, k, c)
            _frame(clip, n - 1 - k, d)
            mirrored = _diff(c, d)
            _frame(clip, (k + n // 5) % n, d)
            phase = _diff(c, d)           # 그냥 다른 위상은 얼마나 다른가
            if phase > 1.0 and mirrored < 0.5 * phase:
                hits += 1
        pingpong = hits == 3
    return {"seam": seam, "pingpong": pingpong}


def forward_frames(meta: dict, pingpong: bool) -> int:
    """앞으로 가는 부분만 몇 프레임인가."""
    return (meta["n"] + 1) // 2 if pingpong else meta["n"]


def graph_xfade(n: int, fade: int, fps: int) -> str:
    """겹쳐 넘기기 — 앞으로만 가는 고리. 나가는 길이 n-fade."""
    return (
        "[0:v]trim=start_frame={f}:end_frame={a},"
        "setpts=PTS-STARTPTS,fps={r},format=yuv420p[body];"
        "[0:v]trim=start_frame={a}:end_frame={n},"
        "setpts=PTS-STARTPTS,fps={r},format=yuv420p[tl];"
        "[0:v]trim=start_frame=0:end_frame={f},"
        "setpts=PTS-STARTPTS,fps={r},format=yuv420p[hd];"
        "[tl][hd]xfade=transition=fade:duration={d}:offset=0[mix];"
        "[body][mix]concat=n=2:v=1:a=0[v]"
    ).format(f=fade, a=n - fade, n=n, r=fps, d=fade / fps)


def graph_pingpong(n: int, fps: int) -> str:
    """되감기 — 카메라가 미는 장면 몫. 나가는 길이 2n-2.

    ★ **겹치는 프레임을 두지 않습니다.** 되도는 자리에 같은 프레임이 두 번
      나오면 24분의 1초씩 멈춥니다. 지금 들어와 있는 일곱이 그 상태입니다
      (`f0‥f120 + f120‥f0` = 242프레임). 여기서는 되돌 때 양 끝을 빼서
      `f0‥f(n-1) + f(n-2)‥f1` 로 갑니다 — 멈추는 프레임이 없습니다.
    """
    return (
        "[0:v]trim=start_frame=0:end_frame={n},"
        "setpts=PTS-STARTPTS,fps={r},format=yuv420p[fwd];"
        "[0:v]trim=start_frame=1:end_frame={m},"
        "setpts=PTS-STARTPTS,fps={r},format=yuv420p,reverse[rev];"
        "[fwd][rev]concat=n=2:v=1:a=0[v]"
    ).format(n=n, m=n - 1, r=fps)


# 크기가 넘치면 조금씩 눌러 다시 냅니다. 600KB 는 발주서 §7 의 값입니다.
CRF_H264 = (24, 27, 30, 33, 36)
CRF_VP9 = (32, 35, 38, 41, 44)


def _encode(src: Path, vf: str, dst: Path, kind: str) -> int:
    base = ["ffmpeg", "-v", "error", "-y", "-i", str(src),
            "-filter_complex", vf, "-map", "[v]", "-an"]
    for crf in (CRF_H264 if kind == "h264" else CRF_VP9):
        if kind == "h264":
            # 값을 치른 눈에 띄지 않을 만큼 두되 600KB 안에 둡니다.
            run(base + ["-c:v", "libx264", "-profile:v", "high",
                        "-pix_fmt", "yuv420p", "-crf", str(crf),
                        "-preset", "slow", "-movflags", "+faststart", str(dst)])
        else:
            # VP9 는 8비트로 냅니다. 10비트(Profile 2)는 사파리가 못 엽니다.
            run(base + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p",
                        "-crf", str(crf), "-b:v", "0", "-row-mt", "1",
                        "-cpu-used", "2", str(dst)])
        if dst.stat().st_size <= MAX_BYTES:
            break
    return dst.stat().st_size


def build(src: Path, clip: Path, meta: dict, n_fwd: int, fade: int,
          mode: str) -> None:
    """고리를 만들어 webm · mp4 · poster 를 새로 쓴다.

    ★ 이름을 넘겨받아 짓습니다. `clip.side.mp4` 처럼 갈래가 붙은 클립이
      있어(풍운도령 옆모습) `clip.mp4` 로 박아 두면 엉뚱한 파일을 만듭니다.

    ★ **있던 것만 다시 씁니다.** webm 만 들어와 있는 자리에 mp4 를
      만들어 놓으면 발주가 안 온 것이 온 것처럼 보입니다.
    """
    out_dir = clip.parent
    stem = clip.stem                          # "clip" · "clip.side" · "greet"
    tail = stem.split(".", 1)[1] if "." in stem else ""
    tail = ("." + tail) if tail else ""
    mp4 = Path(str(clip)[: -len(clip.suffix)] + ".mp4")
    webm = Path(str(clip)[: -len(clip.suffix)] + ".webm")
    # 인사 클립의 첫 프레임은 `greet.webp` — 누끼를 뜬 그림이라
    # 영상에서 다시 뽑으면 **바탕이 살아납니다.** 손대지 않습니다.
    poster = out_dir / ("poster" + tail + ".jpg")
    fps = meta["fps"]
    if mode == "pingpong":
        vf = graph_pingpong(n_fwd, fps)
    else:
        if n_fwd - 2 * fade < 1:
            raise RuntimeError(
                "겹침({})이 원본({}프레임)에 비해 큽니다".format(fade, n_fwd))
        vf = graph_xfade(n_fwd, fade, fps)

    tmp_mp4 = out_dir / (stem + ".new.mp4")
    tmp_webm = out_dir / (stem + ".new.webm")
    tmp_jpg = out_dir / ("poster.new" + tail + ".jpg")

    made = []
    if mp4.exists():
        _encode(src, vf, tmp_mp4, "h264")
        made.append((tmp_mp4, mp4))
    if webm.exists():
        _encode(src, vf, tmp_webm, "vp9")
        made.append((tmp_webm, webm))

    # poster 는 **나가는 영상의 첫 프레임**이어야 합니다. 원본 첫 프레임을
    # 그대로 두면 정지컷과 영상이 어긋납니다 (reduced-motion 손님).
    if poster.exists():
        run(["ffmpeg", "-v", "error", "-y", "-i", str(made[0][0]),
             "-frames:v", "1", "-q:v", "3", str(tmp_jpg)])
        made.append((tmp_jpg, poster))

    for tmp_f, final in made:
        shutil.move(str(tmp_f), str(final))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(rows) -> None:
    """지금 디스크에 있는 클립들을 그대로 찍어 둔다."""
    out = {}
    for name, clip, meta, m in rows:
        short = name.rsplit("/", 1)[-1].split(":")[0]
        files = {}
        for ext in (".mp4", ".webm"):
            f = clip.with_suffix(ext)
            if f.exists():
                files[ext[1:]] = {"bytes": f.stat().st_size, "sha256": sha(f)}
        out[name] = {
            "frames": meta["n"],
            "fps": meta["fps"],
            "seam": round(m["seam"], 2),
            "mode": "pingpong" if m["pingpong"] else "xfade",
            "dolly": short in DOLLY,
            "files": files,
        }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(
        json.dumps({"seam_ok": SEAM_OK, "clips": out},
                   ensure_ascii=False, indent=2, sort_keys=True) + chr(10),
        encoding="utf-8")


# 영원히 도는 것들. `greet` 도 `autoPlay loop` 입니다 (CharArt.tsx).
STEMS = ("clip", "greet")


def clips():
    """돌아가는 클립 전부.

    ★ mp4 만 찾으면 안 됩니다. webm 만 들어와 있는 자리가 생깁니다
      (`scene/cardbg`). 두 벌 다 보고 같은 클립은 한 번만 셉니다.

    ★ `clip` 만 찾아도 안 됩니다. 캐릭터 인사(`greet`)도 돕니다.
    """
    found = []
    for base in ("scene", "char"):
        root = PUBLIC / base
        if not root.exists():
            continue
        seen = set()
        files = []
        for st in STEMS:
            for ex in ("mp4", "webm"):
                files += sorted(root.glob("**/{}*.{}".format(st, ex)))
        for f in files:
            key = str(f)[: -len(f.suffix)]
            if key in seen:
                continue
            seen.add(key)
            name = str(f.relative_to(PUBLIC).parent).replace("\\", "/")
            if f.stem != "clip":
                name += ":" + f.stem.replace(".", "-")
            found.append((name, f))
    return sorted(found)


def has_audio(path: Path) -> bool:
    out = run(["ffprobe", "-v", "error", "-select_streams", "a",
               "-show_entries", "stream=index", "-of", "csv=p=0", str(path)])
    return bool(out.strip())

def verdict_of(name: str, m: dict):
    """무엇으로 보이는가 · 고쳐야 하는가."""
    short = name.rsplit("/", 1)[-1].split(":")[0]
    if m["seam"] > SEAM_OK:
        return "튄다", True
    # 미는 장면의 되감기는 **고른 답**입니다. 흠이 아닙니다.
    if m["pingpong"]:
        if short in DOLLY:
            return "되감기 (미는 장면 — 맞음)", False
        return "거꾸로 간다", True
    return "이어짐", False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", nargs="*", metavar="ID",
                    help="고칠 클립 (이름 일부). 비우고 --all 이면 어긋난 것 전부")
    ap.add_argument("--all", action="store_true", help="어긋난 것 전부 고치기")
    ap.add_argument("--fade", type=int, default=0, help="겹치는 프레임 수")
    ap.add_argument("--mode", choices=("xfade", "pingpong"), default=None,
                    help="고리 만드는 법. 안 적으면 장면마다 알아서 (미는 장면은 되감기)")
    ap.add_argument("--record", action="store_true",
                    help="지금 상태를 seed/loop_seam.json 에 찍는다 (테스트가 봅니다)")
    args = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg 가 없습니다.", file=sys.stderr)
        return 1
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow 가 필요합니다:  pip install pillow", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rows = []
        for name, clip in clips():
            meta = probe(clip)
            rows.append([name, clip, meta, measure(clip, meta, tmp)])

        print("{:<24}{:>7}{:>8}  {}".format("클립", "프레임", "이음새", "판정"))
        print("─" * 60)
        bad = []
        for name, clip, meta, m in rows:
            say, broke = verdict_of(name, m)
            if broke:
                bad.append(name)
            print("{:<24}{:>7}{:>8.1f}  {}".format(
                name, meta["n"], m["seam"], say))

        # ── 재기만 하는 경우
        if args.fix is None and not args.all:
            print()
            if args.record:
                record(rows)
                print("찍었습니다: seed/loop_seam.json")
                return 0
            if bad:
                print("고칠 것 {}개: {}".format(len(bad), " ".join(bad)))
                print("  python tools/loop_seam.py --fix --all")
            else:
                print("전부 앞으로만 돌고 이음새가 없습니다.")
                print("  기록이 낡았으면:  python tools/loop_seam.py --record")
            return 0

        # ── 고치는 경우
        want = args.fix or []
        targets = [r for r in rows
                   if (args.all and verdict_of(r[0], r[3])[1])
                   or any(w in r[0] for w in want)]
        if not targets:
            print("\n고칠 대상이 없습니다.")
            return 0

        print()
        over_any = False
        for name, clip, meta, m in targets:
            n_fwd = forward_frames(meta, m["pingpong"])
            short = name.rsplit("/", 1)[-1].split(":")[0]
            mode = args.mode or ("pingpong" if short in DOLLY else "xfade")
            fade = args.fade or FADE_DEFAULT
            # webm 이 비트레이트가 높아 원본으로 낫습니다. 없으면 mp4.
            src = clip.with_suffix(".webm")
            if not src.exists():
                src = clip.with_suffix(".mp4")
            if has_audio(src):
                # 되감으면 말이 거꾸로 나고, 겹치면 말이 겹칩니다.
                # 소리는 소리대로 손질해야 하므로 사람이 볼 자리입니다.
                print("  {}: 소리 트랙이 있어 손대지 않습니다 — 사람이 보세요"
                      .format(name))
                continue
            note = " (되감기 → 앞 {})".format(n_fwd) if m["pingpong"] else ""
            out_n = 2 * n_fwd - 2 if mode == "pingpong" else n_fwd - fade
            how = "되감기" if mode == "pingpong" else "겹침 {}f".format(fade)
            print("  {}: {}프레임{} · {} → {}프레임 ({:.1f}초)".format(
                name, meta["n"], note, how, out_n, out_n / meta["fps"]),
                flush=True)
            build(src, clip, meta, n_fwd, fade, mode)

            after = probe(clip)
            am = measure(clip, after, tmp)
            sizes = [(p.name, p.stat().st_size)
                     for p in (clip.with_suffix(".mp4"),
                               clip.with_suffix(".webm")) if p.exists()]
            over = [k for k, v in sizes if v > MAX_BYTES]
            over_any = over_any or bool(over)
            print("      이음새 {:.1f} → {:.1f} · {}{}".format(
                m["seam"], am["seam"],
                " · ".join("{} {}KB".format(k, v // 1024) for k, v in sizes),
                "   ★ 600KB 넘음: " + ", ".join(over) if over else ""))

        if over_any:
            print()
            print("★ 600KB 를 넘는 것이 있습니다 — 겹침을 줄이거나 크기를 낮추세요.")

        # ★ 고쳤으면 **전부** 다시 재서 찍습니다. 손댄 것만 찍으면 옆
        #   클립이 그새 바뀌었을 때 기록이 디스크와 어긋납니다.
        again = []
        for name, clip, _meta, _m in rows:
            meta2 = probe(clip)
            again.append([name, clip, meta2, measure(clip, meta2, tmp)])
        record(again)
        print()
        print("찍었습니다: seed/loop_seam.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
