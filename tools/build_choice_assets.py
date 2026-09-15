"""Encode generated choice PNGs and draw exact, editable comparison diagrams.

Raster sources come from the built-in image generator; this tool does not paint,
crop or synthesize replacement raster art. SVGs encode controlled feature changes.
"""
from pathlib import Path
import json

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "apps/web/public/choices"
MASTER = ROOT / "assets/master/choices"


def svg(body, view="0 0 320 240"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}">'
            '<rect width="100%" height="100%" fill="#eee4d3"/>'
            '<g fill="none" stroke="#655143" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
            + body + '</g></svg>')


def path(d, **attrs):
    return '<path d="' + d + '" ' + ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items()) + '/>'


def eyes(kind):
    half = {"long": 49, "round": 26}.get(kind, 36)
    height = {"open": 25, "narrow": 8, "long": 15, "round": 29, "up": 16, "down": 16}[kind]
    def eye(cx, tilt):
        d = f'M{cx-half} 126 Q{cx} {126-height*2} {cx+half} 126 Q{cx} {126+height*1.4} {cx-half} 126Z'
        return (f'<g transform="rotate({tilt} {cx} 126)">' + path(d, fill="#fffaf0") +
                f'<ellipse cx="{cx}" cy="123" rx="{min(13,height)}" ry="{min(15,height)}" fill="#97765a"/>' +
                f'<circle cx="{cx}" cy="123" r="5" fill="#453d36" stroke="none"/></g>')
    tilt = {"up": 12, "down": -12}.get(kind, 0)
    return path('M145 110 Q160 96 175 110 M157 122 L153 151 Q160 157 167 151', opacity=".2") + eye(87, tilt) + eye(233, -tilt)


def brows(kind):
    widths = {"straight": 33, "arched": 33, "thick": 33, "thin": 33, "long": 49, "short": 20}
    thickness = {"thick": 13, "thin": 2}.get(kind, 6)
    result = path('M52 150 Q87 130 122 150 M198 150 Q233 130 268 150', opacity=".2")
    for cx in [87, 233]:
        w = widths[kind]
        d = f'M{cx-w} 107 Q{cx} {66 if kind=="arched" else 104} {cx+w} 107'
        result += path(d, stroke_width=str(thickness), stroke="#594233")
    return result


def nose(kind):
    if kind in ("high", "low"):
        ridge = 218 if kind == "high" else 178
        tip = 232 if kind == "high" else 198
        return (path('M143 25 Q164 42 169 76 M164 163 Q180 180 168 207', opacity=".25") +
                path(f'M169 76 Q{ridge-26} 89 {ridge} 123 Q{tip+8} 143 {tip} 149 L181 157 Q169 164 163 155', fill="#dcc7ad") +
                path('M149 82l14 3', opacity=".35"))
    if kind == "round":
        return (path('M144 44 Q139 100 128 140 Q120 162 141 166 M176 44 Q181 100 192 140 Q200 162 179 166', fill="#dfcbb2") +
                '<ellipse cx="160" cy="155" rx="23" ry="22" fill="#dfcbb2"/>' +
                path('M131 159q7 -6 12 0 M177 159q7 -6 12 0') +
                path('M83 52q15 -8 29 0 M208 52q15 -8 29 0', opacity=".2"))
    bottom = 194 if kind == "long" else 164
    width = {"wide": 56, "narrow": 22, "round": 36, "long": 31}[kind]
    bulb = 30 if kind == "round" else 17
    return (path(f'M144 44 Q139 100 {160-width} {bottom-17} Q{155-width} {bottom+5} 149 {bottom} '
                 f'Q160 {bottom+bulb} 171 {bottom} Q{165+width} {bottom+5} {160+width} {bottom-17} Q181 100 176 44', fill="#dfcbb2") +
            path(f'M{160-width+8} {bottom-4}q8 -8 15 0 M{160+width-23} {bottom-4}q8 -8 15 0') +
            path('M83 52q15 -8 29 0 M208 52q15 -8 29 0', opacity=".2"))


def mouth(kind):
    width = {"wide": 86, "narrow": 40}.get(kind, 65)
    thick = {"full": 34, "thin": 7}.get(kind, 19)
    corners = {"up": 101, "down": 143}.get(kind, 123)
    left, right = 160-width, 160+width
    return (path('M146 64q14 7 28 0 M111 190q49 18 98 0', opacity=".2") +
            path(f'M{left} {corners} Q140 {123-thick} 160 {123-thick*.55} Q180 {123-thick} {right} {corners} '
                 f'Q160 {123+thick*1.9} {left} {corners}Z', fill="#c89181", stroke="#936351") +
            path(f'M{left} {corners} Q160 129 {right} {corners}', stroke="#775346"))


def jaw(kind):
    shapes = {
        "round": 'M83 30 L87 109 Q92 188 160 195 Q228 188 233 109 L237 30',
        "square": 'M83 30 L83 146 Q83 177 111 185 L209 185 Q237 177 237 146 L237 30',
        "pointed": 'M83 30 L91 109 Q110 156 160 207 Q210 156 229 109 L237 30',
        "wide": 'M66 30 L58 136 Q69 184 105 190 L215 190 Q251 184 262 136 L254 30',
        "narrow": 'M93 30 L108 119 Q133 188 160 195 Q187 188 212 119 L227 30',
        "long": 'M83 18 L96 109 Q118 215 160 224 Q202 215 224 109 L237 18',
    }
    return path(shapes[kind], fill="#dfcbb2") + path('M143 84q17 8 34 0 M129 113q31 8 62 0', opacity=".4")


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for source in MASTER.glob("*.png"):
        target = PUBLIC / (source.stem + ".webp")
        if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
            continue
        with Image.open(source) as im:
            im.thumbnail((640, 640), Image.Resampling.LANCZOS)
            im.convert("RGB").save(target, "WEBP", quality=85, method=6)
    variants = {
        "eyes": (eyes, ["open", "narrow", "long", "round", "up", "down"]),
        "brows": (brows, ["straight", "arched", "thick", "thin", "long", "short"]),
        "nose": (nose, ["high", "low", "wide", "narrow", "round", "long"]),
        "mouth": (mouth, ["full", "thin", "wide", "narrow", "up", "down"]),
        "jaw": (jaw, ["round", "square", "pointed", "wide", "narrow", "long"]),
    }
    for group, (draw, ids) in variants.items():
        for id in ids:
            (PUBLIC / f"{group}-{id}.svg").write_text(svg(draw(id)), encoding="utf-8")
    silhouette = ('<ellipse cx="160" cy="42" rx="25" ry="31" fill="#d8c6ac"/>' +
                  path('M149 72 L171 72 L175 89 L208 103 L229 196 L214 201 L191 135 L192 216 '
                       'L196 298 L187 391 L166 391 L160 273 L154 391 L133 391 L124 298 L128 216 '
                       'L129 135 L106 201 L91 196 L112 103 L145 89Z', fill="#d8c6ac"))
    for view in ("front", "back"):
        detail = path('M149 42h4m14 0h4m-18 15q7 4 14 0', stroke_width="2") if view == "front" else path('M160 105v101', opacity=".3")
        (PUBLIC / f"body-{view}.svg").write_text(svg(silhouette + detail, "0 0 320 420"), encoding="utf-8")
    files = list(PUBLIC.glob("*"))
    print(json.dumps({"raster": len(list(PUBLIC.glob('*.webp'))), "svg": len(list(PUBLIC.glob('*.svg'))),
                      "bytes": sum(x.stat().st_size for x in files)}))


if __name__ == "__main__":
    main()
