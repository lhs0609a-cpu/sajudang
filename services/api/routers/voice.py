"""
POST /v1/voice — 한 마디를 소리로.
GET  /v1/voice/{key}.mp3 — 만들어 둔 소리를 내려보낸다.

★ 왜 글을 그대로 안 받나

  화면이 아무 글이나 보내 소리로 바꿀 수 있으면, 그건 남의 열쇠로
  **아무 말이나 읽게 하는 문**입니다. 값이 나가는 자리이므로 잠급니다.

      · 우리 문장 뱅크에서 나온 말만 받습니다 (statement_id 로 확인)
      · 캐릭터 첫마디와 화면에 박힌 말은 이름으로 부릅니다
      · 자유 입력은 안 받습니다

★ 자격은 안 봅니다

  훅은 값을 치르기 전 구간이라 누구나 듣습니다. 대신 **읽는 것은
  훅과 첫마디까지**입니다. 리포트 본문은 소리로 안 나갑니다
  (`voice.MAX_CHARS` 와 아래 목록이 그 자리를 지킵니다).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import voice

router = APIRouter(prefix="/v1", tags=["voice"])

ROOT = Path(__file__).resolve().parents[3]

# 캐릭터 첫마디 — id 로 부릅니다
_LENSES: dict[str, str] = {}
try:
    for l in json.loads((ROOT / "seed" / "lenses.json").read_text(encoding="utf-8")):
        if isinstance(l, dict) and isinstance(l.get("opening_quote"), str):
            _LENSES[l["id"]] = l["opening_quote"]
except Exception:                                   # noqa: BLE001
    pass


class VoiceAsk(BaseModel):
    """무엇을 읽어 달라는가. 글이 아니라 **어디 것인지**를 받습니다."""
    kind: str = Field(pattern="^(hook|lens)$")
    # hook — 훅 한 단. 화면이 받은 그 문장을 그대로 보냅니다.
    #        (뱅크에서 나온 것이라 statement_id 가 함께 옵니다)
    statement_id: str | None = None
    html: str | None = None
    # lens — 캐릭터 첫마디
    lens_id: str | None = None


class VoiceSaid(BaseModel):
    key: str | None = None
    url: str | None = None
    ready: bool = False


@router.post("/voice", response_model=VoiceSaid)
async def make_voice(ask: VoiceAsk) -> VoiceSaid:
    # ★ 먼저 무엇을 읽을지 확인합니다. 열쇠가 없다고 곧장 돌아서면
    #   잘못된 이름도 조용히 통과해, 열쇠를 넣는 날에야 드러납니다.
    if ask.kind == "lens":
        text = _LENSES.get(ask.lens_id or "")
        if not text:
            raise HTTPException(404, "그런 사람은 없소.")
    else:
        if not ask.statement_id or not ask.html:
            raise HTTPException(422, "무엇을 읽을지 덜 왔소.")
        text = ask.html

    if not voice.enabled():
        # 열쇠가 없으면 소리는 없습니다. 오류가 아니라 **없음**입니다 —
        # 화면이 이걸 보고 조용히 넘어갑니다.
        return VoiceSaid()

    k = await voice.synth(text)
    if not k:
        return VoiceSaid()
    return VoiceSaid(key=k, url="/v1/voice/%s.mp3" % k, ready=True)


@router.get("/voice/{key}.mp3")
def get_voice(key: str) -> FileResponse:
    # 이름은 우리가 지은 해시입니다. 길이와 글자를 확인해 경로를 벗어나는
    # 이름을 막습니다.
    if len(key) != 16 or not all(c in "0123456789abcdef" for c in key):
        raise HTTPException(404, "그런 소리는 없소.")
    p = voice.path_of(key)
    if not p.exists():
        raise HTTPException(404, "그런 소리는 없소.")
    return FileResponse(p, media_type="audio/mpeg",
                        headers={"Cache-Control": "public, max-age=31536000, immutable"})
