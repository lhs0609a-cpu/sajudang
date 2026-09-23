import json
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


@pytest.mark.parametrize('character', [row['id'] for row in lens.released()])
@pytest.mark.parametrize('incoming', ['money','work','love','people','dir','health'])
def test_specialist_topics_and_supporting_dialogue_are_consistent(chart,character,incoming):
    result=build_report(chart,'contract-test',character,'free',incoming)
    profile=lens.view(character)
    assert result['concern'] in profile['concerns']
    assert result['concern']==lens.concern_for(character,incoming)
    you=lens.you_of(character,'','F')
    strings=[result['opening'],result['closing'],result['practice']['action'],*result['practice']['steps']]
    for text in strings:
        assert text==voice.speak(text,profile['voice'])
        if you!='그대': assert '그대가' not in text and '그대의' not in text
    if character=='jeokhyeol':
        assert result['concern']=='love'
        assert '지출' not in result['practice']['action']


def test_stale_money_topic_is_discarded_for_relationship_specialist(chart):
    result=build_report(chart,'contract-test','jeokhyeol','one','money',extras={'topic':{'choice':'business'}})
    assert result['concern']=='love'
