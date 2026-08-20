"""훅 문장 중복률 측정 — 문장을 추가할 때마다 실행. 목표 15% 이하"""
import random, re, sys
sys.path.insert(0,"services/api")
from engine.calendar import build_chart
from engine.features import build_features      # T1-4
from engine.bank import build_hook              # T2-1

CONCERNS=["money","work","love","people","dir","health"]
T16=[a+b+c+d for a in "IE" for b in "NS" for c in "TF" for d in "JP"]
strip=lambda t: re.sub(r"[0-9.]+","",re.sub(r"<[^>]*>","",t)).strip()

def main(n=3000):
    seen=set(); stages={}
    for _ in range(n):
        c=build_chart(random.randint(1960,2006),random.randint(1,12),
                      random.randint(1,28),random.randint(0,23),0,
                      random.choice("FM"),True)
        F=build_features(c)
        segs=build_hook(F,random.choice(CONCERNS),random.choice(T16+[None]))
        for s in segs:
            stages.setdefault(s["stage"],set()).add(strip(s["html"]))
        seen.add("".join(strip(s["html"]) for s in segs))
    print(f"표본 {n}")
    for k,v in stages.items():
        print(f"  {k:6} {len(v):5}가지  중복률 {100-len(v)/n*100:5.1f}%")
    dup=100-len(seen)/n*100
    print(f"  전체   {len(seen):5}가지  중복률 {dup:5.1f}%")
    if dup>15: print("\n[FAIL] 중복률 15% 초과 — 뱅크 확장 필요"); sys.exit(1)
    print("\n[OK]")

if __name__=="__main__": main()
