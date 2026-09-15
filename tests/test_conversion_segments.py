from datetime import datetime, timedelta, timezone
import analytics


def journey(sid, days, approved=True):
    at = datetime.now(timezone.utc) - timedelta(days=days)
    rows = [{"sid":sid,"at":at.isoformat(),"name":"flow_started","screen":"a1","n":2},
            {"sid":sid,"at":(at+timedelta(seconds=1)).isoformat(),"name":"entry_context","screen":"a1","n":0,"stage":1,"yes":0}]
    for i, (screen, _) in enumerate(analytics.FUNNEL[1:], 2):
        if screen == "d3" and not approved:
            continue
        rows.append({"sid":sid,"at":(at+timedelta(seconds=i)).isoformat(),"screen":screen,
                     "name":"payment_approved" if screen == "d3" else "chart_completed" if screen == "a6" else "screen"})
    return rows


def test_segment_conversion_excludes_unfinished_observation(monkeypatch):
    rows = journey("a"*32,8) + journey("b"*32,8,False) + journey("c"*32,1)
    monkeypatch.setattr(analytics,"_rows",lambda:rows)
    result=analytics.funnel()
    mobile=next(row for row in result["segments"] if row["label"]=="모바일")
    assert mobile == {"dimension":"n","label":"모바일","visitors":3,"mature":2,"buyers":1,"conversion":50.0}
    assert result["immature_sessions"] == 1


def test_missing_context_is_not_invented_and_no_referrer_is_stored(monkeypatch):
    rows=[row for row in journey("d"*32,8) if row["name"]!="entry_context"]
    monkeypatch.setattr(analytics,"_rows",lambda:rows)
    result=analytics.funnel()
    assert result["context_missing"]==1
    assert all(row["conversion"] is None for row in result["segments"])
    cleaned=analytics._clean({"name":"entry_context","screen":"a1","sid":"e"*32,"n":0,"stage":1,"yes":0,"referrer":"https://private.invalid/name"})
    assert "referrer" not in cleaned
