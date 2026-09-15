from datetime import datetime, timedelta, timezone
import experiments as E

def test_assignment_is_stable_and_balanced():
    assignments=[E.variant(f'{i:032x}') for i in range(10000)]
    assert 4900 <= sum(assignments) <= 5100
    assert assignments == [E.variant(f'{i:032x}') for i in range(10000)]

def test_mature_exposure_and_refund():
    now=datetime.now(timezone.utc); sid='a'*32
    old=(now-timedelta(days=8)).isoformat()
    rows=[{'name':'experiment_exposed','n':1,'sid':sid,'at':old}]*3
    rows.append({'name':'experiment_exposed','n':1,'sid':'b'*32,'at':now.isoformat()})
    order={'analytics_sid':sid,'paid_at':old,'amount':19900,'status':'canceled'}
    result=E.summary(rows,[order],now); group=result['groups'][E.variant(sid)]
    assert group['mature_visitors']==1 and group['buyers']==1
    assert group['gross']==group['refunds']==19900 and group['net']==0
    assert result['immature']==1 and result['decision']=='not_evaluated'

def test_out_of_window_and_renewal_are_not_new_conversions():
    now=datetime.now(timezone.utc);sid='c'*32
    events=[{'name':'experiment_exposed','n':1,'sid':sid,'at':(now-timedelta(days=9)).isoformat()}]
    orders=[{'analytics_sid':sid,'paid_at':now.isoformat(),'amount':14900,'status':'paid'},
            {'analytics_sid':sid,'paid_at':(now-timedelta(days=8)).isoformat(),'amount':14900,'status':'paid','renewal':True}]
    assert sum(g['buyers'] for g in E.summary(events,orders,now)['groups'])==0

def test_exposure_arm_is_server_assigned():
    import analytics
    sid='d'*32
    row=analytics._clean({'name':'experiment_exposed','screen':'a1','sid':sid,'n':1,'stage':999})
    assert row['stage']==E.variant(sid)
