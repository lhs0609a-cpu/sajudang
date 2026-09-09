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
    if hour_known or not text:
        return text
    return re.sub(r'(?<![가-힣])여덟 (글자|자|자리)', r'여섯 \1', text)
