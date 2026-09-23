"""Short-lived, anonymous activity. Only settled live payments become notices."""
import hashlib
import time
from datetime import datetime

import store

WINDOW = 60
RECENT = 3600


def record_purchase(order_id, order):
    import payments
    if not payments.LIVE or order.get('status') != 'paid' or order.get('amount', 0) <= 0:
        return
    with store.payment_lease('public-purchases') as check:
        rows = store.get_json('public-purchases') or []
        rows = [r for r in rows if r['at'] > time.time() - RECENT and r['order'] != order_id]
        rows.append({'order': order_id, 'at': datetime.fromisoformat(order['paid_at']).timestamp()})
        check()
        store.set_json('public-purchases', rows[-30:], ttl=RECENT)


def snapshot(visitor, screen):
    now = time.time()
    key = 'public-presence:' + screen
    identity = hashlib.sha256(visitor.encode()).hexdigest()
    with store.payment_lease(key) as check:
        peers = {k: v for k, v in (store.get_json(key) or {}).items() if v > now - WINDOW}
        if len(peers) < 10000 or identity in peers:
            peers[identity] = now
        check()
        store.set_json(key, peers, ttl=WINDOW + 10)
    notices = []
    # Re-read order status: refunded/canceled receipts must disappear immediately.
    for row in reversed(store.get_json('public-purchases') or []):
        if not 0 <= now - row['at'] < RECENT:
            continue
        order = store.get_json('order:' + row['order']) or {}
        if order.get('status') != 'paid' or order.get('amount', 0) <= 0:
            continue
        notices.append({'id': hashlib.sha256(('notice:' + row['order']).encode()).hexdigest()[:24],
                        'minutes_ago': int((now - row['at']) / 60),
                        'text': '한 분의 유료 풀이 결제가 완료되었습니다.'})
    return {'active_browsers': len(peers), 'window_seconds': WINDOW, 'purchases': notices[:3]}
