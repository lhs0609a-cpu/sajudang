# -*- coding: utf-8 -*-
"""
컷 제목 — **범주가 아니라 주장.**

★ 왜 이 파일이 생겼나 (2026-09-27 · docs/45 §9 ⑦)

  잠긴 컷 일곱의 제목이 번호 + 범주였습니다 —

      1 · 없는 것부터 · 2 · 왜 반복되나 · 3 · 어느 자리에서 ·
      4 · 지금 어디에 · 5 · 필요한 것 · 6 · 대운 맵 · 7 · 물은 자리와 센 자리

  이 일곱은 **값을 부르는 표면**이오. 손님이 값을 치를지 말지 정할 때
  읽는 것이 제목과 맛보기 한 줄뿐인데, 제목이 목차였습니다.

  16personalities 는 사이드바 아홉 항목의 머리말이 전부 **주장**이오 —
  「비판을 개인적으로 받아들입니다」 처럼. 범주(「대인관계」)가 아니오.
  그 집의 아홉째 항목이 페이월이고, 그 앞 여덟이 주장이라 아홉째를
  누릅니다.

★ 어미를 달지 않습니다 — **이름씨꼴**이오.

  제목은 말이 아니라 **표지판**이라 `voice` 층을 안 탑니다
  (`report` 가 `html` 과 `source` 만 갈아 끼웁니다). 그래서 「…굳소」
  라 적으면 스무 명 전부가 하오체로 그 한 줄을 말하게 되오 — 반말
  캐릭터에게서도요. 이 집이 「이게 무슨 말이네요」 로 한 번 겪은
  자리입니다.

  그래서 꼴은 **「…하는 자리」** 요. 주장이면서 어미가 없습니다.
  docs/45 가 든 보기가 바로 그 꼴이오 — 「값을 부를 때 손이 굳는 자리」.

★ 세는 값을 답니다.

  「없는 것부터」 는 틀릴 수가 없소. 「물이 하나뿐 — 쌓고 채우는 힘이
  얇은 자리」 는 손님이 만세력을 펴고 셀 수 있소. 제목에서 이미
  대 볼 수 있으면 그 아래 글도 대 볼 수 있다고 믿습니다.

★ 지어내지 않습니다.

  표에 칸이 없으면 **옛 제목을 그대로** 냅니다 (`title` 의 `fallback`).
  칸을 지어내는 것보다 목차가 낫소.
"""
from __future__ import annotations

from typing import Optional

from .constants import TEN_GOD_GROUP

EL_WORD = {'목': '나무', '화': '불', '토': '흙', '금': '쇠', '수': '물'}

#: 글자를 세는 말. 「하나 자리」 는 「자리」 가 두 번 나와 제목이 겹칩니다.
_N = ('', '한', '두', '세', '네', '다섯', '여섯', '일곱', '여덟')


def _count_word(n: int) -> str:
    return _N[n] if 0 < n < len(_N) else str(n)


# ══════════════════════════════════════════════════════════
# 1 · 없는 것 — 얇은 오행이 **무슨 힘**인가
# ══════════════════════════════════════════════════════════
LACK = {
    '목': '처음 펼 힘이 얇은 자리',
    '화': '남 앞에 나서는 힘이 얇은 자리',
    '토': '버티는 바닥이 얇은 자리',
    '금': '끊고 자르는 힘이 얇은 자리',
    '수': '쌓고 채우는 힘이 얇은 자리',
}

# ══════════════════════════════════════════════════════════
# 2 · 왜 반복되나 — 가장 센 십신이 **어디서 되풀이를 만드나**
# ══════════════════════════════════════════════════════════
WHY = {
    '비견': '혼자 지고 가다 같은 데서 막히는 자리',
    '겁재': '같이 하다 제 몫이 줄어드는 자리',
    '식신': '만드는 데 빠져 값을 못 부르는 자리',
    '상관': '옳은 말을 하고도 지는 자리',
    '정재': '아끼다 때를 놓치는 자리',
    '편재': '벌이는 판은 크고 남는 것은 적은 자리',
    '정관': '금을 지키다 제 몫을 못 챙기는 자리',
    '편관': '먼저 떠맡고 나중에 앓는 자리',
    '정인': '다 알아보고 첫 발이 늦는 자리',
    '편인': '남이 안 보는 각도를 설명 반만 하는 자리',
}

# ══════════════════════════════════════════════════════════
# 3 · 어느 자리에서 — 발밑이 부딪히는가 · 힘이 어디로 기우나
# ══════════════════════════════════════════════════════════
PLACE = {
    (True, '관'): '가까운 데서 부딪히고 밖에서 참는 자리',
    (True, '재'): '가까운 데서 부딪히고 씀씀이로 푸는 자리',
    (True, '식'): '가까운 데서 부딪히고 일로 덮는 자리',
    (True, ''): '가장 가까운 자리에서 먼저 흔들리는 자리',
    (False, '관'): '남이 그은 금 안에서만 편한 자리',
    (False, '재'): '쓰면서 마음이 풀리는 자리',
    (False, '식'): '손을 놀리지 못하는 자리',
    (False, ''): '어느 쪽으로도 크게 기울지 않은 자리',
}

# ══════════════════════════════════════════════════════════
# 4 · 지금 어디에 — 지금 대운의 십신이 **무엇을 켜는가**
# ══════════════════════════════════════════════════════════
DAEUN_NOW = {
    '비견': '같이 서는 사람이 늘어나는 십 년',
    '겁재': '나눌 사람이 늘고 몫이 갈리는 십 년',
    '식신': '손에서 나온 것이 쌓이는 십 년',
    '상관': '하던 말을 참기 어려워지는 십 년',
    '정재': '들어온 것을 지키는 일이 커지는 십 년',
    '편재': '판이 커지고 손이 바빠지는 십 년',
    '정관': '자리와 이름이 걸리는 십 년',
    '편관': '떠맡을 일이 먼저 찾아오는 십 년',
    '정인': '배우고 받쳐 주는 쪽으로 도는 십 년',
    '편인': '혼자 파는 일이 깊어지는 십 년',
}

# ══════════════════════════════════════════════════════════
# 5 · 필요한 것 — 용신이 **어떤 일을 하는가**
# ══════════════════════════════════════════════════════════
YONGSIN = {
    '목': '새로 펴는 일에서 풀리는 자리',
    '화': '드러내는 일에서 풀리는 자리',
    '토': '자리를 정하는 일에서 풀리는 자리',
    '금': '끊는 일에서 풀리는 자리',
    '수': '쉬며 채우는 일에서 풀리는 자리',
}


def lack(f) -> Optional[str]:
    weak = f.weak_el
    say = LACK.get(weak)
    if not say:
        return None
    # ★ 셈은 **리포트와 같은 자리**에서 받습니다. 제 손으로 세다가
    #   여섯 사람 전부 「겉에 안 보임」 이 나왔습니다 — `f.pillars` 에
    #   `gan_el` 같은 칸이 없어 늘 0이 된 것이오. 두 벌로 세면 그
    #   사고가 조용히 납니다.
    from .report import _visible
    vis = _visible(f, weak)
    # ★ 「없다」 와 「가장 얇다」 를 가릅니다 — 한 자 있어도 뽑히는 값이오.
    n = ('겉에 안 보임' if not vis else
         '겉에 %s 자' % _count_word(vis) if vis <= 4 else '겉에 %d자' % vis)
    return '%s %s — %s' % (EL_WORD.get(weak, weak), n, say)


def why(f) -> Optional[str]:
    top = f.top_ten_god
    say = WHY.get(top)
    if not say:
        return None
    return '%s %s자 — %s' % (top, int(f.ten_gods.get(top, 0)), say)


def place(f) -> Optional[str]:
    lean = ('관' if f.gwan >= 2 else '재' if f.jae >= 2
            else '식' if f.sik >= 2 else '')
    say = PLACE.get((bool(f.ilji_chung), lean))
    if not say:
        return None
    return '일지 %s — %s' % (f.day_ji, say)


def daeun_now(f) -> Optional[str]:
    say = DAEUN_NOW.get(f.daeun_ten_god)
    if not say:
        return None
    if not f.daeun_started:
        return '아직 들지 않은 십 년 — %s' % say
    try:
        age = int(f.daeun[f.daeun_now]['start_age'])
    except Exception:
        return say
    return '%d살부터 — %s' % (age, say)


def yongsin(f) -> Optional[str]:
    say = YONGSIN.get(f.yongsin)
    if not say:
        return None
    return '%s — %s' % (EL_WORD.get(f.yongsin, f.yongsin), say)


def daeun_map(f) -> Optional[str]:
    """표는 표라 주장이 없소. 대신 **손님이 대 볼 수 있는 수**를 답니다."""
    try:
        first = int(f.daeun[0]['start_age'])
    except Exception:
        return None
    return '%d살부터 열 해씩 — 어느 칸이 그대 칸인가' % first


#: 물은 자리 이름. `topic` 이 정한 것을 그대로 받습니다.
CONCERN_WORD = {'money': '돈', 'work': '일', 'love': '사랑', 'people': '사람',
                'dir': '갈 곳', 'health': '몸', 'real_estate': '부동산'}


def concern(f, concern_id: str) -> Optional[str]:
    """
    ★ 조사를 손으로 박지 마시오. 처음에 「받침이 돈·일·몸이면 을」 이라
      적었는데 **사람 · 부동산 · 갈 곳**이 다 받침이오 — 「사람를」 이
      나갈 자리였습니다. 이 집에 `josa` 가 있습니다.
    """
    word = CONCERN_WORD.get(concern_id or '')
    got = TEN_GOD_GROUP.get(f.top_ten_god or '')
    if not word or not got:
        return None
    from .bank import josa
    return '%s 물었을 때 먼저 켜지는 자리 — %s' % (josa(word, '을', '를'), got)


# ══════════════════════════════════════════════════════════
# 남은 넷 — 희소도 · 신살 · 길신 · 조상
# ══════════════════════════════════════════════════════════
#
# ★ 이 넷도 잠긴 컷이오 — **값을 부르는 표면**입니다.
#   「몇이나 되는가」 「이름 붙은 자리」 는 물음과 범주지 주장이 아니오.

#: 희소도 띠 → 그 띠가 무슨 말인가. 골라 담지 않습니다 — 흔하면 흔하다고.
#: ★ 열쇠는 `engine/rarity` 가 내는 **그 띠 이름**이오 (`seed/rarity_text`).
#:   처음에 영어로 적었더니 한 칸도 안 걸려 옛 제목이 그대로 나갔습니다 —
#:   물러서는 자리를 둔 덕에 안 터졌을 뿐이오.
RARITY = {
    '표본에없음': '표본에 같은 배치가 없는 자리',
    '아주드묾': '같은 배치가 아주 드문 자리',
    '드묾': '같은 배치가 드문 자리',
    '적잖음': '같은 데서 막히는 사람이 더러 있는 자리',
    # ★ 줄표를 두 번 쓰지 마시오 — 셈 앞에 이미 하나 섭니다.
    '흔함': '흔해서 혼자가 아닌 자리',
}


def rarity(f, band: str = '', per10k=None) -> str:
    """
    ★ 골라 담지 않습니다 — 띠를 그대로 말하고 **셈을 앞에** 댑니다.
      드문 쪽만 말하면 화면에 남는 숫자가 전부 드물어 보이오.
    ★ 띠를 모르면 수만, 수를 모르면 띠만. 지어내지 않소.
      `per10k` 는 표본에 없는 배치면 비어 있습니다 — 0 과 다릅니다.
    """
    say = RARITY.get(band or '')
    try:
        n10k = int(per10k)
    except (TypeError, ValueError):
        n10k = -1
    if n10k >= 1:
        n = ('만 명에 %d명' % n10k if n10k < 100
             else '천 명에 %d명' % round(n10k / 10))
        return '%s — %s' % (n, say) if say else '인구에서 %s' % n
    return say or ''


def sinsal(f) -> str:
    n = len(getattr(f, 'sinsal', ()) or ())
    if not n:
        return '이름 붙은 자리가 하나도 없는 명식'
    return '이름 붙은 자리 %d개 — 어느 글자에 무엇이 앉았나' % n


def helper(f) -> str:
    seats = len({h['pillar'] for h in (getattr(f, 'helpers', ()) or ())})
    if not seats:
        return '길신이 앉은 자리가 없음 — 그러면 무엇으로 버티나'
    return '길신이 앉은 자리 %d곳 — 누가 받쳐 주나' % seats


def ancestor(f) -> str:
    a = getattr(f, 'ancestor', None) or {}
    gz, tg = a.get('pillar'), a.get('gan_ten_god')
    if not gz or not tg:
        return ''
    return '년주 %s · %s — 물려받아 쓰고 있는 것' % (gz, tg)


#: 컷 이름 → 제목을 짓는 함수. `report` 는 여기만 봅니다.
OF = {'lack': lack, 'why': why, 'place': place, 'daeun_now': daeun_now,
      'yongsin': yongsin, 'daeun_map': daeun_map, 'sinsal': sinsal,
      'helper': helper, 'ancestor': ancestor}


def title(cut_id: str, f, fallback: str, concern_id: str = '') -> str:
    """
    주장 제목. 표에 칸이 없으면 **옛 제목을 그대로** 냅니다.

    ★ 칸을 지어내는 것보다 목차가 낫소 — 계산이 없으면 「모른다」고
      적는 것과 같은 규칙이오.
    """
    try:
        if cut_id == 'concern':
            got = concern(f, concern_id)
        else:
            fn = OF.get(cut_id)
            got = fn(f) if fn else None
    except Exception:
        got = None
    return got or fallback
