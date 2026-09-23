"""One welcome credit per account; all financial state is server-authoritative."""
import secrets
import time
from contextlib import ExitStack
from fastapi import HTTPException
import member_accounts as accounts
import store

PERCENT = 5
LIFETIME = 7 * 86400
RELATIONS = {
    'lover': ('연인', '맞고 틀림보다 서로 원하는 반응을 한 문장씩 먼저 말해 보세요.'),
    'family': ('가족', '가족이라서 안다고 넘기지 말고, 이번 주 필요한 도움을 하나씩 물어보세요.'),
    'relative': ('친지', '가까움의 정도가 다를 수 있으니 연락과 부탁의 편한 범위를 먼저 맞춰보세요.'),
    'friend': ('친구', '해결책을 주기 전에 지금은 공감과 조언 중 무엇이 필요한지 먼저 물어보세요.'),
    'coworker': ('동료', '일의 우선순위와 책임 범위를 말로 확인하면 서로의 다른 속도가 장점이 됩니다.'),
    'other': ('소중한 사람', '관계를 단정하지 말고, 서로 편해지는 행동 하나를 직접 확인해 보세요.'),
}
FLOW_WORD = {'비겁':'사람과 나란히 서는 데', '식상':'표현하고 만들어 내는 데',
             '재성':'현실적인 결과를 챙기는 데', '관성':'책임과 기준을 지키는 데',
             '인성':'생각을 정리하고 이해하는 데'}


def invite(account):
    key = 'invite-owner:' + account['id']
    with store.payment_lease(key):
        code = store.get_json(key)
        if not code:
            code = secrets.token_urlsafe(24)
            store.set_json(key, code)
            store.set_json('invite:' + code, {'owner':account['id'], 'created_at':time.time()})
    return code


def claim(account, code, relation='other'):
    if relation not in RELATIONS:
        raise HTTPException(422, '함께 볼 관계를 다시 선택해 주세요.')
    row = store.get_json('invite:' + code)
    if not row or not store.get_json('member:' + row['owner']):
        raise HTTPException(404, '초대 링크를 확인해 주세요.')
    if row['owner'] == account['id']:
        raise HTTPException(409, '내 초대 링크에는 혜택을 적용할 수 없습니다.')
    if account['created_at'] < row['created_at']:
        raise HTTPException(409, '초대받아 새로 가입한 계정의 첫 혜택입니다.')
    with ExitStack() as stack:
        for key in sorted({row['owner'], account['id']}):
            stack.enter_context(store.payment_lease('referral:' + key))
        old = store.get_json('referral-claim:' + account['id'])
        if old and old != code:
            raise HTTPException(409, '이미 다른 초대 혜택을 받았습니다.')
        store.set_json('referral-claim:' + account['id'], code)
        store.set_json('referral-pair:' + account['id'], {
            'owner':row['owner'], 'invited':account['id'], 'relation':relation,
            'created_at':time.time()})
        pair_key = 'referral-pairs:' + row['owner']
        pairs = store.get_json(pair_key) or []
        if account['id'] not in pairs:
            store.set_json(pair_key, [account['id'], *pairs][:100])
        for member_id in (row['owner'], account['id']):
            key = 'referral-credit:' + member_id
            if not store.get_json(key):
                # Never reset an expired or consumed credit on another invitation.
                store.set_json(key, {'percent':PERCENT, 'expires_at':time.time()+LIFETIME,
                                     'status':'ready', 'order_id':None})
    return status(account)


def _profile(member_id):
    """Only comparison axes; never return birth data, pillars, names or account IDs."""
    library = store.get_json('member-library:' + member_id) or []
    for rid in library:
        record_key = 'member-reading:' + member_id + ':' + rid
        record = store.get_json(record_key)
        profile = (record or {}).get('compare_profile')
        if profile:
            return profile
        # Readings saved before together-view existed do not have a comparison
        # profile. Derive and persist only the five safe axes so existing members
        # can participate without saving the same reading again.
        if record and record.get('birth'):
            from routers.chart import post_chart
            from schemas.api import ChartRequest
            chart = post_chart(ChartRequest(**record['birth']))
            profile = {key:chart.features[key] for key in (
                'flow', 'top_ten_god', 'strength', 'strong_el', 'weak_el')}
            record['compare_profile'] = profile
            store.set_json(record_key, record)
            return profile
    return None


def _comparison(mine, theirs, relation):
    same_flow = mine['flow'] == theirs['flow']
    if same_flow:
        shared = '두 사람 모두 힘을 %s 쓰는 편이라, 중요한 순간에 같은 곳을 먼저 봅니다.' % FLOW_WORD[mine['flow']]
    else:
        shared = '나는 힘을 %s 쓰고, 상대는 %s 씁니다. 서로 다른 부분을 맡으면 균형이 생깁니다.' % (
            FLOW_WORD[mine['flow']], FLOW_WORD[theirs['flow']])
    if mine['strength'] == theirs['strength']:
        difference = '결정의 속도는 비슷하지만, 나는 %s을 먼저 보고 상대는 %s을 먼저 봅니다.' % (
            mine['top_ten_god'], theirs['top_ten_god'])
    else:
        difference = '나는 %s 쪽이고 상대는 %s 쪽이라, 같은 일도 밀어붙이는 속도와 쉬어 가는 시점이 다릅니다.' % (
            mine['strength'], theirs['strength'])
    if mine['strong_el'] == theirs['weak_el']:
        watch = '내게 자연스러운 %s의 방식이 상대에게는 버거울 수 있습니다. 익숙하다고 재촉하지 않는 것이 중요합니다.' % mine['strong_el']
    elif theirs['strong_el'] == mine['weak_el']:
        watch = '상대에게 자연스러운 %s의 방식이 내게는 버거울 수 있습니다. 모른다는 말보다 필요한 속도를 알려주세요.' % theirs['strong_el']
    elif mine['weak_el'] == theirs['weak_el']:
        watch = '두 사람 모두 %s의 힘이 모자라기 쉬워, 미루는 일을 서로 눈치만 보면 오래 남을 수 있습니다.' % mine['weak_el']
    else:
        watch = '서로 부족한 자리가 다릅니다. 상대가 힘들어하는 일을 내 기준으로 쉽다고 판단하지 않는 것이 중요합니다.'
    return {'shared':shared, 'difference':difference, 'watch':watch,
            'action':RELATIONS[relation][1]}


def comparisons(account):
    mine = _profile(account['id'])
    pair_ids = []
    own_pair = store.get_json('referral-pair:' + account['id'])
    if own_pair:
        pair_ids.append(account['id'])
    pair_ids.extend(store.get_json('referral-pairs:' + account['id']) or [])
    result = []
    seen = set()
    for invited_id in pair_ids:
        pair = store.get_json('referral-pair:' + invited_id)
        if not pair or account['id'] not in (pair['owner'], pair['invited']):
            continue
        other_id = pair['owner'] if account['id'] == pair['invited'] else pair['invited']
        token = ':'.join(sorted((account['id'], other_id)))
        pair_id = accounts.digest('comparison:' + token)[:24]
        if pair_id in seen:
            continue
        seen.add(pair_id)
        theirs = _profile(other_id)
        relation = pair.get('relation') if pair.get('relation') in RELATIONS else 'other'
        row = {'id':pair_id, 'relation':relation, 'relation_label':RELATIONS[relation][0],
               'status':'ready' if mine and theirs else 'waiting'}
        if mine and theirs:
            row.update(_comparison(mine, theirs, relation))
        result.append(row)
    return result


def forget(account):
    """Remove comparison links when a member withdraws; payment records stay separate."""
    member_id = account['id']
    own_pair = store.get_json('referral-pair:' + member_id)
    if own_pair:
        owner_key = 'referral-pairs:' + own_pair['owner']
        store.set_json(owner_key, [i for i in (store.get_json(owner_key) or []) if i != member_id])
        store.delete('referral-pair:' + member_id)
    for invited_id in store.get_json('referral-pairs:' + member_id) or []:
        pair = store.get_json('referral-pair:' + invited_id)
        if pair and pair.get('owner') == member_id:
            store.delete('referral-pair:' + invited_id)
    code = store.get_json('invite-owner:' + member_id)
    if code:
        store.delete('invite:' + code)
    for prefix in ('invite-owner:', 'referral-pairs:', 'referral-claim:', 'referral-credit:'):
        store.delete(prefix + member_id)


def status(account):
    row = store.get_json('referral-credit:' + account['id'])
    if not row:
        return None
    state = row['status']
    if state == 'ready' and row['expires_at'] <= time.time():
        state = 'expired'
    return {'percent':row['percent'], 'expires_at':row['expires_at'], 'status':state}


def credit_for(session_id):
    owner = accounts.owner(session_id)
    row = store.get_json('referral-credit:' + owner) if owner else None
    if row and row['status'] == 'reserved' and time.time() - row.get('reserved_at', time.time()) > 86460 and not store.get_json('order:' + row['order_id']):
        # Pending orders have a one-day TTL and cannot be confirmed once absent.
        # Serialize recovery with reservations; never revive a paid/used credit.
        with store.payment_lease('referral:' + owner):
            row = store.get_json('referral-credit:' + owner)
            if row['status'] == 'reserved' and time.time() - row.get('reserved_at', time.time()) > 86460 and not store.get_json('order:' + row['order_id']):
                row.update(status='ready', order_id=None)
                store.set_json('referral-credit:' + owner, row)
    if row and row['status'] == 'ready' and row['expires_at'] > time.time():
        return owner, row
    return owner, None


def quote(base, tier, session_id):
    import promotions
    price = promotions.quote(base, tier)
    owner, credit = credit_for(session_id)
    if tier in ('one', 'all') and credit:
        discounted = base * (100 - credit['percent']) // 100
        if discounted < price['price']:
            price.update(price=discounted, promotion=None, referral={'percent':credit['percent'], 'expires_at':credit['expires_at']})
    return price


def reserve(session_id, order_id, quote):
    if not quote.get('referral'):
        return
    owner = accounts.owner(session_id)
    with store.payment_lease('referral:' + str(owner)):
        row = store.get_json('referral-credit:' + str(owner))
        if not row or row['status'] != 'ready' or row['expires_at'] <= time.time():
            raise HTTPException(409, '초대 할인이 이미 다른 주문에 적용되었습니다. 구매 내역을 확인해 주세요.')
        row.update(status='reserved', order_id=order_id, reserved_at=time.time())
        store.set_json('referral-credit:' + owner, row)


def pending(session_id, chart_id, lens_id, tier):
    owner = accounts.owner(session_id)
    row = store.get_json('referral-credit:' + owner) if owner else None
    order = store.get_json('order:' + row['order_id']) if row and row['status'] == 'reserved' else None
    if order and order['status'] == 'pending' and all(order.get(k) == v for k,v in (
            ('session_id',session_id),('chart_id',chart_id),('lens_id',lens_id),('tier',tier))):
        return row['order_id'], order
    return None


def settle(order_id, order):
    if not order.get('price_quote', {}).get('referral'):
        return
    owner = accounts.owner(order['session_id'])
    with store.payment_lease('referral:' + str(owner)):
        row = store.get_json('referral-credit:' + str(owner))
        if row and row.get('order_id') == order_id:
            row['status'] = 'used'
            store.set_json('referral-credit:' + owner, row)
