"""User-facing calendar dates always use Korea time, independent of host TZ."""
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

def today():
    return datetime.now(KST).date()
