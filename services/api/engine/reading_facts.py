"""Explicit display scope for visible characters versus hidden-stem weights."""
import re
from .constants import ELEMENT_OF_GAN, ELEMENT_OF_JI

def visible_elements(f):
    counts = dict.fromkeys(('목','화','토','금','수'), 0)
    for pillar in f.pillars:
        counts[ELEMENT_OF_GAN[pillar['gan']]] += 1
        counts[ELEMENT_OF_JI[pillar['ji']]] += 1
    return counts

def scope_text(text, hour_known):
    """
    시각 미상이면 글에 적힌 **범위를 같이 줄입니다.**

    ★ 「여덟 글자」 만 갈고 「네 기둥」 을 두고 갔습니다 (2026-09-28)

      그래서 시각 미상 손님 12/12 장에 이런 줄이 나갔습니다 —

          「여섯 글자 **네 기둥** 가운데 길신이 앉은 것은 1자리요」

      여섯 글자면 세 기둥이오. 이 집이 금해 둔 「기둥 수를 글에 박기」 가
      한 자리 더 남아 있었습니다. 범위를 줄이는 자리는 여기 한 곳이니
      **여기서 다 갈아야** 합니다 — 부르는 쪽마다 따로 갈면 또 어긋납니다.
    """
    if hour_known or not text:
        return text
    text = re.sub(r'(?<![가-힣])여덟 (글자|자|자리)', r'여섯 \1', text)
    text = re.sub(r'(?<![가-힣])네 기둥', '세 기둥', text)
    return text
