from engine import bank
from engine.calendar import build_chart
from engine.features import build_features


def test_opening_checks_experience_instead_of_inventing_history():
    for row in bank.bank()['STAB'].values():
        for text in row.values():assert text.endswith('?')
    assert '자가진단' not in bank.bank()['IGKEY']['편인']['health']


def test_rejection_is_respected_for_every_hook_stage():
    f=build_features(build_chart(1993,11,25,None,0,'F',hour_known=False))
    for concern in bank.bank()['STAB']:
        for misses in (0,3):
            for segment in bank.build_hook(f,concern,misses=misses):
                assert '맞지 않는 해석' in segment['no']
                assert '아직 안 터진' not in segment['no']
                assert segment['statement_id'].endswith(':copy2')
                assert '그럴 줄 알았소' not in segment['yes']
