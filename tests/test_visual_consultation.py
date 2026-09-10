"""End-to-end contracts for picture selection, attribution and correction."""
from pathlib import Path

import pytest

from engine import extras, guard, lens, visual
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report


@pytest.fixture(scope="module")
def features():
    return build_features(build_chart(1993, 5, 15, None, None, "F", hour_known=False))


def test_every_character_has_a_relevant_picture_question():
    special = {"myeonsang": "face", "yakcho": "body", "monghwa": "image", "paeseon": "cards"}
    for character in lens.all_lenses():
        id = character["id"]
        catalog = extras.choices(id)
        if id in special:
            assert lens.required_input(id) == special[id]
        else:
            assert catalog["scene"]["title"]
            assert len(catalog["scene"]["options"]) >= 3
        # Unselected reading content must stay on the server.
        assert "reading" not in repr(catalog)


def test_every_advertised_picture_is_present():
    root = Path(__file__).resolve().parents[1] / "apps/web/public"
    def check(value):
        if isinstance(value, dict):
            if "image" in value and isinstance(value["image"], str):
                asset = root / value["image"].lstrip("/")
                assert asset.is_file(), asset
                assert asset.stat().st_size > 100
            for v in value.values():
                check(v)
        elif isinstance(value, list):
            for v in value:
                check(v)
    for character in lens.all_lenses():
        check(extras.choices(character["id"]))
    assert (root / "choices/card-back.webp").is_file()


def test_face_selection_changes_the_reading_and_is_editable(features):
    first = {"shape": "round", "features": {"eyes": "up", "nose": "wide"}}
    second = {"shape": "square", "features": {"eyes": "down"}}
    reports = [build_report(features, "cid", "myeonsang", "free", "love", None, {"face": p})
               for p in (first, second)]
    cuts = [next(c for c in r["cuts"] if c["id"] == "face") for r in reports]
    assert all(r["needs_input"] is None for r in reports)
    assert cuts[0]["html"] != cuts[1]["html"]
    assert "둥근형" in cuts[0]["html"] and "네모형" in cuts[1]["html"]
    assert "넓은 콧방울" not in cuts[1]["html"]  # no stale previous answer
    for c in cuts:
        assert "창작 관상" in c["html"]
        assert guard.check(c["html"])[0]


def test_face_features_work_without_a_matching_whole_face(features):
    c = visual.face_cut(features, {"shape": "unknown", "features": {"jaw": "round"}})
    assert "둥근 턱" in c["html"]
    with pytest.raises(visual.VisualInputError):
        visual.face_cut(features, {"shape": "unknown", "features": {}})


@pytest.mark.parametrize("payload", [
    {"shape": "<script>", "features": {}},
    {"shape": "round", "features": []},
    {"shape": "round", "features": {"eyes": "wrong"}},
    {"shape": "round", "features": {"secret": "open"}},
    [],
])
def test_malformed_face_input_is_a_recoverable_report_error(features, payload):
    # Non-empty malformed payloads go through the normal report validation path.
    if payload == []:
        with pytest.raises(visual.VisualInputError):
            visual.face_cut(features, payload)
        return
    r = build_report(features, "cid", "myeonsang", "free", "love", None, {"face": payload})
    assert r["extra_error"]
    assert not any(c["id"] == "face" for c in r["cuts"])


def test_body_summary_reports_the_selected_regions_without_diagnosis(features):
    payload = dict(regions=["neck", "back"], state="pain", duration="days", impact="disrupt")
    r = build_report(features, "cid", "yakcho", "free", "health", None, {"body": payload})
    c = next(c for c in r["cuts"] if c["id"] == "body")
    assert "목 · 등" in c["html"] and "며칠 전부터" in c["html"]
    assert "의료진" in c["html"] and "직접 알려주신" in c["html"]
    assert r["needs_input"] is None
    assert guard.check(c["html"])[0]
    urgent = visual.body_cut(features, {**payload, "impact": "severe"})
    assert "119" in urgent["html"]
    assert "원인은 여기서" not in urgent["html"]  # skip ordinary reflection for severe input


@pytest.mark.parametrize("regions", [[], ["neck"] * 2, ["neck", "back", "arm", "leg"], ["whole", "neck"], ["unknown"], [{}]])
def test_body_rejects_unknown_duplicate_or_excess_regions(features, regions):
    with pytest.raises(visual.VisualInputError):
        visual.body_cut(features, dict(regions=regions, state="pain", duration="today", impact="mild"))


def test_all_scene_choices_produce_distinct_guarded_readings():
    for lens_id, (_, options) in visual.SCENES.items():
        results = [visual.scene_cut(lens_id, dict(lens_id=lens_id, pick=o["id"])) for o in options]
        assert len({c["html"] for c in results}) == len(options)
        assert all(guard.check(c["html"])[0] for c in results)


def test_scene_cannot_leak_between_characters(features):
    payload = {"lens_id": "hunjang", "pick": "tired"}
    good = build_report(features, "cid", "hunjang", "free", "work", None, {"scene": payload})
    assert any(c["id"] == "scene" for c in good["cuts"])
    bad = build_report(features, "cid", "haengsu", "free", "money", None, {"scene": payload})
    assert bad["extra_error"] and not any(c["id"] == "scene" for c in bad["cuts"])


def test_all_38_face_options_have_guarded_readings(features):
    for shape in visual.FACE:
        assert guard.check(visual.face_cut(features, dict(shape=shape["id"]))["html"])[0]
    for group, (_, options) in visual.FEATURES.items():
        for id, *_ in options:
            assert guard.check(visual.face_cut(features, dict(shape="unknown", features={group: id}))["html"])[0]
