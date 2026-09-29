from dataclasses import replace
from datetime import date
import re

import pytest
from engine.calendar import build_chart
from engine.features import build_features
from engine.personal_reading import build_depth, build_scene, basis, INTERVIEWS, leaders
from engine.plain_reading import text, html
from engine.peek import _reading_sample
from engine.report import build_report
from engine.topic import ask_spec
from engine.character_consultation import enrich_spec


@pytest.fixture(scope='module')
def f():
    return build_features(build_chart(1993,11,25,None,None,'F',False),as_of=date(2026,9,29))


def test_negation_and_ordinary_inventory_keep_their_meanings():
    for value in ['비교에서 지지 않으려고 애쓰오.', '지지 못하오.', '재고를 확인하시오.', '계획을 재고해 보시오.']:
        assert text(value)==value
    assert '아랫줄' in text('지지 午의 관계')
    assert '재물을 모으는' in text('재고 丑이오.')


def test_compound_names_are_explained_as_whole_concepts():
    for term in ('식상생재','관인상생','재다신약','관살','본기','월령','신강약'):
        assert term not in text(term+'를 살피오.')


def test_tied_counts_and_missing_time_are_not_hidden(f):
    tied=replace(f,ten_gods={key:1 for key in f.ten_gods})
    assert len(leaders(tied))==10
    assert '한 가지 성격으로 정하지' in build_depth(tied,'pungun','work')
    data=basis(f,'pungun','work',None)
    assert '시간은 제외' in data['birth']
    assert data['answers']==[]
    assert '올해' not in data['birth']


@pytest.mark.parametrize('lens',INTERVIEWS)
def test_every_specialist_separates_real_answers_from_chart_interpretation(f,lens):
    raw=build_scene(f,lens,'work')
    assert '아직 세부 상황을 듣지 못했으므로' in raw
    spec=INTERVIEWS[lens]
    first={'choice4':spec[2][0]['id'],'choice5':spec[4][0]['id']}
    other={'choice4':spec[2][-1]['id'],'choice5':spec[4][-1]['id']}
    a=build_scene(f,lens,'work',first); b=build_scene(f,lens,'work',other)
    assert a!=b
    assert spec[2][0]['label'] in a and spec[4][0]['label'] in a
    assert '직접 고른 답' in a and str(f.year_num) in a
    assert '아직 세부 상황' not in a


def test_new_year_changes_only_calculated_interpretation_not_selected_answers(f):
    topic={'choice4':'a','choice5':'b'}
    other=replace(f,year_num=2027,year_ten_god='정인')
    a=build_scene(f,'baegun','work',topic); b=build_scene(other,'baegun','work',topic)
    assert '2026' in a and '2027' in b
    assert basis(f,'baegun','work',topic)['answers']==basis(other,'baegun','work',topic)['answers']


def test_preview_is_a_real_partial_sentence_and_does_not_fabricate_authority():
    body='상관은 생각을 밖으로 드러내는 주제로 읽소. '+ '구체적인 상황에서는 실제 경험을 함께 확인해야 하오. '*8
    sample, complete=_reading_sample(body,'work','F')
    assert complete
    assert text(body,'work','F').startswith(sample)
    assert len(sample)<=100 and len(sample)<=len(text(body,'work','F'))//3
    long='하나둘셋넷다섯여섯일곱여덟아홉열 '*40
    sample,complete=_reading_sample(long,'work','F')
    assert not complete and len(sample)<=100
    short='기준을 정하고 일정을 조율하는 특징으로 읽소.'
    sample, complete=_reading_sample(short,'work','F',total_chars=360)
    assert sample==short and complete


def test_personal_reader_keeps_original_evidence_and_paid_lock(f):
    spec=enrich_spec(ask_spec('work'),'baegun','work')
    topic={('choice' if i==1 else f'choice{i}'):spec['options' if i==1 else f'options{i}'][0]['id'] for i in range(1,6)}
    result=build_report(f,'personal','baegun','free','work',extras={'topic':topic})
    assert not result['extra_error']
    assert result['reading_basis']['answers']==['시간이 촉박할 때','기회를 놓칠까 봐']
    for c in result['cuts']:
        if c['id'] in ('spine_depth','spine_scene'):
            assert c['html'] in c['reader_html']
            assert '<details class="reading-calculation">' in c['reader_html']
    assert all('html' not in c and 'reader_html' not in c for c in result['locked'])


def test_dense_evidence_stays_available_without_changing_numbers():
    raw='<p class="sm">이 그림이 나온 자리 — 정인 3 · 편인 2</p>'
    result=html(raw)
    assert result.startswith('<details') and raw in result
    assert re.findall(r'\d+',result)==['3','2']
