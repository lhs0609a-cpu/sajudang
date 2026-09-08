"""
한 달 듣기 — 자동결제.

★ 여기서 **증명 못 하는 것**
    실제 빌링키 발급과 청구. PG 키가 없고, 자동결제는 토스와 따로
    계약해야 열립니다. 토스 테스트 키를 넣고 카드 한 장을 걸어 봐야
    끝납니다 (docs/17).

★ 여기서 증명하는 것
    · 카드 열쇠(빌링키)가 **어떤 응답에도 안 실린다** ← 가장 중요
    · 열쇠를 봉해서 저장한다 (SUB_SECRET)
    · 손님 열쇠를 화면이 못 지어낸다 (남의 카드로 긁는 길)
    · 카드를 걸기 전에 값·주기·다음 날·그만두는 길을 다 말한다
    · 그만둬도 **치른 달은 끝까지** 열려 있다
    · 그만둔 뒤에는 다시 안 긁는다
    · 갱신은 늦게 돌아도 손님이 하루도 손해 안 본다
    · 실패해도 바로 안 끊고, 네 번 실패하면 그만 긁는다
    · 달삯은 결제창(한 번 긁기)으로 안 판다
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.setenv("SUB_SECRET", "시험용-열쇠-0001")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "payments", "db", "main", "analytics")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
    import payments
    import store
    from routers import subscription as sub_mod
    return payments, store, sub_mod


def _sub(sub_mod, payments, **over):
    now = datetime.now(timezone.utc)
    s = {
        "user_key": "u0001", "session_id": "sess-sub-0001",
        "customer_key": "sjd_cust", "billing_key": payments.seal("bk_secret"),
        "card_last4": "1234", "card_name": "시험카드",
        "amount": payments.TIER_PRICE["sub"], "status": "live",
        "ending": False, "started_at": now.isoformat(),
        "period_end": (now + timedelta(days=30)).isoformat(),
        "months": 1, "fails": 0, "last_error": None,
        "chart_id": None, "concern": "love", "orders": ["sjd_sub_x"],
    }
    s.update(over)
    sub_mod._save(s)  # renew must re-read a persisted subscription, like the scheduler.
    return s


# ══════════════════════════════════════════════════════════
# 카드 열쇠 — 이게 새면 그 카드로 반복해서 긁힙니다
# ══════════════════════════════════════════════════════════
def test_the_card_key_is_sealed_before_it_is_stored(env):
    payments, _store, _sub_mod = env
    blob = payments.seal("bk_live_verysecret")
    assert blob != "bk_live_verysecret"
    assert blob.startswith("v1:")
    assert payments.unseal(blob) == "bk_live_verysecret"


def test_stale_scheduler_copy_cannot_charge_twice(env, monkeypatch):
    payments, store, mod = env
    s=_sub(mod,payments,period_end=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat())
    stale=dict(s); calls=[]
    def charge(*args):
        calls.append(args[3])
        return payments.PaymentResult(ok=True,order_id=args[3],amount=args[2],pg_tid='pk',status='DONE',raw={})
    monkeypatch.setattr(payments,'charge_billing',charge)
    mod._save(s)
    assert mod.renew(s)['ok']
    assert mod.renew(stale)['already']
    assert len(calls)==1


def test_renewal_recovers_after_local_write_failure(env,monkeypatch):
    payments, store, mod=env
    s=_sub(mod,payments,period_end=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat())
    mod._save(s); calls=[]
    def charge(*args):
        calls.append(args[3])
        return payments.PaymentResult(ok=True,order_id=args[3],amount=args[2],pg_tid='pk',status='DONE',raw={})
    monkeypatch.setattr(payments,'charge_billing',charge)
    real=mod._write_order
    monkeypatch.setattr(mod,'_write_order',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('disk')))
    with pytest.raises(RuntimeError): mod.renew(s)
    monkeypatch.setattr(mod,'_write_order',real)
    assert mod.renew(s)['ok']
    assert len(calls)==1


def test_uncertain_billing_does_not_consume_decline_limit(env,monkeypatch):
    payments, store, mod=env
    s=_sub(mod,payments,period_end=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat())
    monkeypatch.setattr(payments,'charge_billing',lambda *a: (_ for _ in ()).throw(payments.BillingUncertain('timeout')))
    result=mod.renew(s)
    assert result['retry'] and s['fails']==0


def test_registration_recovers_without_second_charge(env,monkeypatch):
    payments,store,mod=env
    sid='registration-recovery-0001'
    monkeypatch.setattr(payments,'subscriptions_problem',lambda:None)
    monkeypatch.setattr(payments,'issue_billing_key',lambda *a:{'billingKey':'bk','card':{}})
    charges=[]
    def charge(*a):
        charges.append(a[3])
        return payments.PaymentResult(ok=True,order_id=a[3],amount=a[2],pg_tid='pk',status='DONE',raw={})
    monkeypatch.setattr(payments,'charge_billing',charge)
    real=mod._write_order
    monkeypatch.setattr(mod,'_write_order',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('disk')))
    req=mod.RegisterRequest(session_id=sid,auth_key='ak',customer_key=mod._customer_key(sid))
    with pytest.raises(RuntimeError):mod.register(req)
    monkeypatch.setattr(mod,'_write_order',real)
    assert mod.register(req)['ok']
    assert len(charges)==1
    assert store.get_json('order:'+charges[0])['status']=='paid'


def test_a_different_secret_cannot_open_it(env, monkeypatch):
    payments, _store, _sub_mod = env
    blob = payments.seal("bk_live_verysecret")
    monkeypatch.setattr(payments, "SUB_SECRET", "다른-열쇠")
    with pytest.raises(payments.PaymentError):
        payments.unseal(blob)


def test_the_card_key_never_reaches_the_screen(env):
    """
    ★ 이 파일에서 가장 중요한 검사입니다.
      화면으로 내려보내는 꼴(`_view`)에 빌링키가 섞이면, 그 값을 쥔
      사람은 그 카드로 반복해서 긁을 수 있습니다. 카드 뒷자리만 갑니다.
    """
    payments, _store, sub_mod = env
    view = sub_mod._view(_sub(sub_mod, payments))
    flat = repr(view)
    assert "bk_secret" not in flat
    assert "billing_key" not in view
    assert "customer_key" not in view
    assert view["card"] == "1234"


def test_live_without_a_secret_refuses_to_open_subscriptions(env, monkeypatch):
    """
    라이브 키로 도는데 봉할 열쇠가 없으면 **구독을 안 엽니다.**
    맨몸으로 저장하느니 안 파는 편이 낫습니다.
    """
    payments, _store, _sub_mod = env
    monkeypatch.setattr(payments, "SUB_SECRET", "")
    monkeypatch.setattr(payments, "LIVE", True)
    monkeypatch.setattr(payments, "DISABLED_REASON", None)
    assert payments.subscriptions_problem()


# ══════════════════════════════════════════════════════════
# 손님 열쇠 — 화면이 지어내면 남의 카드로 긁힙니다
# ══════════════════════════════════════════════════════════
def test_the_customer_key_is_ours_not_the_screens(env):
    _payments, _store, sub_mod = env
    mine = sub_mod._customer_key("sess-a")
    assert mine == sub_mod._customer_key("sess-a")     # 늘 같아야 겹쳐 안 걸림
    assert mine != sub_mod._customer_key("sess-b")
    # 세션 아이디를 그대로 실어 보내지 않습니다 — 그건 자격의 열쇠입니다.
    assert "sess-a" not in mine


# ══════════════════════════════════════════════════════════
# 그만두기 — 시작한 길만큼 쉬워야 하고, 치른 달은 지켜야 합니다
# ══════════════════════════════════════════════════════════
def test_cancelling_does_not_take_back_the_month_already_paid(env):
    _payments, _store, sub_mod = env
    payments = _payments
    s = _sub(sub_mod, payments, ending=True)
    assert sub_mod.active(s), "그만뒀다고 남은 날을 뺏으면 안 되오"


def test_a_cancelled_seat_is_never_charged_again(env):
    _payments, _store, sub_mod = env
    past = datetime.now(timezone.utc) - timedelta(days=1)
    s = _sub(sub_mod, _payments, ending=True, period_end=past.isoformat())
    assert not sub_mod.due(s), "그만둔 사람을 또 긁으면 안 되오"


def test_a_dead_seat_is_never_charged_again(env):
    _payments, _store, sub_mod = env
    past = datetime.now(timezone.utc) - timedelta(days=1)
    s = _sub(sub_mod, _payments, status="dead", period_end=past.isoformat())
    assert not sub_mod.due(s)
    assert not sub_mod.active(s)


def test_retiring_throws_the_card_key_away(env):
    """
    ★ 그만둔 사람의 카드를 계속 들고 있을 까닭이 없습니다.
      들고 있으면 언젠가 실수로 긁힙니다.
    """
    payments, store, sub_mod = env
    s = _sub(sub_mod, payments)
    sub_mod.retire(s)
    assert not s["billing_key"]
    assert s["status"] == "dead"
    kept = store.get_json("sub:" + s["user_key"])
    assert not kept["billing_key"]
    # 기록은 남습니다 — 몇 달 들었는지는 지우지 않습니다.
    assert kept["months"] == 1


# ══════════════════════════════════════════════════════════
# 갱신
# ══════════════════════════════════════════════════════════
def test_a_late_renewal_does_not_cost_the_customer_a_day(env, monkeypatch):
    """
    ★ 다음 기간은 **끝난 날부터** 셉니다.
      오늘부터 세면 갱신이 늦어질 때마다 손님이 그만큼 손해 봅니다.
    """
    payments, _store, sub_mod = env
    ended = datetime.now(timezone.utc) - timedelta(days=2)
    s = _sub(sub_mod, payments, period_end=ended.isoformat())

    def _fake(billing_key, customer_key, amount, order_id, order_name):
        assert billing_key == "bk_secret", "봉한 것을 안 풀고 긁었소"
        assert amount == payments.TIER_PRICE["sub"]
        return payments.PaymentResult(
            ok=True, order_id=order_id, amount=amount, pg_tid="pk_1",
            status="DONE", raw={})

    monkeypatch.setattr(payments, "charge_billing", _fake)
    r = sub_mod.renew(s)
    assert r["ok"]
    got = datetime.fromisoformat(r["period_end"])
    assert (got - ended).days == sub_mod.PERIOD_DAYS


def test_renewing_twice_in_a_day_does_not_charge_twice(env, monkeypatch):
    payments, _store, sub_mod = env
    ended = datetime.now(timezone.utc) - timedelta(hours=1)
    s = _sub(sub_mod, payments, period_end=ended.isoformat())
    monkeypatch.setattr(
        payments, "charge_billing",
        lambda *a, **k: payments.PaymentResult(
            ok=True, order_id=a[3], amount=a[2], pg_tid="pk", status="DONE",
            raw={}))
    assert sub_mod.due(s)
    sub_mod.renew(s)
    assert not sub_mod.due(s), "긁고 나서도 또 긁을 때라 하면 두 번 나가오"


def test_one_failure_does_not_close_the_door(env, monkeypatch):
    """카드 한도·유효기간은 사흘이면 손님이 고칩니다. 그동안 열어 둡니다."""
    payments, _store, sub_mod = env
    ended = datetime.now(timezone.utc) - timedelta(hours=1)
    s = _sub(sub_mod, payments, period_end=ended.isoformat())

    def _boom(*a, **k):
        raise payments.PaymentError("한도를 넘었소")

    monkeypatch.setattr(payments, "charge_billing", _boom)
    r = sub_mod.renew(s)
    assert not r["ok"] and r["fails"] == 1
    assert sub_mod.active(s), "한 번 실패했다고 바로 닫으면 안 되오"


def test_four_failures_stop_the_charging(env, monkeypatch):
    """계속 긁으면 카드사가 우리를 막습니다."""
    payments, _store, sub_mod = env
    ended = datetime.now(timezone.utc) - timedelta(hours=1)
    s = _sub(sub_mod, payments,
             period_end=ended.isoformat(), fails=sub_mod.MAX_FAILS - 1)
    monkeypatch.setattr(
        payments, "charge_billing",
        lambda *a, **k: (_ for _ in ()).throw(payments.PaymentError("안 되오")))
    sub_mod.renew(s)
    assert s["status"] == "dead"
    assert not s["billing_key"], "그만 긁기로 했으면 열쇠도 버리오"
    assert not sub_mod.due(s)


# ══════════════════════════════════════════════════════════
# 고지 — 카드를 걸기 **전에** 넷을 다 말한다 (docs/11 §5)
# ══════════════════════════════════════════════════════════
def test_the_notice_says_all_four_things(env):
    payments, _store, sub_mod = env
    when = datetime.now(timezone.utc) + timedelta(days=30)
    joined = " ".join(sub_mod._terms(payments.TIER_PRICE["sub"], when))
    assert format(payments.TIER_PRICE["sub"], ",") in joined, "얼마인지"
    assert "달마다" in joined, "얼마마다인지"
    assert "%d월 %d일" % (when.month, when.day) in joined, "언제 처음 다시인지"
    assert "그만두" in joined, "어떻게 그만두는지"


# ══════════════════════════════════════════════════════════
# 값
# ══════════════════════════════════════════════════════════
def test_the_monthly_seat_costs_more_than_one_seat(env):
    """
    ★ 달삯이 「이 자리 하나」와 같은 값이면 한 사람은 아무도 안 고릅니다.
      같은 값에 한 명과 스무 명이 놓이기 때문입니다.
    """
    payments, _store, _sub_mod = env
    from engine import lens as lens_mod
    floor = min(int(l["price"]) for l in lens_mod.all_lenses()
                if int(l["price"]) > 0)
    assert payments.TIER_PRICE["sub"] > floor


def test_all_costs_more_than_the_dearest_seat(env):
    """세 목패에 순서가 있어야 합니다. all 이 가장 비싼 캐릭터 아래면
    「스무 사람 전부」가 「이 자리 하나」에 잡아먹힙니다."""
    payments, _store, _sub_mod = env
    from engine import lens as lens_mod
    top = max(int(l["price"]) for l in lens_mod.all_lenses())
    assert payments.TIER_PRICE["all"] > top
