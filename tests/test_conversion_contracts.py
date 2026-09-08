import pytest


def test_approval_timeout_recovers_only_matching_psp_result(monkeypatch):
    import httpx
    import payments
    monkeypatch.setattr(payments,"_auth_header",lambda:{})
    headers=[]
    def timeout(*args,**kwargs):
        headers.append(kwargs["headers"])
        raise httpx.ReadTimeout("timeout")
    monkeypatch.setattr(payments.httpx,"post",timeout)
    data={"orderId":"random-order-1234","paymentKey":"pk","totalAmount":15900,"status":"DONE"}
    monkeypatch.setattr(payments,"lookup_by_order",lambda _:data)
    for _ in range(2):
        result=payments.confirm("pk","random-order-1234",15900)
        assert result.ok and result.amount == 15900
    assert headers[0]["Idempotency-Key"] == headers[1]["Idempotency-Key"]
    data["totalAmount"]=1
    with pytest.raises(payments.PaymentError):
        payments.confirm("pk","random-order-1234",15900)


@pytest.mark.parametrize("status",["READY","IN_PROGRESS","WAITING_FOR_DEPOSIT","CANCELED"])
def test_unfinished_or_canceled_payment_does_not_grant(status):
    import payments
    with pytest.raises(payments.PaymentError):
        payments._verified_result({"orderId":"oid","paymentKey":"pk","totalAmount":9900,"status":status},"pk","oid",9900)


def test_practice_is_complete_and_explicitly_not_a_prediction():
    from engine.practice import build,PRACTICES
    assert set(PRACTICES) == {"love","money","health","work","people","dir"}
    assert build("unrecognized") is None
    actions=[]
    for concern in PRACTICES:
        item=build(concern)
        assert item["source_kind"] == "general_practice"
        assert "사주 계산 결과가 아닙니다" in item["source"]
        assert len(item["action"]) > 30
        actions.append(item["action"])
    assert len(set(actions)) == 6


def test_unknown_hour_stays_unknown_with_free_practice():
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.report import build_report
    f=build_features(build_chart(1993,11,25,None,None,"F",hour_known=False))
    free=build_report(f,"test-chart","wolha","free","love")
    paid=build_report(f,"test-chart","wolha","one","love")
    assert free["practice"] == paid["practice"]
    assert not f.hour_known
