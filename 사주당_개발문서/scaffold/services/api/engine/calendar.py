"""
만세력 — docs/05_계산엔진_사양서.md 구현 골격

★ 이 파일이 서비스의 근간입니다. 절기·대운수 근사식 절대 금지.
  pip install sxtwl
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal, Optional

GAN = list("甲乙丙丁戊己庚辛壬癸")
JI  = list("子丑寅卯辰巳午未申酉戌亥")

ELEMENT_OF_GAN = {"甲":"목","乙":"목","丙":"화","丁":"화","戊":"토",
                  "己":"토","庚":"금","辛":"금","壬":"수","癸":"수"}
YIN_YANG = {"甲":1,"乙":0,"丙":1,"丁":0,"戊":1,"己":0,"庚":1,"辛":0,"壬":1,"癸":0}
ELEMENT_OF_JI = {"子":"수","丑":"토","寅":"목","卯":"목","辰":"토","巳":"화",
                 "午":"화","未":"토","申":"금","酉":"금","戌":"토","亥":"수"}
# 지장간 (본기 1.0 / 중기 0.3 / 여기 0.2) — 유파 확정값. 바꾸지 말 것.
HIDDEN = {
 "子":[("癸",1.0)], "丑":[("己",1.0),("癸",.3),("辛",.2)],
 "寅":[("甲",1.0),("丙",.3),("戊",.2)], "卯":[("乙",1.0)],
 "辰":[("戊",1.0),("乙",.3),("癸",.2)], "巳":[("丙",1.0),("庚",.3),("戊",.2)],
 "午":[("丁",1.0),("己",.3)], "未":[("己",1.0),("丁",.3),("乙",.2)],
 "申":[("庚",1.0),("壬",.3),("戊",.2)], "酉":[("辛",1.0)],
 "戌":[("戊",1.0),("辛",.3),("丁",.2)], "亥":[("壬",1.0),("甲",.3)],
}
GENERATES = {"목":"화","화":"토","토":"금","금":"수","수":"목"}   # 生
CONTROLS  = {"목":"토","화":"금","토":"수","금":"목","수":"화"}   # 剋
CHUNG = {"子":"午","丑":"未","寅":"申","卯":"酉","辰":"戌","巳":"亥",
         "午":"子","未":"丑","申":"寅","酉":"卯","戌":"辰","亥":"巳"}
# 오호둔 — 년간 → 寅월 천간
OHO  = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚",
        "辛":"庚","丁":"壬","壬":"壬","戊":"甲","癸":"甲"}
# 오서둔 — 일간 → 子시 천간
OSEO = {"甲":"甲","己":"甲","乙":"丙","庚":"丙","丙":"戊",
        "辛":"戊","丁":"庚","壬":"庚","戊":"壬","癸":"壬"}

# ── 자시 정책 ──────────────────────────────────────────────
# "조자시": 23:00~23:59 를 익일 일주로 넘김  (권장 · 확정)
# "야자시": 당일 일주 유지, 시주만 子
ZI_POLICY: Literal["조자시","야자시"] = "조자시"

# ── 시각 보정 ──────────────────────────────────────────────
CITY_LON = {"서울":126.98,"인천":126.71,"대전":127.38,"대구":128.60,
            "부산":129.08,"광주":126.85,"울산":129.31,"제주":126.53}

def std_meridian(y:int,m:int,d:int)->float:
    t = y*10000+m*100+d
    if t < 19120101: return 127.5
    if t < 19540321: return 135.0
    if t < 19610810: return 127.5
    return 135.0

DST_RANGES = [((1948,6,1),(1948,9,12)), ((1949,4,3),(1949,9,10)),
 ((1950,4,1),(1950,9,9)),  ((1951,5,6),(1951,9,8)),
 ((1955,5,5),(1955,9,8)),  ((1956,5,20),(1956,9,29)),
 ((1957,5,5),(1957,9,21)), ((1958,5,4),(1958,9,20)),
 ((1959,5,3),(1959,9,19)), ((1960,5,1),(1960,9,17)),
 ((1987,5,10),(1987,10,11)),((1988,5,8),(1988,10,9))]

def is_dst(y:int,m:int,d:int)->bool:
    t=(y,m,d)
    return any(a<=t<=b for a,b in DST_RANGES)

def jdn(y:int,m:int,d:int)->int:
    a=(14-m)//12; yy=y+4800-a; mm=m+12*a-3
    return d+(153*mm+2)//5+365*yy+yy//4-yy//100+yy//400-32045

JDN_BASE = jdn(1900,1,1)   # 1900-01-01 = 甲戌

@dataclass
class Correction:
    std_label:str; std_deg:float; dst:bool
    lon:float; lon_min:float
    before:str; after:str; day_shift:int

@dataclass
class Chart:
    pillars: list           # [(gan,ji,label)] — 시각 미상이면 3개
    day_gan: str
    day_ji: str
    hour_known: bool
    sex: str
    correction: Correction

# ── 절기 (sxtwl) ───────────────────────────────────────────
def jieqi_month_ji(y:int,m:int,d:int,hh:int,mi:int)->tuple[str,int]:
    """
    TODO(T1-2): sxtwl 로 12절의 절입 '시각'까지 산출해 월지와 연도(입춘 기준)를 반환.
      import sxtwl
      lunar = sxtwl.fromSolar(y,m,d)
      ... getJieQiJD / JD2DD 로 절입 시각 비교
    근사 테이블 사용 금지.
    """
    raise NotImplementedError("sxtwl 연결 필요 — docs/05 2-2 참조")

def build_chart(year:int,month:int,day:int,
                hour:Optional[int],minute:Optional[int],
                sex:str, hour_known:bool=True, city:str="서울")->Chart:
    lon = CITY_LON.get(city,126.98)
    std = std_meridian(year,month,day)
    dst = is_dst(year,month,day)
    lon_min = (lon-std)*4

    h = hour if hour_known and hour is not None else 12
    mi = minute or 0
    before = f"{h:02d}:{mi:02d}"

    mins = h*60+mi
    if dst: mins -= 60
    mins += lon_min
    shift = 0
    if mins < 0:    mins += 1440; shift = -1
    elif mins >= 1440: mins -= 1440; shift = 1
    th, tm = int(mins//60), int(round(mins%60))

    d0 = date(year,month,day) + timedelta(days=shift)

    # 조자시 — 23시대는 익일 일주
    d_for_day = d0 + timedelta(days=1) if (ZI_POLICY=="조자시" and th==23 and hour_known) else d0

    # 년주·월주 (입춘·절입 시각 기준)
    month_ji, saju_year = jieqi_month_ji(d0.year,d0.month,d0.day,th,tm)
    yg = GAN[(saju_year-4)%10]; yj = JI[(saju_year-4)%12]
    off = (JI.index(month_ji)-JI.index("寅"))%12
    mg = GAN[(GAN.index(OHO[yg])+off)%10]

    # 일주
    n = jdn(d_for_day.year,d_for_day.month,d_for_day.day) - JDN_BASE
    dg = GAN[(n+GAN.index("甲"))%10]
    dj = JI[(n+JI.index("戌"))%12]

    pillars = [(yg,yj,"년주"),(mg,month_ji,"월주"),(dg,dj,"일주")]
    if hour_known:
        hi = ((th+1)%24)//2
        pillars.append((GAN[(GAN.index(OSEO[dg])+hi)%10], JI[hi], "시주"))

    return Chart(pillars, dg, dj, hour_known, sex,
        Correction(f"{'1908~1911' if std==127.5 and year<1912 else ''}",
                   std, dst, lon, round(lon_min,1),
                   before, f"{th:02d}:{tm:02d}", shift))
