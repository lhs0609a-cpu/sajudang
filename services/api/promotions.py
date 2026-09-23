"""Fixed campaign dates. Catalog prices and content entitlement never change."""
import os
from datetime import datetime, timezone


def current(now=None):
    now = now or datetime.now(timezone.utc)
    try:
        start = datetime.fromisoformat(os.environ['SALE_START'])
        end = datetime.fromisoformat(os.environ['SALE_END'])
        percent = int(os.environ['SALE_PERCENT'])
        if start.tzinfo is None or end.tzinfo is None or not 1 <= percent <= 50 or not start <= now < end:
            return None
    except (KeyError, ValueError, TypeError):
        return None
    return {'percent':percent, 'ends_at':end.isoformat(), 'server_now':now.isoformat()}


def quote(base, tier):
    campaign = current() if tier in ('one', 'all') else None
    amount = base * (100 - campaign['percent']) // 100 if campaign else base
    return {'price':amount, 'base_price':base, 'promotion':campaign}
