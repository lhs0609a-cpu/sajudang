"""
스무 사람의 얼굴 — 초상 발주서.

    python tools/char_sheet.py                한 장으로 뽑는다
    python tools/char_sheet.py pungun         한 사람만
    python tools/char_sheet.py --write 캐릭터_초상_발주서.txt

★ 왜 이 도구가 생겼나

  발주서(docs/10 §7)는 `/char/{id}/bust.png` 768×1024 를 요구하는데,
  **무엇을 그릴지는 아무 데도 없었습니다.** 신살 인물 13명은 프롬프트가
  있고 장면 24개도 있는데, 정작 이 집이 파는 **스무 사람**만 없었습니다.

  그래서 화면에 얼굴이 없었고, 손님은 일곱 화면을 지나도록 그 사람을
  못 봤습니다.

★ 지어내지 않습니다

  각 사람의 것은 이미 정해져 있습니다 — 이름·한자·유파·원형(archetype)·
  성별·색·전문 분야. 여기서는 그걸 **그림 지시로 옮길 뿐**입니다.
  설정집에 없는 성격을 새로 붙이면 글과 그림이 갈립니다.

★ 화풍은 신살 인물과 같습니다

  같은 집의 사람들입니다. 화풍이 갈리면 스무 명이 한 집 식구로 안
  보입니다. 머리말은 asset-prompts.json 의 신살 인물 것을 그대로 씁니다.

★ 배경은 흰색입니다

  초상은 투명 PNG 로 잘라 써야 합니다(대사 옆·진열대·첫 대면에서 각각
  다른 바탕 위에 얹힙니다). 배경이 들어가면 잘라낼 수 없습니다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LENSES = ROOT / "seed" / "lenses.json"
PROMPTS = ROOT / "apps" / "web" / "public" / "asset-prompts.json"

# ── 원형(archetype) → 얼굴·머리·옷 ─────────────────────────
#
#   설정집이 정한 원형을 그림 말로 옮긴 것입니다. 여기 없는 성격을
#   새로 붙이지 않습니다 — 글과 그림이 갈립니다.
LOOK = {
    "차가운 미남": ("a composed young nobleman with cool distant eyes and a "
                "straight mouth, black hair tied high with a jade pin, deep "
                "indigo scholar's robe with silver trim"),
    "백발 미청년": ("a serene young monk with long silver-white hair loose over "
                "one shoulder, pale grey-green eyes, plain undyed hemp robe, "
                "a single wooden bead bracelet"),
    "무뚝뚝한 장년": ("a broad-shouldered man in his forties, weathered face, "
                 "thick brows, unsmiling, greying topknot, worn dark blue "
                 "hanbok with rolled sleeves"),
    "야성적인": ("a rugged man with an unkempt topknot, a thin old scar across "
             "one brow, open collar, dark hemp robe"),
    "지적인 안경": ("a slender young man wearing round brass-rimmed spectacles, "
                "neat side-parted hair, a fine chain across his chest, "
                "pale grey robe with many small pockets"),
    "차가운 분석가": ("a woman with an unreadable calm face, hair pulled back "
                 "severely, silver hairpin, high-collared dark hanbok, "
                 "eyes catching a faint cold light"),
    "위험한 매력": ("a striking woman with a knowing half-smile, loose crimson "
                "hanbok slipping off one shoulder, dark red lips, a single "
                "long earring, hair falling free"),
    "서늘한 신비": ("a pale otherworldly young woman with long unbound black "
                "hair, distant unfocused gaze, layered gauzy pale-lilac "
                "hanbok that seems to drift"),
    "이국적 미남": ("a young man of foreign features — deeper set eyes, higher "
                "nose bridge, sun-darkened skin — dark travelling coat over "
                "hanbok, small brass astrolabe hanging at his belt"),
    "능글맞은 미남": ("a handsome man with a lazy amused grin, one brow raised, "
                 "hair carelessly tied, loose plum robe open at the throat, "
                 "a card held between two fingers"),
    "날카로운 미남": ("a sharp-featured man with narrow observing eyes that seem "
                 "to measure the viewer, thin lips, dark high-collared robe, "
                 "hands folded"),
    "인연을 매는 사람": ("a gentle woman with a soft knowing smile, moonlit pale "
                   "hanbok, a length of red thread wound loosely around her "
                   "fingers, hair in a low braid"),
    "압도적인 언니": ("a magnificent woman in her thirties, bold direct gaze, "
                 "richly embroidered deep-red hanbok, gold hairpin, arms "
                 "crossed, utterly unbothered"),
    "상처 있는 미남": ("a quiet young man with sad downcast eyes, faint shadows "
                  "beneath them, dark muted robe worn a little loose, hair "
                  "falling over one eye"),
    "편들지 않는 판관": ("a stern androgynous figure with a level unblinking gaze, "
                   "black official's robe, hair severely bound, holding a "
                   "closed brush case like a verdict"),
    "우아한 귀공자": ("an elegant young merchant prince, fine silk robe in muted "
                 "gold, immaculate topknot, an abacus-like ledger tucked "
                 "under one arm, faint polite smile"),
    "엄격한 연상": ("a stern older scholar with grey at the temples, small "
                "reading glasses low on the nose, dark scholar's robe, a "
                "bamboo cane rod held upright"),
    "다정한 연상": ("a warm woman in her thirties with kind tired eyes, sleeves "
                "tied back for work, soft moss-green hanbok, dried herbs "
                "tucked at her sash"),
    "무심한 미남": ("a beautiful man with a flat uninterested expression, looking "
                "slightly past the viewer, pale blue-grey robe, a small sun "
                "dial hanging from his belt"),
    "원조 걸크러쉬": ("a formidable old woman with a lined face and fierce clear "
                 "eyes, white hair in a tight knot, patched dark hanbok, a "
                 "long smoking pipe resting on her shoulder"),
    "청량한 소년": ("a bright clear-eyed boy of about fourteen, tousled hair, an "
                "open easy smile, simple pale-blue hanbok, sleeves too long "
                "for his arms"),
}

# ★ 정면 초상입니다 (2026-09-03).
#
#   전에는 「slight three-quarter angle」 이라 비스듬히 나왔습니다. 이
#   초상이 가장 크게 쓰이는 자리는 **대사 옆 66×88 조각**인데, 그 크기
#   에서 얼굴을 살짝 돌리면 한쪽 눈이 묻히고 시선이 손님을 비껴갑니다.
#   마주 앉은 자리라 눈이 마주쳐야 합니다.
#
#   금지도 같이 적습니다 — 생성기는 「정면」 한 마디로는 자꾸 3/4 로
#   돌아갑니다. no head turn · no profile 까지 박아야 섭니다.
# 초상 프롬프트를 마지막으로 고친 날 (정면으로 바꾼 날)
REVISED = "2026-09-03"

TAIL = ("Bust-up from the chest up, centered, subject occupying about 72% of\n"
        "frame height. FRONT-FACING PORTRAIT — head and shoulders squared to\n"
        "the camera, both eyes fully visible and level, gaze straight at the\n"
        "viewer. Symmetrical. No head turn, no profile, no three-quarter angle.\n"
        "\n"
        "Flat solid pure white (#FFFFFF) background — no gradient, no scenery,\n"
        "no cast shadow, no vignette. No text, letters, numbers, logos or\n"
        "watermarks. Aspect ratio 3:4. High detail.")

# ── 표정 두 벌 ─────────────────────────────────────────────
#
#   얼굴 한 장으로 다 하면 **짚는 순간과 누그러뜨리는 순간이 같은
#   얼굴**이 됩니다. 훅 0단은 아픈 데를 찌르는 자리이고 만류 문구는
#   달래는 자리인데, 같은 표정이면 둘 다 힘을 잃습니다.
#
#   문장 뱅크를 세어 셋으로 정했습니다 —
#     짚는 말 26 · 누그러뜨리는 말 19 · 아니라고 하는 말 7
#   「아니라고 하는 말」은 짚는 얼굴에 접습니다. 일곱 마디를 위해
#   스무 명분을 더 그리는 것은 값이 안 맞습니다.
#
#   ★ 같은 사람이라야 합니다. 머리·옷·빛은 그대로 두고 **눈과 입만**
#     바꿉니다. 얼굴이 달라지면 다른 사람이 됩니다.
MOOD_HEAD = ("Same character, same hair, same clothing, same lighting, same\n"
             "front-facing pose — only the expression changes.")

# ★ 모션의 잠금 — 사람마다 다른 것은 **몸짓**이고, 이건 스무 명이
#   같습니다. 초상은 얼굴로 잘라 쓰기 때문에(눈높이 37% 를 잡고 2.6배)
#   머리가 제자리를 뜨면 크롭이 깨집니다.
MOTION_HOLD = (
    "The head stays exactly where it is and does not turn — the app crops\n"
    "this clip to the face, so any drift breaks the crop. No new pose, no\n"
    "expression change. Only what is described above moves. Seamlessly\n"
    "loopable: the last frame must match the first exactly.")

GREET_HOLD = (
    "The head stays centred and front-facing throughout — this plays once,\n"
    "at the first meeting, and the face is cropped the same way. It ends on\n"
    "the same still portrait it began with, so the greeting can hand over to\n"
    "the looping clip without a jump.")


# ── 사람마다 다른 연출 ─────────────────────────────────────
#
# ★ 스무 명이 **한 벌**을 나눠 쓰고 있었습니다 (2026-09-06).
#
#   모션은 「눈 한 번 깜빡, 머리카락이 흔들림」 한 문장이었고 그것을
#   스무 명이 그대로 썼습니다. 표정 둘도 한 벌이었고, 게다가 「He」로
#   쓰여 있어 **여자 일곱**에게도 그대로 나갔습니다. 열넷은 어른인데
#   청동자는 열넷짜리 아이입니다.
#
#   이 집이 파는 것은 「같은 사주를 스무 사람이 저마다 다르게 읽는
#   것」입니다. 그런데 스무 사람이 다 똑같이 눈을 깜빡이면, 손님이
#   보는 것은 스무 사람이 아니라 옷을 갈아입은 한 사람입니다.
#
# ★ 지어내지 않습니다 — LOOK 이 이미 그 사람에게 쥐여 준 것으로 합니다.
#   담뱃대·패·붉은 실·염주·회초리·해시계·장부·아스트롤라베. 없는 소품을
#   새로 붙이면 그림과 발주서가 갈립니다.
#
#   {he}/{his}/{him} 은 lenses.json 의 sex 가 채웁니다. 손으로 적으면
#   한 사람은 반드시 틀립니다.
STAGE = {
    "pungun": {   # 차가운 미남 · 왜 하필 지금 · 옥비녀
        "beat": "The jade pin in the high-tied hair catches the light once as "
                "it passes. A single slow blink. The silver trim at the "
                "collar breathes with a shallow breath. The cool gaze never "
                "leaves the viewer.",
        "cut": "The eyes narrow a fraction and hold, pupils sharp. The mouth "
               "stays a straight line. One brow a hair lower than the other. "
               "{he} has said the true thing first and is waiting.",
        "soft": "The gaze drops a few degrees and the cold goes out of it. "
                "The chin tucks slightly. No smile — {he} is simply not "
                "pressing any further.",
        "greet": "{his} eyes lift to the viewer as if just noticing them, and "
                 "{he} inclines {his} head a few degrees — the smallest "
                 "possible bow — then straightens and holds the gaze.",
    },
    "baegun": {   # 백발 미청년 · 모자란 것 채우기 · 나무 염주
        "beat": "The eyes close and open again very slowly, once. A single "
                "strand of the silver-white hair lifts and settles. One "
                "wooden bead turns a half-turn on the wrist.",
        "cut": "The eyes open fully and stay open, unblinking, the pale "
               "grey-green iris very clear. The mouth is level. {he} is not "
               "accusing — {he} has simply stopped softening it.",
        "soft": "The eyelids lower to half and the outer corners ease. The "
                "hand around the bead bracelet loosens. A breath goes out.",
        "greet": "The lowered eyes open, find the viewer, and the head bows "
                 "once slowly and comes back up. The bead bracelet swings a "
                 "little and stills.",
    },
    "cheongam": {   # 무뚝뚝한 장년 · 타고난 그릇 · 걷어붙인 소매
        "beat": "One deep breath — the broad shoulders rise a little and come "
                "down. The creases in the rolled-up sleeve shift with it. The "
                "thick brows do not move. One slow blink at the end.",
        "cut": "The brows come down a fraction and the jaw sets. The eyes go "
               "flat and stay on the viewer. {he} is not going to repeat it.",
        "soft": "The set jaw loosens. The eyes stay level but the weight goes "
                "out of the brow. Something close to, but not, kindness.",
        "greet": "{he} looks up from whatever was in {his} hands, sees the "
                 "viewer, and gives one short nod. The shoulders settle.",
    },
    "sigye": {   # 지적인 안경 · 때와 시기 · 가슴의 가는 사슬
        "beat": "The fine chain across the chest swings in a small even "
                "rhythm, like something counting. Light crosses one lens of "
                "the brass-rimmed spectacles and passes. One blink, on the "
                "beat.",
        "cut": "The chin drops a fraction so the eyes come over the top of "
               "the spectacles and fix on the viewer. The mouth closes flat. "
               "{he} has just put a date on it.",
        "soft": "{he} pushes the spectacles back up and the eyes behind them "
                "soften. The counting chain slows. The mouth eases.",
        "greet": "{he} glances down at the chain, then up at the viewer, and "
                 "the eyebrows lift in mild recognition — right on time.",
    },
    "eunbyeol": {   # 차가운 분석가 · 성향과 어긋난 자리 · 은비녀
        "beat": "A cold light travels along the silver hairpin and goes out. "
                "The high collar stays perfectly still. {he} does not blink "
                "for a long time, then blinks once, late.",
        "cut": "The eyes stop moving entirely and rest on the viewer. Nothing "
               "in the face gives anything away. {he} has found the place "
               "where the answers do not agree.",
        "soft": "The gaze slides a few degrees off the viewer — deliberately, "
                "giving them room. The severe line of the mouth loosens by "
                "almost nothing.",
        "greet": "The eyes come up from somewhere off-frame and settle on the "
                 "viewer, unhurried. The head tilts a degree, measuring, then "
                 "levels.",
    },
    "jeokhyeol": {   # 위험한 매력 · 끌림과 욕망 · 긴 귀걸이
        "beat": "The single long earring turns slowly through a half-circle "
                "and swings back. The loose crimson collar shifts on the bare "
                "shoulder. The half-smile deepens a little and returns.",
        "cut": "The half-smile goes out completely. The eyes stay exactly "
               "where they were, and that is worse. {he} has named the thing "
               "the viewer wants.",
        "soft": "The smile comes back small and real. The eyes warm and the "
                "head tips toward the viewer. The teasing stops.",
        "greet": "{he} looks up through {his} lashes, the half-smile arriving "
                 "before the gaze does, and the long earring swings once.",
    },
    "monghwa": {   # 서늘한 신비 · 신살과 자리 · 겹겹의 연보라
        "beat": "The layered pale-lilac gauze and the unbound hair drift as "
                "if underwater, with no wind in the room. The unfocused gaze "
                "does not settle. A blink that is almost too slow.",
        "cut": "The wandering eyes snap into focus on the viewer, all at "
               "once, and stay. The drifting cloth goes still. {he} is "
               "looking straight at the thing standing behind the question.",
        "soft": "The focus dissolves again and the gaze goes soft and "
                "far-off. The mouth curves very slightly. The cloth begins to "
                "drift once more.",
        "greet": "The distant eyes drift across the frame and find the viewer "
                 "by accident, and stay — as if {he} had been expecting them "
                 "without knowing when.",
    },
    "seoyeok": {   # 이국적 미남 · 고을과 별 · 놋 아스트롤라베
        "beat": "The brass astrolabe at the belt turns a slow half-turn on "
                "its ring and a thin line of light runs around its rim. The "
                "travelling coat's collar lifts once. One blink.",
        "cut": "The deep-set eyes fix and the head goes very still, the way "
               "someone holds still to take a sighting. {he} has placed the "
               "viewer on a map they did not know existed.",
        "soft": "The shoulders drop out of the travelling posture. The eyes "
                "crease at the corners — a long way from home and glad of "
                "the company.",
        "greet": "{he} looks up from the astrolabe, and the sun-darkened face "
                 "opens into recognition. One hand steadies the instrument as "
                 "{he} turns {his} attention over.",
    },
    "paeseon": {   # 능글맞은 미남 · 패로 보는 빈자리 · 손가락 사이의 패
        "beat": "The card held between two fingers flips over once and comes "
                "back, face hidden both times. The raised brow stays raised. "
                "The plum robe's open collar shifts.",
        "cut": "The lazy grin drops off in one frame. The card stops moving. "
               "The eyes, suddenly not amused at all, hold the viewer. {he} "
               "has turned up the one {he} was not joking about.",
        "soft": "The grin comes back crooked and easy, and {he} tucks the "
                "card away out of frame. The raised brow lowers. Nothing to "
                "see here.",
        "greet": "{he} fans the card into view between two fingers, gives the "
                 "viewer a lazy sideways look, and the grin arrives.",
    },
    "myeonsang": {   # 날카로운 미남 · 기색과 자리 · 맞잡은 손
        "beat": "The narrow eyes travel a short way across the viewer's face "
                "— left, right, back to centre — reading it. The folded hands "
                "do not move at all. One blink, precise.",
        "cut": "The reading stops. The eyes lock centre and the thin lips "
               "press. {he} has seen the thing the viewer arranges {his} face "
               "to hide.",
        "soft": "The eyes let go and drop politely to the viewer's collar "
                "instead of {his} face. The hands unfold slightly. {he} "
                "gives the face back.",
        "greet": "The narrow eyes come up and take the viewer in with one "
                 "quick sweep, then settle and hold. The folded hands tighten "
                 "once in greeting.",
    },
    "wolha": {   # 인연을 매는 사람 · 인연 맺기 · 붉은 실
        "beat": "The red thread wound around the fingers loosens by one turn "
                "and winds back. The moonlit pale hanbok glows a little "
                "brighter and dims. The knowing smile holds. One soft blink.",
        "cut": "The smile stays but stops being kind. The thread pulls taut "
               "between the fingers. The eyes hold the viewer without "
               "blinking — {he} can see both ends of it.",
        "soft": "The thread goes slack. The eyes lower and warm, and the "
                "smile becomes an ordinary one. {he} lets the viewer keep the "
                "hope.",
        "greet": "{he} lifts {his} hands into view, the red thread already "
                 "wound around them, and smiles as if the viewer were "
                 "expected.",
    },
    "hongmae": {   # 압도적인 언니 · 혼인과 중매 · 팔짱 · 금비녀
        "beat": "One breath moves the folded arms. Light runs along the gold "
                "hairpin. The bold gaze does not waver and does not blink "
                "until the very end, once.",
        "cut": "The chin comes up a fraction. The eyes go hard and stay on "
               "the viewer. {he} has said out loud what everyone else was too "
               "polite to.",
        "soft": "The arms loosen out of the fold. The mouth curves — big, "
                "unembarrassed warmth. {he} is on the viewer's side and "
                "always was.",
        "greet": "{he} looks the viewer over head to foot in one sweep, "
                 "decides in {his} favour, and the arms come uncrossed.",
    },
    "yeondam": {   # 상처 있는 미남 · 재회 · 한쪽 눈을 덮은 머리
        "beat": "The hair falling over one eye stirs and settles. The visible "
                "eye lowers, then lifts again. The muted robe hangs loose at "
                "the shoulder. Very little else moves.",
        "cut": "The downcast eye comes up and stays up, level with the "
               "viewer for once. The sadness is still there but it is not "
               "looking away. {he} has said the part about waiting.",
        "soft": "The eye drops again and the mouth softens. The hair falls "
                "back across it. {he} is giving the viewer somewhere to look "
                "that is not {him}.",
        "greet": "The lowered head comes up slowly, the hair sliding off the "
                 "covered eye, and both eyes find the viewer before the hair "
                 "falls back.",
    },
    "hwagyeong": {   # 편들지 않는 판관 · 다툼과 시비 · 닫힌 붓집
        "beat": "Nothing moves for a long moment. Then the hand around the "
                "closed brush case tightens once and lets go. The level gaze "
                "does not blink at all.",
        "cut": "The eyes stay open and absolutely still. The brush case comes "
               "up an inch, still closed. {he} has ruled, and {he} is not "
               "going to soften the ruling.",
        "soft": "The unblinking gaze finally blinks. The brush case lowers. "
                "The severity stays in the posture but leaves the eyes.",
        "greet": "{he} raises {his} eyes from the closed brush case to the "
                 "viewer, unhurried and without welcome or hostility, and "
                 "holds them there.",
    },
    "haengsu": {   # 우아한 귀공자 · 돈과 장사 · 겨드랑이의 장부
        "beat": "{he} shifts the ledger under {his} arm to a better grip. The "
                "muted gold silk catches light along one fold. The polite "
                "smile does not change. One measured blink.",
        "cut": "The polite smile stays exactly as it was, which is the point. "
                "The eyes go direct and cool. {he} has just said the number "
                "out loud.",
        "soft": "The smile loosens into a real one and the eyes crease. The "
                "ledger arm relaxes. This part is not being charged for.",
        "greet": "{he} tucks the ledger firmly under one arm, turns {his} "
                 "full attention to the viewer, and the polite smile arrives "
                 "on cue.",
    },
    "hunjang": {   # 엄격한 연상 · 공부와 시험 · 대나무 회초리
        "beat": "The upright bamboo rod taps down once, soundlessly, and "
                "rests. The eyes come up over the reading glasses low on the "
                "nose and go back down. The grey temples do not move.",
        "cut": "The eyes come up over the glasses and stop there. The rod "
               "stops. {he} has found where the work was not done.",
        "soft": "{he} takes the glasses off entirely, and without them the "
                "eyes are much older and much kinder. The rod leans away.",
        "greet": "The eyes lift over the reading glasses, take the measure of "
                 "the viewer, and the rod comes upright — class is in.",
    },
    "yakcho": {   # 다정한 연상 · 몸과 건강 · 허리춤의 마른 약초
        "beat": "The dried herbs tucked at the sash stir and settle. The "
                "sleeves stay tied back for work. The tired kind eyes blink "
                "once, softly, and stay warm.",
        "cut": "The warmth stays but the eyes stop being gentle. The head "
               "does not tilt. {he} has told the viewer the thing about {his} "
               "body that {he} has been ignoring.",
        "soft": "The eyes crease and the tiredness shows. {he} looks at the "
                "viewer the way you look at someone who has been carrying it "
                "a long time.",
        "greet": "{he} finishes tying back a sleeve, looks up, and the tired "
                 "eyes warm as though the viewer were the first good thing "
                 "all day.",
    },
    "ilgwan": {   # 무심한 미남 · 날 잡기 · 허리의 해시계
        "beat": "The shadow on the small sun dial at the belt moves one mark "
                "and stops. The gaze stays fixed slightly past the viewer's "
                "shoulder. One blink, entirely unbothered.",
        "cut": "The eyes come off the middle distance and land on the viewer "
               "for the first time. The flat expression does not change. That "
               "{he} bothered to look is the whole point.",
        "soft": "The gaze drifts back past the viewer's shoulder where it was "
                "before. The mouth stays flat. It is as close to reassurance "
                "as {he} gets.",
        "greet": "The eyes arrive on the viewer a beat later than expected, "
                 "as if {he} had checked the dial first and found the time "
                 "acceptable.",
    },
    "nopa": {   # 원조 걸크러쉬 · 갈림길 · 어깨의 담뱃대
        "beat": "A thin line of smoke rises slowly from the bowl of the long "
                "pipe resting on the shoulder and curls out of frame. The "
                "white knot of hair does not move. The fierce clear eyes stay "
                "open.",
        "cut": "The pipe comes off the shoulder an inch. The lined face sets "
               "and the clear eyes pin the viewer. {he} has seen this "
               "crossroads before and knows which way they will go.",
        "soft": "The pipe goes back on the shoulder. The lines around the "
                "eyes deepen into something like amusement. {he} has decided "
                "not to say the rest of it.",
        "greet": "{he} takes the pipe off {his} shoulder, looks the viewer up "
                 "and down once, and puts it back — approved.",
    },
    "dongja": {   # 청량한 소년 · 첫 자리 · 너무 긴 소매
        "beat": "{he} pushes one too-long sleeve back up {his} forearm and it "
                "slides straight back down over {his} hand. The tousled hair "
                "bounces. The open smile widens a little. Two quick blinks.",
        "cut": "The smile drops and the boy's face goes suddenly serious, "
               "eyes wide and direct. {he} has said something far too true "
               "for {his} age and knows it.",
        "soft": "The grin comes back all at once, bright and easy, and {he} "
                "ducks {his} chin. Whatever it was, it is over now.",
        "greet": "{he} looks up, breaks into a wide grin, and waves one "
                 "too-long sleeve at the viewer — the hand lost somewhere "
                 "inside it.",
    },
}


# 표정 파일 이름과 우리말 이름. 그림은 STAGE 가 사람마다 따로 적습니다.
MOOD_FILE = {
    "cut": ("bust_cut.png", "짚는"),
    "soft": ("bust_soft.png", "누그러뜨리는"),
}


def _pronouns(l: dict) -> dict:
    """
    그 사람의 대명사. lenses.json 의 sex 가 정합니다.

    ★ 손으로 적으면 한 사람은 반드시 틀립니다 — 실제로 표정 두 벌이
      「He」로 쓰인 채 **여자 일곱**에게 그대로 나가고 있었습니다.
    """
    m = l.get("sex") == "M"
    return {"he": "he" if m else "she",
            "his": "his" if m else "her",
            "him": "him" if m else "her"}


def _fill(text: str, l: dict) -> str:
    """
    대명사를 끼워 넣고 문장 첫 글자를 세운다.

    ★ 자리표시가 문장 맨 앞에 오면 「Static camera. she takes…」 가
      됩니다. 채워 넣은 뒤에 세워야 합니다 — 표에 대문자로 적어 두면
      문장 가운데에서 「and She」 가 됩니다.
    """
    import re
    out = " ".join(text.format(**_pronouns(l)).split())
    return re.sub(r"(^|(?<=[.!?] ))([a-z])",
                  lambda m: m.group(1) + m.group(2).upper(), out)


def _wrap(text: str, w: int = 72) -> str:
    import textwrap
    # 「too-long」 같은 말을 붙임표에서 끊으면 뜻이 갈립니다.
    return "\n".join(
        textwrap.wrap(text, w, break_on_hyphens=False))


def motion_of(l: dict, anim: str) -> str:
    """② 모션 — 그 사람이 3초 동안 하는 것."""
    st = STAGE[l["id"]]
    return (_wrap("Static camera. " + _fill(st["beat"], l)) + "\n\n"
            + MOTION_HOLD + "\n\n" + anim)


def greet_of(l: dict, anim: str) -> str:
    """③ 첫 대면 — 한 번만 돕니다. 도령만 파일이 있고 열아홉은 없습니다."""
    st = STAGE[l["id"]]
    return (_wrap("Static camera. " + _fill(st["greet"], l)) + "\n\n"
            + GREET_HOLD + "\n\n" + anim)


def mood_of(l: dict, key: str) -> str:
    """①-표정 — 같은 사람, 눈과 입만."""
    return MOOD_HEAD + "\n" + _wrap(_fill(STAGE[l["id"]][key], l))


def house_style() -> str:
    """신살 인물과 **같은** 머리말. 갈리면 한 집 식구로 안 보입니다."""
    d = json.loads(PROMPTS.read_text(encoding="utf-8"))
    img = d["figures"]["cheoneul"]["image"]
    return img[:img.index("\n\nA serene")].strip()


def animbase() -> str:
    d = json.loads(PROMPTS.read_text(encoding="utf-8"))
    return d["ANIMBASE"]


def colors() -> dict:
    """
    그 사람의 색. seed 에는 없고 화면 쪽(lenses.ts)에 있습니다.
    빛의 색을 그 사람 색으로 맞춰야 초상과 화면이 한 벌로 보입니다.
    """
    import re
    src = (ROOT / "apps" / "web" / "lib" / "lenses.ts").read_text(
        encoding="utf-8")
    return dict(re.findall(r'id: "(\w+)"[^}]*?color: "(#[0-9A-Fa-f]{3,8})"',
                           src))


COLOR: dict = {}


def lenses() -> list:
    return json.loads(LENSES.read_text(encoding="utf-8"))


def one(l: dict, style: str, anim: str) -> list:
    look = LOOK.get(l["archetype"])
    sex = "man" if l.get("sex") == "M" else "woman"
    who = look or ("a %s in Korean hanbok" % sex)
    # 그 사람의 색. seed 에는 없고 화면 쪽(lenses.ts)에 있습니다.
    tone = ("Key light subtly tinted %s. " % COLOR.get(l["id"], "").strip()
            if COLOR.get(l["id"]) else "")

    out = []
    out.append("=" * 74)
    out.append("  %s  %s   [%s]" % (l["name"], l["hanja"], l["id"]))
    out.append("  %s · %s · %s원 · 전문 %s"
               % (l["group"], l["archetype"], format(l["price"], ","),
                  l.get("specialty", "—")))
    out.append("  두는 곳  public/char/%s/bust.png   768×1024 투명 PNG · 눈높이 y=380"
               % l["id"])
    out.append("=" * 74)
    out.append("")
    out.append("--- ① 이미지 ---")
    out.append(style)
    out.append("")
    out.append(who + "." + ((" " + tone.strip()) if tone else ""))
    out.append("")
    out.append(TAIL)
    out.append("")
    for key in ("cut", "soft"):
        fn, ko = MOOD_FILE[key]
        out.append("--- ①-%s 표정 · %s ---" % (ko, fn))
        out.append(mood_of(l, key))
        out.append("")
        out.append("  나머지는 위 ① 과 똑같이. 배경도 흰색, 3:4.")
        out.append("  두는 곳  public/char/%s/%s" % (l["id"], fn))
        out.append("")

    out.append("--- ② 모션 · 도는 초상 (clip.webm · 3s · 이음새 있음) ---")
    out.append(motion_of(l, anim))
    out.append("")
    out.append("  두는 곳  public/char/%s/clip.webm · clip.mp4" % l["id"])
    out.append("")
    out.append("--- ③ 첫 대면 · 인사 (greet.webm · 2s · 한 번만) ---")
    out.append(greet_of(l, anim))
    out.append("")
    out.append("  두는 곳  public/char/%s/greet.webm · greet.mp4 · greet.webp"
               % l["id"])
    out.append("")
    return out


def main() -> int:
    ls = lenses()
    COLOR.update(colors())
    style, anim = house_style(), animbase()

    # ★ `--write 파일이름` 의 **값**을 사람 이름으로 세면 안 됩니다.
    #   처음 판이 그래서 "그런 사람이 없소: 캐릭터_초상_발주서.txt" 라고
    #   했습니다.
    argv, pick, skip = sys.argv[1:], [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a == "--write":
            skip = True
            continue
        if a.startswith("--"):
            continue
        pick.append(a)
    rows = [l for l in ls if not pick or l["id"] in pick]
    if pick and not rows:
        print("그런 사람이 없소: %s" % ", ".join(pick))
        print("있는 사람: %s" % ", ".join(l["id"] for l in ls))
        return 1

    missing = [l["name"] for l in ls if l["archetype"] not in LOOK]
    lines: list[str] = []
    lines.append("=" * 74)
    lines.append("  성신당 · 스무 사람 초상 발주서")
    lines.append("  화풍은 신살 인물과 같습니다 — 한 집 식구라야 합니다.")
    lines.append("  배경은 흰색입니다. 투명 PNG 로 잘라 써야 합니다 —")
    lines.append("  대사 옆 · 진열대 · 첫 대면이 서로 다른 바탕 위에 얹힙니다.")
    lines.append("=" * 74)
    lines.append("")
    if missing:
        lines.append("★ 그림 말이 아직 없는 원형: %s" % ", ".join(missing))
        lines.append("")

    for l in rows:
        lines += one(l, style, anim)

    # ── 화면이 읽는 묶음에도 넣는다 ─────────────────────────
    #
    # ★ 장면은 눌러서 프롬프트를 볼 수 있는데 캐릭터는 못 봤습니다.
    #   프롬프트가 이 도구(파이썬) 안에만 있어서 화면이 읽을 길이
    #   없었기 때문입니다. asset-prompts.json 에 `chars` 로 넣습니다 —
    #   장면·신살 인물과 **같은 자리**입니다.
    if "--json" in sys.argv:
        d = json.loads(PROMPTS.read_text(encoding="utf-8"))
        d["chars"] = {}
        for l in ls:
            look = LOOK.get(l["archetype"])
            sexw = "man" if l.get("sex") == "M" else "woman"
            who = look or ("a %s in Korean hanbok" % sexw)
            tone = (" Key light subtly tinted %s." % COLOR[l["id"]]
                    if COLOR.get(l["id"]) else "")
            d["chars"][l["id"]] = {
                "title": "%s %s" % (l["name"], l["hanja"]),
                "who": "%s · %s" % (l["group"], l["archetype"]),
                "hint": "전문 %s · %s원" % (l.get("specialty", "—"),
                                          format(l["price"], ",")),
                "spec": ["3:4", "초상", "768×1024 투명 PNG · 눈높이 y=380"],
                "seasonal": False, "seasons": None, "note": None,
                "preset": "Static", "ratio": "3:4", "duration": "3s",
                "loop": True, "tint": False, "still": False,
                # ★ 프롬프트를 고친 날. 화면(AssetBoard)이 이 날짜와
                #   그림 파일의 만든 날을 대 보고, 그림이 더 오래면
                #   「프롬프트가 바뀜」 이라 찍습니다. 안 그러면 낡은
                #   그림이 초록불로 남아 다 된 줄 압니다 — 도령 초상이
                #   비스듬한 채 그랬습니다.
                "revised": REVISED,
                "image": style + "\n\n" + who + "." + tone + "\n\n" + TAIL,
                "motion": motion_of(l, anim),
                # ★ 첫 대면 인사 — 코드에는 자리가 있는데(CharArt greet)
                #   **명령어가 한 줄도 없었습니다.** 도령만 파일이 있고
                #   열아홉은 무엇을 시켜야 할지가 어디에도 없었습니다.
                "greet": greet_of(l, anim),
                # 표정 두 벌 — 모달이 같이 보여 줍니다
                "moods": {k: {"file": MOOD_FILE[k][0],
                              "ko": MOOD_FILE[k][1],
                              "image": mood_of(l, k)}
                          for k in ("cut", "soft")},
            }
        PROMPTS.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
        print("화면이 읽는 묶음에 %d명을 넣었습니다 — %s"
              % (len(d["chars"]), PROMPTS.name))

    text = "\n".join(lines)
    if "--write" in sys.argv:
        i = sys.argv.index("--write")
        out = ROOT / (sys.argv[i + 1] if len(sys.argv) > i + 1
                      else "캐릭터_초상_발주서.txt")
        out.write_text(text + "\n", encoding="utf-8")
        print("%d명을 적었습니다 — %s" % (len(rows), out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
