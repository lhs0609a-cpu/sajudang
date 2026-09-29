from datetime import date
import pytest
from engine.calendar import build_chart, daeun_periods
from engine.features import build_features
from engine.constants import GAN, JI, ten_god


@pytest.mark.parametrize('sex',['M','F'])
@pytest.mark.parametrize('year',[1900,1920,1935,1960,1993,2008])
def test_current_age_always_belongs_to_the_current_decade(year,sex):
    chart=build_chart(year,5,17,12,0,sex,True)
    f=build_features(chart,as_of=date(2026,9,29))
    current=f.daeun[f.daeun_now]
    assert current['start_age']<=f.age<current['start_age']+10
    assert current['ten_god']==ten_god(current['gan'],f.day_gan)
    assert f.daeun_ten_god==current['ten_god']
    assert [d['gz'] for d in f.daeun[:8]]==[d.gz for d in chart.daeun]
    step=1 if chart.forward else -1
    for previous,following in zip(f.daeun,f.daeun[1:]):
        assert following['gan']==GAN[(GAN.index(previous['gan'])+step)%10]
        assert following['ji']==JI[(JI.index(previous['ji'])+step)%12]
        assert following['start_age']==previous['start_age']+10


def test_extension_happens_at_the_end_of_the_last_decade_without_mutating_chart():
    chart=build_chart(1920,5,17,12,0,'F',True)
    end=chart.daeun[-1].start_age+10
    before=build_features(chart,as_of=date(1920+end-1,9,29))
    after=build_features(chart,as_of=date(1920+end,9,29))
    assert len(before.daeun)==8
    assert after.daeun_now==8
    assert len(after.daeun)==10
    assert len(chart.daeun)==8
    assert after.daeun[8]['start_age']==end


def test_before_first_decade_does_not_invent_an_active_period():
    chart=build_chart(2026,5,17,12,0,'F',True)
    f=build_features(chart,as_of=date(2026,9,29))
    assert not f.daeun_started and len(f.daeun)==8


def test_hook_cache_changes_with_calculation_version(monkeypatch):
    from routers import chart,hook
    from schemas.api import ChartRequest,HookRequest
    result=chart.post_chart(ChartRequest(year=1920,month=5,day=17,sex='F',hour_known=False))
    request=HookRequest(chart_id=result.chart_id,lens_id='pungun',concern='work')
    monkeypatch.setattr(hook,'ENGINE_VER','lifetime-a')
    assert not hook.post_hook(request).cached
    assert hook.post_hook(request).cached
    monkeypatch.setattr(hook,'ENGINE_VER','lifetime-b')
    assert not hook.post_hook(request).cached


def test_january_midnight_keeps_the_actual_birth_year_for_age():
    chart=build_chart(1951,1,1,0,0,'M',True)
    f=build_features(chart,as_of=date(2026,9,29))
    assert f.birth_year==1951
    assert f.age==75
