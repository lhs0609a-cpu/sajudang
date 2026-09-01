# -*- coding: utf-8 -*-
"""
잇달아 나오는 두 화면이 같은 그림을 쓰지 않는가.

★ 왜 지키나

  a3 「날을 대다」와 a4b 「성향 4글자」가 둘 다 「먹이 번지는 종이」였다.
  a4b 는 발주서가 쓰인 뒤에 붙은 화면이라 제 장면이 없었고, 앞 화면
  것을 그대로 갖다 쓴 것이다.

  잇달아 나오는데 그림이 같으면 손님은 **화면이 안 넘어간 줄 안다.**
  글을 읽다 말고 뒤로 가거나, 눌러도 안 되는 줄 알고 나간다.

  나눠 써도 되는 자리는 있다(바탕 질감·같은 뜻의 자리). 그건 도구의
  SHARED_OK 에 **까닭과 함께** 적어 두고 쓴다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import asset_audit as aa  # noqa: E402


def test_no_two_screens_share_a_scene():
    bad = aa.shared(aa.read_usage())
    assert not bad, "두 화면이 같은 장면을 쓴다: %s" % bad


def test_every_entry_screen_has_its_own_scene():
    """진입 흐름은 한 화면 한 장면이라야 한다."""
    src = (ROOT / "apps" / "web" / "app" / "page.tsx").read_text(encoding="utf-8")
    import re
    ids = re.findall(r'<Scene id="(\w+)"', src)
    dup = [i for i in set(ids) if ids.count(i) > 1]
    assert not dup, "진입 흐름에서 겹치는 장면: %s" % dup
