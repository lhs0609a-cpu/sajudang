"""
목소리 — 글을 소리로 바꿔 곳간에 둔다.

★ 왜 「그때그때 만들고 곳간에 두는」 방식인가

  "훅 5단과 캐릭터 첫마디만" 은 스물다섯 마디처럼 들린다. 세어 보면
  아니다 (`tools/voice_sheet.py`).

      고정  캐릭터 첫마디 20 · 화면에 박힌 도령의 말 12   = 32 마디
      조합  훅 5단                                       = 3,539 마디
            (표본 400명 × 고민 6가지에서 나온 서로 다른 말)

  훅은 사람의 여덟 글자에서 **조합**된다. 미리 다 만들어 둘 수 없고,
  사람이 늘면 새 조합이 계속 나온다. 그렇다고 방문할 때마다 새로
  만들면 값이 **트래픽에 묶인다.**

  그래서 글의 해시로 곳간을 둔다. 같은 말은 두 번 안 만든다. 그러면
  값이 트래픽이 아니라 **서로 다른 말의 수**에 묶인다 — 손님이 만
  명이 와도 만들어야 할 말은 늘지 않는다.

★ 열쇠가 없으면 소리는 없다

  결제와 같은 규칙이다. 열쇠가 없으면 조용히 없는 것으로 한다.
  소리 때문에 화면이 멈추면 안 된다.

★ 무엇을 안 읽는가

  리포트 본문(관점 컷 2,000여 개)은 읽지 않는다. 값과 용량도 문제지만
  무엇보다 **읽는 속도를 손님이 정해야 하는 글**이다. 소리로 읽어 주면
  손님이 그 속도에 묶인다.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Optional

import httpx

# 곳간. Fly 에서는 /data 가 볼륨입니다 (store.sqlite 와 같은 자리).
CACHE = Path(os.getenv("VOICE_DIR") or
             ("/data/voice" if Path("/data").is_dir() else "./.voice"))

API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
# 도령의 목소리. 바꾸면 **이미 만든 것과 목소리가 갈립니다** —
# 바꿀 때는 곳간을 비워야 합니다.
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/%s"

# 한 마디의 한계. 이보다 길면 읽지 않습니다 — 리포트 본문이 흘러드는
# 것을 막는 자리이기도 합니다.
MAX_CHARS = 220

# 이번 판에서 만든 수 — 폭주를 막습니다 (열쇠가 새면 값이 나갑니다)
_made = 0
MAX_PER_BOOT = int(os.getenv("VOICE_MAX_PER_BOOT", "2000"))


def enabled() -> bool:
    return bool(API_KEY and VOICE_ID)


def _bare(html: str) -> str:
    """
    소리로 읽을 말만 남긴다.

    ★ 풀이 괄호를 지운다. 「상관(나를 표현하는 힘)」 을 그대로 읽으면
      말이 끊기고 괄호까지 소리로 나온다. 눈으로 읽을 때는 도움이지만
      귀로 들을 때는 방해다.
    """
    s = re.sub(r'<i class="gl">\([^)]*\)</i>', "", html)
    s = re.sub(r"<[^>]*>", " ", s)
    s = s.replace("&nbsp;", " ").replace(" ", " ")
    return " ".join(s.split()).strip()


def key_of(text: str) -> str:
    """
    글 + 목소리로 이름을 짓는다.

    목소리를 바꾸면 이름도 바뀌어야 한다 — 안 그러면 곳간의 옛 소리가
    새 목소리인 척 나온다.
    """
    raw = "%s|%s|%s" % (VOICE_ID, MODEL, text)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def path_of(k: str) -> Path:
    return CACHE / (k + ".mp3")


def cached(text: str) -> Optional[str]:
    """이미 만들어 둔 것이 있으면 그 이름."""
    k = key_of(text)
    return k if path_of(k).exists() else None


async def synth(html_or_text: str) -> Optional[str]:
    """
    한 마디를 소리로. 이미 있으면 만들지 않는다.

    돌려주는 것은 곳간의 이름이다. 못 만들면 None — 화면은 소리 없이
    그대로 돕니다.
    """
    global _made
    text = _bare(html_or_text)
    if not text or len(text) > MAX_CHARS:
        return None

    k = key_of(text)
    if path_of(k).exists():
        return k
    if not enabled():
        return None
    if _made >= MAX_PER_BOOT:
        # 열쇠가 새거나 뭔가 잘못 돌 때 값이 끝없이 나가는 것을 막습니다.
        return None

    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        async with httpx.AsyncClient(timeout=20.0) as cx:
            r = await cx.post(
                ENDPOINT % VOICE_ID,
                headers={"xi-api-key": API_KEY,
                         "accept": "audio/mpeg",
                         "content-type": "application/json"},
                json={
                    "text": text,
                    "model_id": MODEL,
                    "voice_settings": {
                        # 도령은 흔들리지 않는 사람입니다. 안정을 높이고
                        # 꾸밈을 낮춥니다 — 광고 성우 톤이 되면 안 됩니다.
                        "stability": 0.55,
                        "similarity_boost": 0.8,
                        "style": 0.15,
                        "use_speaker_boost": True,
                    },
                },
            )
        if r.status_code != 200 or not r.content:
            return None
        # 먼저 임시 이름으로 적고 옮깁니다 — 반쯤 적힌 파일을 다음
        # 요청이 「있다」고 읽으면 깨진 소리가 나갑니다.
        tmp = path_of(k).with_suffix(".part")
        tmp.write_bytes(r.content)
        tmp.replace(path_of(k))
        _made += 1
        return k
    except Exception:
        # 소리는 곁가지입니다. 실패가 글을 막아서는 안 됩니다.
        return None
