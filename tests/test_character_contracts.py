import json
import re
from datetime import date
from pathlib import Path
import pytest
from engine import lens, voice
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report


def test_public_contract_matches_canonical_character_seed():
    root=Path(__file__).resolve().parents[1]
    public=json.loads((root/'apps/web/lib/character-profiles.json').read_text(encoding='utf-8'))
    assert len(public)==20
    for key,p in public.items():
        assert all(lens.view(key)[field]==value for field,value in p.items())


@pytest.fixture(scope='module')
def chart():
    return build_features(build_chart(1993,11,25,None,None,'F',False,'서울'),as_of=date(2026,9,22))


def _concerns():
    import typing
    from schemas.api import Concern
    return list(typing.get_args(Concern))


@pytest.mark.parametrize('character', [row['id'] for row in lens.released()])
@pytest.mark.parametrize('incoming', _concerns())
def test_specialist_topics_and_supporting_dialogue_are_consistent(chart,character,incoming):
    """
    ★ 계약이 바뀌었습니다 (2026-09-24).

      전에는 **캐릭터가 손님의 고민을 갈아치우는 것**이 계약이었습니다.
      그런데 그러면 본문이 「자네가 물으러 오신 고민은 갈 곳이네」 라고
      다른 고민 이름을 대고(손님은 돈을 골랐소), 고민만 바꿔 다시 물어도
      명식 85%에서 리포트가 글자 그대로 같았습니다.

      지금 계약은 **물으신 자리에 답하고, 내 자리가 아니면 그렇다고
      말하는 것**입니다 — `LENS_OFF` 가 그 줄이고 스무 명 몫이 이미
      적혀 있었습니다. 갈아치우는 동안 그 줄은 한 번도 안 나갔습니다.
    """
    result=build_report(chart,'contract-test',character,'free',incoming)
    profile=lens.view(character)
    assert result['concern']==incoming, '물으신 고민을 그대로 답해야 하오'
    assert result['concern']==lens.concern_for(character,incoming)
    allowed=profile.get('concerns') or []
    if allowed and incoming not in allowed and incoming!='real_estate':
        # ★ 태그를 걷고 봅니다 — 「내가 <b>맡은 일</b>이 아닙니다」 처럼
        #   굵게가 낱말 사이에 끼면 원문 그대로는 안 잡힙니다.
        body=re.sub(r'<[^>]+>','',''.join(c.get('html','') for c in result['cuts']))
        # ★ 어미 **앞까지**만 봅니다. 한글은 음절이 통째로 바뀌어서
        #   「아니오 → 아닙니다」 가 되면 「아니」 도 안 남습니다 —
        #   어간으로 찾는다고 「아니」 를 찾으면 합쇼체에서 헛짚습니다.
        assert ('맡은 일이' in body or '제 자리가' in body
                or '깊이는 못' in body),             '안 보는 자리를 물었는데 아니라고 말하지 않았소'
    you=lens.you_of(character,'','F')
    strings=[result['opening'],result['closing'],result['practice']['action'],*result['practice']['steps']]
    for text in strings:
        assert text==voice.speak(text,profile['voice'])
        if you!='그대': assert '그대가' not in text and '그대의' not in text


def test_relationship_specialist_answers_the_asked_concern(chart):
    """돈을 물으면 돈으로 답하고, 그것이 제 자리가 아니라고 말한다."""
    result=build_report(chart,'contract-test','jeokhyeol','one','money',extras={'topic':{'choice':'business'}})
    assert result['concern']=='money'
    body=re.sub(r'<[^>]+>','',''.join(c.get('html','') for c in result['cuts']))
    assert '맡은 일이' in body or '제 자리가' in body


def test_화면도_고민을_갈아치우지_않는다():
    """
    ★ 서버만 고치면 반쪽입니다 (2026-09-24).

      화면의 `characterConcern` 이 곳간(store)에서 고민을 바꿔 저장하고
      있었습니다 — 손님이 「돈」 을 눌러도 기억에 남는 것은 「사랑」 이었소.
      부르는 자리가 넷이라(store · lobby · InlinePaidReading · 진입 화면)
      함수는 남겨 두고, **그 함수가 아무것도 바꾸지 않는지**를 셉니다.
    """
    src = (Path(__file__).resolve().parents[1]
           / 'apps/web/lib/character-topic.ts').read_text(encoding='utf-8')
    # 이름이 겹치는 함수가 둘이오 (characterConcerns / characterConcern).
    body = src.split('export function characterConcern(')[1].split('}')[0]
    assert 'default_concern' not in body, '화면이 아직 고민을 갈아치우오'
    assert 'return concern;' in body, '화면이 고른 고민을 그대로 안 돌려주오'

