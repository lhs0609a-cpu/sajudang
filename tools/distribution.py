"""분포 검증 — 도달 불가 분기 탐지. 어느 값이든 0%면 실패"""
import random, sys, collections
sys.path.insert(0,"services/api")
from engine.calendar import build_chart
from engine.features import build_features

def main(n=3000):
    c=collections.defaultdict(collections.Counter)
    for _ in range(n):
        ch=build_chart(random.randint(1960,2006),random.randint(1,12),
                       random.randint(1,28),random.randint(0,23),0,
                       random.choice("FM"),True)
        F=build_features(ch)
        c["일간"][F.day_gan]+=1; c["신강약"][F.strength]+=1
        c["주도십신"][F.top_ten_god]+=1; c["약오행"][F.weak_el]+=1
        c["흐름"][F.flow]+=1
    fail=False
    EXPECT={"일간":10,"신강약":3,"주도십신":10,"약오행":5,"흐름":5}
    for k,cnt in c.items():
        line=" ".join(f"{a} {b/n*100:.1f}%" for a,b in cnt.most_common())
        print(f"{k:8} {line}")
        if len(cnt)<EXPECT[k]:
            print(f"  [FAIL] {k}: {EXPECT[k]}종 중 {len(cnt)}종만 출현 — 도달 불가 분기")
            fail=True
    sys.exit(1 if fail else 0)

if __name__=="__main__": main()
