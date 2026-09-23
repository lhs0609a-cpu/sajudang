"""Export public voice/address/topic contracts from the canonical character seed."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TOPICS = {
 'pungun': ['money','work','love','people','dir','health'],
 'baegun': ['dir','work','love','people','money','health'],
 'cheongam':['dir','work'], 'sigye':['dir','work'], 'eunbyeol':['people','dir'],
 'jeokhyeol':['love'], 'monghwa':['dir','people'], 'seoyeok':['dir'],
 'paeseon':['dir','money'], 'myeonsang':['people','work'], 'wolha':['love','people'],
 'hongmae':['love','people'], 'yeondam':['love'], 'hwagyeong':['people','love'],
 'haengsu':['money','work'], 'hunjang':['work','dir'], 'yakcho':['health'],
 'ilgwan':['dir','work'], 'nopa':['dir','people','work'],
 'dongja':['dir','money','work','love','people','health'],
}
seed_path=ROOT/'seed/lens_view.json'
seed=json.loads(seed_path.read_text(encoding='utf-8'))
for key, topics in TOPICS.items():
    seed[key]['concerns']=topics
    seed[key]['default_concern']=topics[0]
seed_path.write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
public={key:{field:row[field] for field in ('voice','you','you_else','you_m','you_f','concerns','default_concern') if field in row} for key,row in seed.items() if key!='_'}
(ROOT/'apps/web/lib/character-profiles.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Exported',len(public),'character contracts')
