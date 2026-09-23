"""The user replaced all scene music with one continuous track on 2026-09-22.
Actual looping/navigation/mute checks run in tools/check-global-bgm.cjs.
"""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'apps'/'web'

def test_only_the_requested_original_bgm_is_published():
    source=ROOT/'BGM'/'moon-thread-loop.mp3'
    directory=WEB/'public'/'audio'/'bgm'
    assert {p.name for p in directory.glob('*.mp3')}=={'moon-thread-loop.mp3'}
    assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256((directory/source.name).read_bytes()).digest()

def test_sound_control_stays_available_on_entry_and_other_pages():
    shell=(WEB/'components'/'Shell.tsx').read_text('utf-8')
    assert shell.count('<SoundToggle />')>=2
    toggle=(WEB/'components'/'SoundToggle.tsx').read_text('utf-8')
    assert 'on ? "소리 끄기" : "소리 켜기"' in toggle