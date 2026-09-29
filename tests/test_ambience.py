"""The user replaced all scene music with one continuous track on 2026-09-22.
Actual looping/navigation/mute checks run in tools/check-global-bgm.cjs.
"""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'apps'/'web'

def test_only_the_requested_original_bgm_is_published():
    directory=WEB/'public'/'audio'/'bgm'
    assert {p.name for p in directory.glob('*.mp3')}=={'moon-thread-loop.mp3'}
    # Verified against the original master; CI does not contain the ignored BGM folder.
    expected='2d1f1e436b9d2a33c81105b56d91c85c09863da5e46e1a2f45d5e2c7253a207b'
    assert hashlib.sha256((directory/'moon-thread-loop.mp3').read_bytes()).hexdigest()==expected

def test_sound_control_stays_available_on_entry_and_other_pages():
    """
    ★ 끌 데는 **소리가 나는 층에** 둡니다 (2026-09-23).

      전에는 껍데기(Shell)가 두 벌을 그렸습니다 — 상단바에 하나,
      띠를 숨기는 대문에 또 하나. 소리를 뿌리 층 한 벌로 돌리면서
      (`BackgroundMusic`) 끌 단추도 그리로 옮겼습니다. 소리를 내는
      자리가 끌 자리를 들고 있으니 어느 화면에서도 빠지지 않습니다 —
      띠를 숨기는 대문에서도요. 자는 **몇 벌인가**가 아니라
      **어디서나 닿는가**를 봅니다.
    """
    music=(WEB/'components'/'BackgroundMusic.tsx').read_text('utf-8')
    assert '<SoundToggle />' in music, '소리를 내는 층에 끌 데가 없소'
    layout=(WEB/'app'/'layout.tsx').read_text('utf-8')
    assert '<BackgroundMusic />' in layout, '뿌리 층에 안 걸려 있소'
    # 단추는 **두 쪽 다** 말해야 합니다 — 켜져 있으면 끌 데를, 꺼져
    # 있으면 켤 데를. 낱말은 바뀔 수 있으니 뜻으로 잽니다.
    toggle=(WEB/'components'/'SoundToggle.tsx').read_text('utf-8')
    assert 'aria-pressed={on}' in toggle, '켜졌는지 안 알려 주오'
    assert '끄기' in toggle and '켜기' in toggle, '끌 말·켤 말이 둘 다 있어야 하오'
