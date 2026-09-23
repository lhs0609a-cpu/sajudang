"""Member credentials and ownership on the existing durable store."""
import hashlib
import hmac
import re
import secrets
import time
import uuid
from contextlib import ExitStack
from fastapi import HTTPException
import store
import throttle

TOKEN_SECONDS=30*24*3600
ITERATIONS=600_000


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password, salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),ITERATIONS).hex()


def password_matches(password, encoded):
    return hmac.compare_digest(password_hash(password,encoded.split(':')[0]),encoded)


_DUMMY_HASH=password_hash('unused-password','00'*16)


def username(value):
    value=value.strip().lower()
    if not re.fullmatch(r'[a-z0-9_]{4,32}',value):
        raise HTTPException(422,'아이디는 영문 소문자·숫자·밑줄 4~32자로 입력해 주세요.')
    return value


def limit(bucket,key,count=10):
    try:throttle.check('member-'+bucket,key,limit=count,window=900,say='시도가 너무 많습니다. 15분 후 다시 시도해 주세요.')
    except throttle.TooMany as exc:raise HTTPException(429,str(exc))


def owner(session_id):
    return store.get_json('member-owner:'+digest(session_id)) if session_id else None


# 선결제한 브라우저의 난수.
#
# ★ 여기가 `[a-f0-9-]{32,36}` 였습니다 — `crypto.randomUUID()` 의 꼴만
#   받는 자입니다. 그런데 `lib/store.newSessionId` 는 그것이 없는
#   자리(비보안 컨텍스트·구형 브라우저)에서 `s` + 36진수로 물러섭니다.
#   그 꼴은 자에 안 맞아 **새 uuid 로 갈아치웠고**, 그 순간 치른 주문이
#   통째로 갈 곳을 잃었습니다. 409 도 안 떴습니다 — 빈 보관함이 달린
#   계정이 조용히 만들어졌습니다.
#
#   자를 넓혀 **화면이 실제로 만드는 꼴을 다 받습니다.** 열여섯 자를
#   바닥으로 둔 것은 아무 클라이언트도 그보다 짧게 안 만들기 때문이오 —
#   그보다 짧은 난수에 주문이 붙어 있으면 조용히 버리지 않고 멈춥니다
#   (`register` 가 409 를 냅니다). 결제 라우터는 8~64자를 받습니다.
SESSION=re.compile(r'[A-Za-z0-9_-]{16,64}')


def session_orders(session_id):
    return sorted(store.get_json('orders:'+session_id) or []) if session_id else []


def bound_member(order_id):
    order=store.get_json('order:'+order_id) or {}
    return store.get_json('member-order:'+order_id) or order.get('member_id') or owner(order.get('session_id'))


def _seal_key(session_id):
    return 'seals:'+hashlib.sha256(session_id.encode()).hexdigest()[:16]


def sessions(session_id):
    """이 난수와 **같은 계정에 붙은** 난수 전부.

    ★ 자격은 이 묶음으로 섭니다(`report._paid_orders`). 주문을 계정
      쪽으로 **옮기지 않고** 난수를 묶는 까닭은 승인 시차 때문입니다 —
      손님이 값을 치르고 승인이 도는 동안(settling) 로그인하면, 그때는
      `orders:` 에 아직 그 주문이 없습니다. 옮겨 붙이는 방식이면 그
      주문은 영영 뒤에 남습니다. 묶어 두면 나중에 서는 주문도 같이
      열립니다.
    """
    account_id=owner(session_id)
    if not account_id:return [session_id]
    account=store.get_json('member:'+account_id) or {}
    ordered=[account.get('session_id'),*(store.get_json('member-sessions:'+account_id) or [])]
    return [s for i,s in enumerate(ordered) if s and s not in ordered[:i]] or [session_id]


def attach(account,session_id):
    """선결제한 브라우저를 이 계정에 잇는다.

    ★ 이 집은 **값을 먼저 치르고 나중에 가입**하는 집입니다. 그래서
      잇는 일은 가입에만 있으면 안 됩니다 — 전에 계정을 만든 손님이
      로그아웃 상태에서 치르고 **로그인**하면, 가입 경로를 한 번도
      안 지나므로 그 구매가 계정에 안 붙었습니다. 자격은
      `orders:<계정 난수>` 로만 서는데(`report.entitled_tier`),
      로그인하는 순간 화면의 난수가 계정 것으로 갈리므로 브라우저에서도
      사라졌습니다. 값은 치렀는데 아무 데서도 안 열립니다.

      주문 기록의 `session_id` 는 손대지 않습니다 — 환불·복원이 그걸로
      댑니다. 난수만 계정 밑에 묶습니다.
    """
    sid=(session_id or '').strip()
    if not SESSION.fullmatch(sid) or sid==account['session_id']:return []
    held=owner(sid)
    if held==account['id']:return session_orders(sid)
    if held:
        # 남의 계정이 쓰던 브라우저다. 조용히 넘기지 않는다 — 넘기면
        # 그 손님은 「가입했는데 결제한 게 없다」 만 봅니다.
        if session_orders(sid):raise HTTPException(409,'이 브라우저의 구매는 다른 계정에 연결되어 있습니다. 그 계정으로 로그인해 주세요.')
        return []
    order_ids=session_orders(sid)
    try:
        with store.payment_lease('member-browser:'+digest(sid)), ExitStack() as ownership:
            for oid in order_ids:ownership.enter_context(store.payment_lease('member-order:'+oid))
            for oid in order_ids:
                bound=bound_member(oid)
                if bound and bound!=account['id']:raise HTTPException(409,'이 브라우저의 구매는 다른 계정에 연결되어 있습니다. 그 계정으로 로그인해 주세요.')
            linked=[s for s in (store.get_json('member-sessions:'+account['id']) or []) if s!=sid]+[sid]
            # 치른 것이 없는 난수만 솎습니다. 주문이 붙은 난수는 안 버립니다.
            if len(linked)>50:linked=[s for s in linked if session_orders(s)][-50:]
            store.set_json('member-sessions:'+account['id'],linked)
            for oid in order_ids:store.set_json('member-order:'+oid,account['id'])
            # 인장도 치른 값에 딸린 것이오. 주문만 잇고 두면 인장첩이 빕니다.
            seals=store.get_json(_seal_key(sid)) or []
            if seals:
                held_seals=store.get_json(_seal_key(account['session_id'])) or []
                store.set_json(_seal_key(account['session_id']),held_seals+[s for s in seals if s not in held_seals])
            # 잇고 나서 잠급니다 — 이 난수를 다른 가입이 다시 주워 갈 수 없습니다.
            store.set_json('member-owner:'+digest(sid),account['id'])
            return order_ids
    except store.LeaseBusy:raise HTTPException(409,'구매를 연결하는 중입니다. 잠시 후 다시 확인해 주세요.')


def issue(account):
    token=secrets.token_urlsafe(32)
    store.set_json('member-token:'+digest(token),{'id':account['id'],'version':account['version']},ttl=TOKEN_SECONDS)
    return token


def authenticate(authorization):
    token=(authorization or '').removeprefix('Bearer ')
    row=store.get_json('member-token:'+digest(token)) if token else None
    account=store.get_json('member:'+row['id']) if row else None
    if not account or row['version']!=account['version']:
        raise HTTPException(401,'로그인해 주세요.')
    return account


def public(account):
    return {k:account[k] for k in ('id','username','session_id')}


def register(name,password,session_id):
    name=username(name);limit('register',session_id,5)
    try:
        with store.payment_lease('member-browser:'+digest(session_id)), store.payment_lease('member-register:'+name), ExitStack() as ownership:
            if store.get_json('member-name:'+name):raise HTTPException(409,'다른 아이디를 선택해 주세요.')
            # Never claim another account's browser session, even after logout.
            presented=(session_id or '').strip()
            adoptable=bool(SESSION.fullmatch(presented)) and not owner(presented)
            # ★ 못 쓰는 난수면 새것으로 갈았습니다 — 그 자리에 **치른 값이
            #   있어도** 그랬습니다. 빈 계정을 조용히 만드는 대신 멈춥니다.
            #   멈추면 손님은 주문번호로 되찾는 길(/v1/pay/restore)이 있소.
            if not adoptable and session_orders(presented):
                raise HTTPException(409,'이미 회원에게 연결된 구매입니다. 기존 계정으로 로그인해 주세요.')
            sid=presented if adoptable else str(uuid.uuid4())
            order_ids=session_orders(sid)
            for oid in order_ids:ownership.enter_context(store.payment_lease('member-order:'+oid))
            if any(bound_member(oid) for oid in order_ids):
                raise HTTPException(409,'이미 회원에게 연결된 구매입니다. 기존 계정으로 로그인해 주세요.')
            recovery=secrets.token_urlsafe(24)
            account={'id':uuid.uuid4().hex,'username':name,'password':password_hash(password),
                     'recovery':digest(recovery),'session_id':sid,'version':1,'created_at':time.time()}
            store.set_json('member:'+account['id'],account)
            store.set_json('member-name:'+name,account['id'])
            store.set_json('member-owner:'+digest(sid),account['id'])
            # Keep ownership separate: linking an account must never overwrite a
            # concurrent payment confirmation, opened_at update, or refund.
            for oid in order_ids:store.set_json('member-order:'+oid,account['id'])
            return account,issue(account),recovery
    except store.LeaseBusy:raise HTTPException(409,'가입을 처리 중입니다. 잠시 후 다시 확인해 주세요.')


def login(name,password,session_id=''):
    name=username(name);limit('login',name)
    key=store.get_json('member-name:'+name)
    account=store.get_json('member:'+key) if key else None
    # Equal work for unknown IDs; credentials are never logged or returned.
    encoded=account['password'] if account else _DUMMY_HASH
    if not password_matches(password,encoded) or not account:
        raise HTTPException(401,'아이디 또는 비밀번호를 확인해 주세요.')
    # 값을 먼저 치르고 들어온 손님. 자물쇠를 연 뒤에만 잇습니다.
    attach(account,session_id)
    return account,issue(account)


def recover(name,code,password,session_id=''):
    name=username(name);limit('recover',name,5)
    key=store.get_json('member-name:'+name)
    account=store.get_json('member:'+key) if key else None
    if not account or not hmac.compare_digest(account['recovery'],digest(code.strip())):
        raise HTTPException(401,'아이디와 복구 코드를 확인해 주세요.')
    try:
        with store.payment_lease('member:'+account['id']):
            latest=store.get_json('member:'+account['id'])
            if not hmac.compare_digest(latest['recovery'],digest(code.strip())):raise HTTPException(401,'복구 코드를 확인해 주세요.')
            recovery=secrets.token_urlsafe(24)
            latest.update(password=password_hash(password),recovery=digest(recovery),version=latest['version']+1)
            store.set_json('member:'+latest['id'],latest)
    except store.LeaseBusy:raise HTTPException(409,'계정 변경 중입니다. 잠시 후 다시 시도해 주세요.')
    # 계정 자물쇠를 놓고 나서 잇습니다 — 잠금 둘을 겹쳐 쥐지 않습니다.
    attach(latest,session_id)
    return latest,issue(latest),recovery
