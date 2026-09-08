import httpx,pytest
import payments

def test_billing_timeout_looks_up_same_order(monkeypatch):
    headers=[]
    monkeypatch.setattr(payments,'_auth_header',lambda:{})
    def post(*a,**k):
        headers.append(k['headers']['Idempotency-Key'])
        raise httpx.ReadTimeout('lost response')
    monkeypatch.setattr(payments.httpx,'post',post)
    monkeypatch.setattr(payments,'lookup_by_order',lambda oid:{'orderId':oid,'paymentKey':'pk','totalAmount':14900,'status':'DONE'})
    for _ in range(2):assert payments.charge_billing('bk','ck',14900,'same-order','sub').ok
    assert len(set(headers))==1

def test_billing_does_not_grant_wrong_amount(monkeypatch):
    monkeypatch.setattr(payments,'_auth_header',lambda:{})
    monkeypatch.setattr(payments.httpx,'post',lambda *a,**k:httpx.Response(200,json={'orderId':'oid','paymentKey':'pk','totalAmount':1,'status':'DONE'}))
    with pytest.raises(payments.PaymentError):payments.charge_billing('bk','ck',14900,'oid','sub')

def test_refund_timeout_recovers_only_confirmed_full_cancel(monkeypatch):
    monkeypatch.setattr(payments,'_auth_header',lambda:{})
    monkeypatch.setattr(payments.httpx,'post',lambda *a,**k:(_ for _ in ()).throw(httpx.ReadTimeout('lost')))
    monkeypatch.setattr(payments.httpx,'get',lambda *a,**k:httpx.Response(200,json={'orderId':'oid','paymentKey':'pk','totalAmount':9900,'status':'CANCELED'}))
    assert payments.cancel('pk','refund').status=='CANCELED'
    with pytest.raises(payments.PaymentError):payments.cancel('another-pk','refund')


def test_live_billing_requires_confirmed_contract_and_encryption(monkeypatch):
    monkeypatch.setattr(payments,'DISABLED_REASON',None)
    monkeypatch.setattr(payments,'LIVE',True)
    monkeypatch.setattr(payments,'sealing_problem',lambda:None)
    monkeypatch.delenv('TOSS_BILLING_APPROVED',raising=False)
    assert payments.subscriptions_problem()
    monkeypatch.setenv('TOSS_BILLING_APPROVED','true')
    assert payments.subscriptions_problem() is None
    monkeypatch.setattr(payments,'sealing_problem',lambda:'missing secret')
    assert payments.subscriptions_problem()
