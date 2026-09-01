"""출력 금지어 필터 — 모든 응답이 반드시 통과해야 함"""
import json, re, logging
from pathlib import Path

_G = json.loads((Path(__file__).parents[3]/"seed"/"guard.json").read_text("utf-8"))
_PATS = [re.compile(p) for p in _G["regex"]]
log = logging.getLogger("guard")

def check(text:str)->tuple[bool,list[str]]:
    hits=[p.pattern for p in _PATS if p.search(text)]
    return (not hits), hits

def sanitize(text:str)->str:
    for a,b in _G["replacements"].items():
        text = text.replace(a,b)
    return text

def enforce(text:str, ctx:dict|None=None)->str:
    ok, hits = check(text)
    if ok: return text
    log.warning("guard violation %s ctx=%s", hits, ctx)
    fixed = sanitize(text)
    ok2,_ = check(fixed)
    if ok2: return fixed
    return "이 부분은 말씀드릴 수 없소. 다른 자리를 보시겠소?"
