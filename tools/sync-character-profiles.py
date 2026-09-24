"""Export public voice/address/topic contracts from the canonical character seed.

★ 고민 목록을 **이 도구가 손으로 들고 있었습니다** (2026-09-24).

  캐릭터가 보는 자리가 네 곳에 적혀 있었고 열다섯 명이 서로 달랐습니다 —

      seed/lenses.json     concerns    릴레이가 순위를 매길 때 보는 것
      seed/topic.json      LENS_ON     그 사람이 「내 자리요」 라 말하는 줄
      seed/lens_view.json  concerns    화면에 내려가는 것
      이 도구의 TOPICS                 ← 위 셋을 덮어쓰고 있었음

  그래서 풍운도령은 화면에 「여섯 고민을 다 본다」 고 적혀 있는데 리포트는
  「내가 맡은 일이 아니오」 라고 말했습니다. 손으로 고친 seed 를 이 도구가
  다시 덮어써서, 고쳐도 되돌아왔습니다.

  이제 **`seed/lenses.json` 한 자리**에서 받습니다. 릴레이가 그걸 보고,
  LENS_ON 이 그것과 같으니 셋이 한 벌이 됩니다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

lenses = json.loads((ROOT / 'seed/lenses.json').read_text(encoding='utf-8'))
rows = lenses['lenses'] if isinstance(lenses, dict) and 'lenses' in lenses else lenses
TOPICS = {row['id']: list(row.get('concerns') or []) for row in rows}

seed_path = ROOT / 'seed/lens_view.json'
seed = json.loads(seed_path.read_text(encoding='utf-8'))
for key, topics in TOPICS.items():
    if key not in seed:
        continue
    seed[key]['concerns'] = topics
    # ★ 기본 고민은 더 두지 않습니다. 손님이 고른 고민을 갈아치우는 데
    #   쓰이던 값이고, 그 갈아치우기를 뺐습니다 (engine/lens.concern_for).
    seed[key].pop('default_concern', None)
seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + '\n',
                     encoding='utf-8')

public = {key: {field: row[field]
                for field in ('voice', 'you', 'you_else', 'you_m', 'you_f',
                              'concerns')
                if field in row}
          for key, row in seed.items() if key != '_'}
(ROOT / 'apps/web/lib/character-profiles.json').write_text(
    json.dumps(public, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Exported', len(public), 'character contracts ·',
      'concerns 는 seed/lenses.json 에서 받았습니다')
