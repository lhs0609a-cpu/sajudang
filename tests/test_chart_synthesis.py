"""Evidence and sensitivity, rather than 'every string must be unique'."""
from dataclasses import replace
from datetime import date
import re

import pytest
from engine.calendar import build_chart
from engine.features import build_features
from engine.constants import ELEMENT_OF_GAN, GENERATES, CONTROLS, TEN_GOD_GROUP, ten_god
from engine.chart_synthesis import analyze, contacts, core, relation, timing_text, period, balance
from engine.personal_reading import INTERVIEWS
from engine.report import build_report


def feature(year=1993, month=11, day=25, hour=None):
    return build_features(build_chart(year,month,day,hour,0 if hour is not None else None,'F',hour is not None),as_of=date(2026,9,29))


def normalized(value):
    return re.sub(r'[0-9一-龥\s]+','',value)


def test_same_top_role_does_not_force_same_explanation():
    # Find a real pair with the same dominant role but different structure.
    seen={}
    for year in range(1970,2001):
        f=feature(year,5,17,12)
        if f.top_ten_god in seen:
            other=seen[f.top_ten_god]
            if f.strength != other.strength:
                assert normalized(core(f,'baegun','work')) != normalized(core(other,'baegun','work'))
                return
        seen[f.top_ten_god]=f
    pytest.fail('fixture did not exercise equal top role with different balance')


def test_position_changes_explanation_even_with_identical_counts():
    f=feature()
    pillars=[dict(p) for p in f.pillars]
    month=next(p for p in pillars if p['label']=='월주')
    month['gan']='甲' if month['gan']!='甲' else '乙'
    month['gz']=month['gan']+month['ji']
    other=replace(f,pillars=pillars)
    assert other.ten_gods==f.ten_gods
    assert analyze(f)['month_role'] != analyze(other)['month_role']
    assert normalized(core(f,'baegun','work')) != normalized(core(other,'baegun','work'))


def test_balance_changes_recommendation_without_changing_top_role():
    f=feature()
    weak=replace(f,strength='신약',year_ten_god='정인')
    strong=replace(f,strength='신강',year_ten_god='정인')
    assert analyze(weak)['priority']=='support'
    assert analyze(strong)['priority']=='deliver'
    assert weak.top_ten_god==strong.top_ten_god
    assert '함께할 사람' in core(weak,'pungun','work')
    assert '결과 하나' in core(strong,'pungun','work')


def test_five_role_relations_match_element_direction():
    # Exhaust all 100 actual stem pairs relative to a fixed day stem.
    for a in ELEMENT_OF_GAN:
        for b in ELEMENT_OF_GAN:
            ea,eb=ELEMENT_OF_GAN[a],ELEMENT_OF_GAN[b]
            expected=('same' if ea==eb else 'produces' if GENERATES[ea]==eb else
                      'controls' if CONTROLS[ea]==eb else 'controlled_by' if CONTROLS[eb]==ea else 'supported_by')
            assert relation(TEN_GOD_GROUP[ten_god(a,'甲')],TEN_GOD_GROUP[ten_god(b,'甲')])==expected


def test_contact_positions_are_not_interchangeable():
    pillars=[{'label':label,'ji':ji} for label,ji in [('년주','午'),('월주','丑'),('일주','子'),('시주','寅')]]
    rows=contacts(pillars,'子')
    assert [(r['position'],r['kind']) for r in rows]==[('년주','clash'),('월주','join'),('일주','repeat')]


def test_annual_branch_changes_timing_even_if_annual_stem_is_same():
    f=feature()
    a=replace(f,year_gz='丙午'); b=replace(f,year_gz='丙辰')
    assert a.year_ten_god==b.year_ten_god
    assert analyze(a)['year_contacts'] != analyze(b)['year_contacts']
    assert normalized(period(a,'work')) != normalized(period(b,'work'))


def test_no_current_period_or_unknown_hour_is_invented():
    f=replace(feature(),daeun_started=False)
    s=analyze(f)
    assert s['period_group'] is None and s['period_contacts']==[]
    assert '시주' not in s['root_positions']
    assert not any(r['position']=='시주' for r in s['year_contacts'])
    assert '첫 10년 운에 들어가기 전' in ''.join(timing_text(f,s))
    assert '계산상' not in ''.join(timing_text(f,s))


def test_same_chart_is_deterministic_and_not_artificially_unique():
    f=feature()
    assert core(f,'baegun','work')==core(feature(),'baegun','work')
    # Merely changing a calendar year number cannot earn interpretation diversity.
    other=replace(f,year_num=f.year_num+1)
    assert normalized(period(f,'work'))==normalized(period(other,'work'))


@pytest.mark.parametrize('lens',INTERVIEWS)
def test_all_characters_deliver_composite_reading_and_keep_paywall(lens):
    f=feature()
    report=build_report(f,'synthesis',lens,'all','work')
    for key in ('spine_depth','why','daeun_now','yongsin'):
        cut=next(c for c in report['cuts'] if c['id']==key)
        assert 'chart-synthesis' in cut['reader_html'], (lens,key)
    scene=next(c for c in report['cuts'] if c['id']=='spine_scene')
    assert '올해 글자가 닿는 생활 자리' in scene['reader_html']
    free=build_report(f,'synthesis',lens,'free','work')
    assert all('reader_html' not in c and 'html' not in c for c in free['locked'])
    assert free['reading_basis']['answers']==[]


def test_balance_does_not_prescribe_lucky_goods_or_claim_missing_ability():
    value=balance(feature(),'money')
    assert '물건이나 색깔 하나로 바꾸지는 않소' in value
    assert '능력이 없' not in value or '없다는 뜻은 아니오' in value
