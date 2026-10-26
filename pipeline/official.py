"""Official records for North Carolina -> one table of permitted food businesses, plus their inspections.

Counties inspect restaurants under the state's rules (15A NCAC 18A .2600) and post the result on a grade card: the score, and the grade
rule .2662 attaches to it (A at 90 or more, B 80 to under 90, C 70 to under 80; under 70 the permit is revoked). The statewide portal
(public.cdpehs.com) is search only. The one county that publishes its records as open data (playbook/12-sources.md):
- "wak": Wake County Environmental Health & Safety, through Wake County's Open Data hub (data.wake.gov, CC BY 4.0): every active
         permitted food facility (closed ones drop out of all three tables) with HSISID (the state ID), name, address, a point and the
         facility type; every inspection since 2012-09-20 with its score; every cited violation with its Food Code item, severity and
         points. The inspector names and free-text comments in the tables are never read into the app or the leaderboard.

load() returns: jur, lic (our id), name, keys (name keys), addr, city, zip, num, street, lat, lon, kind, active, ltype, opened.
kind: food (restaurants, food stands, limited food service) | truck (mobile food units, push carts) | retail (meat markets)
      | other (school lunchrooms, institutions, elderly nutrition sites).
"""
import os, re, json, datetime
import numpy as np, pandas as pd
from common import norm_name, RAW, name_sim, _stems, GENERIC, canon_city

OFF = os.path.join(RAW, "official")
DIRS = {"N": "N", "S": "S", "E": "E", "W": "W", "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
TYPES = set("ST STREET AVE AV AVENUE BLVD BOULEVARD RD ROAD DR DRIVE LN LANE CT COURT PL PLACE PKWY PARKWAY TER TRL TRAIL WAY HWY CIR "
            "CIRCLE PLZ SQ MALL BND PASS XING RUN ROW WALK RDG LOOP FWY FREEWAY EXPY EXPRESSWAY PIKE PK PKE BV".split())


def road(a):
    """One spelling for numbered roads: 'US HIGHWAY 70' = 'US-70' = 'US 70'; 'NC HWY 55' = 'NC-55' = 'SR 55' = 'SH 55';
    'N INTERSTATE 40' = 'I-40'; 'COUNTY ROAD 5' = 'CR 5'."""
    a = re.sub(r"(\d)\s*&\s*(\d)", r"\1-\2", a.upper())
    a = re.sub(r"\b(US|NC|SR|SH|CR|I|IH)-(\w)", r"\1 \2", a)
    a = re.sub(r"\b(?:INTERSTATE(?: HIGHWAY| HWY)?|IH|I H)\s*(?=\d)", "I ", a)
    a = re.sub(r"\b(?:US|U S)\s+(?:HIGHWAY|HWY)\b", "US", a)
    a = re.sub(r"\b(?:STATE (?:HIGHWAY|HWY|ROAD|RD|ROUTE|RTE)|SR|SH|NORTH CAROLINA (?:HIGHWAY|HWY)|NC (?:HIGHWAY|HWY)|NC)\b(?=\s*\d)", "SH", a)
    a = re.sub(r"\b(?:COUNTY (?:HIGHWAY|HWY|ROAD|RD)|CO RD|CTY (?:HWY|RD)|CR)\b", "CR", a)
    a = re.sub(r"\bHIGHWAY\b", "HWY", a)
    return re.sub(r"\b(US|SH|CR|HWY|I) (\w+)\s*-\s*\w+", r"\1 \2", a)


ORD = {"FIRST": "1ST", "SECOND": "2ND", "THIRD": "3RD", "FOURTH": "4TH", "FIFTH": "5TH", "SIXTH": "6TH", "SEVENTH": "7TH",
       "EIGHTH": "8TH", "NINTH": "9TH", "TENTH": "10TH", "ELEVENTH": "11TH", "TWELFTH": "12TH"}


def street_key(a):
    """'2505 Monroe St' -> ('2505', 'MONROE'); '1000 OSAGE STREET' -> ('1000', 'OSAGE'); 'E Colfax Ave' keeps 'COLFAX'."""
    if not isinstance(a, str):
        return None, None
    a = re.sub(r"[.,#]", " ", road(a))
    m = re.match(r"^\s*(\d+)[A-Z]?(?:\s*-\s*\d+[A-Z]?)?\s+(.*)$", a)
    if not m:
        return None, None
    words = [w for w in m.group(2).split() if w]
    if len(words) > 1 and words[0] in DIRS:
        words = words[1:]
    core = []
    for w in words:
        if w in TYPES and core:
            break
        core.append(w)
    core = [ORD.get(w, w) for w in core]
    return m.group(1), " ".join(core[:3]) or None


def street_compat(a, b):
    """Same street, or one is a whole-word prefix of the other: Boulder's 2025 set sometimes truncates ("1206 CENTAUR" = Centaur Village Dr)."""
    if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
        return False
    return a == b or a.startswith(b + " ") or b.startswith(a + " ")


def street_nums(a):
    """'157-159 W Main St' -> {'157', '159'}; '2505 Monroe St' -> {'2505'}."""
    if not isinstance(a, str):
        return set()
    a = road(a)
    m = re.match(r"^\s*(\d+)[A-Z]?(?:\s*-\s*(\d+)[A-Z]?)?\s", a.upper() + " ")
    if not m:
        return set()
    lo = int(m.group(1)); hi = int(m.group(2)) if m.group(2) else lo
    if hi < lo:   # "1500-02"
        hi = int(str(lo)[: len(str(lo)) - len(m.group(2))] + m.group(2)) if m.group(2) else lo
    return {str(x) for x in range(lo, hi + 1, 2 if (hi - lo) % 2 == 0 else 1)} if 0 <= hi - lo <= 12 else {str(lo)}


def _names(*vals):
    out = []
    for v in vals:
        if not isinstance(v, str):
            continue
        v = re.sub(r"\s*\((?:MOBILE|MOBILE UNIT|COMMISSARY|CATERING|SPECIAL EVENT|SPEC EVENT|TEMP(?:ORARY)? EVENT|CP|INSIDE [^)]*)\)\s*$", "", v, flags=re.I)
        for part in re.split(r"\s*/\s*|\s+\bdba\b\s+|\s+&\s+(?=[A-Z][a-z])", v, flags=re.I):
            k = norm_name(re.sub(r"\b(?:LLC|INC|CORP|CORPORATION|LTD|CO)\b\.?", "", part, flags=re.I))
            if k and k not in out:
                out.append(k)
    return out





# the day the Wake tables were fetched (fetch_official.py writes it)
_META = os.path.join(OFF, "wake_meta.json")
LIST_DATE = json.load(open(_META)).get("fetched") if os.path.exists(_META) else None
WAKE_ITEM = "https://data.wake.gov/datasets/124c2187da8c41c59bde04fa67eb2872"
WAKE_INSP_ITEM = "https://data.wake.gov/datasets/ebe3ae7f76954fad81411612d7c4fb17"
# the statewide portal's page for one county: counties are numbered alphabetically (Alamance 1 ... Mecklenburg 60 ... Yancey 100).
# The portal is search only, so a place links its county's page, which the portal renders server-side (checked with curl)
PORTAL = "https://public.cdpehs.com/NCENVPBL/ESTABLISHMENT/ShowESTABLISHMENTTablePage.aspx?ESTTST_CTY="
_COUNTIES = """Alamance Alexander Alleghany Anson Ashe Avery Beaufort Bertie Bladen Brunswick Buncombe Burke Cabarrus Caldwell Camden Carteret
Caswell Catawba Chatham Cherokee Chowan Clay Cleveland Columbus Craven Cumberland Currituck Dare Davidson Davie Duplin Durham Edgecombe
Forsyth Franklin Gaston Gates Graham Granville Greene Guilford Halifax Harnett Haywood Henderson Hertford Hoke Hyde Iredell Jackson
Johnston Jones Lee Lenoir Lincoln McDowell Macon Madison Martin Mecklenburg Mitchell Montgomery Moore Nash New_Hanover Northampton
Onslow Orange Pamlico Pasquotank Pender Perquimans Person Pitt Polk Randolph Richmond Robeson Rockingham Rowan Rutherford Sampson
Scotland Stanly Stokes Surry Swain Transylvania Tyrrell Union Vance Wake Warren Washington Watauga Wayne Wilkes Wilson Yadkin Yancey"""
COUNTY_NO = {n.replace("_", " ") + " County": i + 1 for i, n in enumerate(_COUNTIES.split())}
assert len(COUNTY_NO) == 100 and COUNTY_NO["Mecklenburg County"] == 60 and COUNTY_NO["Union County"] == 90 and COUNTY_NO["Wake County"] == 92
# rule .2662's grade for an official score (the grade card shows both); under 70 the permit is revoked and there is no grade
def grade(score):
    if score is None or score != score:
        return None
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "Under 70"


def _zip(z):
    z = re.sub(r"\D", "", str(int(z)) if isinstance(z, float) and z == z else str(z or ""))
    return z[:5] if len(z) >= 5 else ""


KIND = {"1": "food", "2": "food", "14": "food", "3": "truck", "4": "truck", "30": "retail"}   # every other type: schools, institutions
TYPE_LABEL = {"1": "Restaurant", "2": "Food stand", "14": "Limited food service", "3": "Mobile food unit", "4": "Push cart",
              "30": "Meat market", "5": "Private school lunchroom", "9": "Elderly nutrition site", "11": "Public school lunchroom",
              "16": "Institutional food service"}
OTHER = re.compile(r"\b(?:SCHOOL|ELEMENTARY|ACADEMY|HOSPITAL|JAIL|DETENTION|SENIOR|NURSING|COMMISSARY|CORRECTION(?:AL)?|CAMPUS|WAREHOUSE|"
                   r"DISTRIBUT\w*|WHOLESALE|DAYCARE|DAY CARE|CHILD CARE)\b", re.I)


def _row(jur, lic, name, addr, city, z, la, lo, kind, active=True, ltype=None, holder=None):
    num, st = street_key(addr)
    if kind == "food" and OTHER.search(name or ""):
        kind = "other"
    return {"jur": jur, "lic": lic, "name": name, "dba": name, "holder": holder, "keys": _names(name), "addr": addr, "city": city,
            "zip": _zip(z), "num": num, "street": st, "lat": la, "lon": lo, "kind": kind, "active": active, "ltype": ltype}


def _addr(a):
    """'2426 WAKE FOREST RD ' -> '2426 Wake Forest Rd' (directions and unit words keep their case)."""
    a = re.sub(r"\s+", " ", a or "").strip()
    return re.sub(r"\b([A-Z]{2,})\b", lambda m: m.group(1).title() if m.group(1) not in ("NE", "NW", "SE", "SW", "US", "NC") else m.group(1), a)


def _csv(name):
    return pd.read_csv(os.path.join(OFF, f"{name}.csv"), dtype=str, encoding="utf-8-sig")


def load_wake():
    global LIST_DATE
    meta = json.load(open(os.path.join(OFF, "wake_meta.json")))
    LIST_DATE = meta.get("fetched")
    rows = []
    for r in _csv("wake_restaurants").itertuples():
        code = str(r.FACILITYTYPE or "").split(" - ")[0].strip()
        la, lo = pd.to_numeric(r.Y, errors="coerce"), pd.to_numeric(r.X, errors="coerce")
        if not (33.5 < (la if la == la else 0) < 37 and -85 < (lo if lo == lo else 0) < -75):
            la = lo = np.nan
        addr = " ".join(x for x in (r.ADDRESS1, r.ADDRESS2) if isinstance(x, str) and x.strip())
        x = _row("wak", "wak-" + r.HSISID, (r.NAME or "").strip(), _addr(addr), canon_city(r.CITY), r.POSTALCODE, la, lo,
                 KIND.get(code, "other"), ltype=TYPE_LABEL.get(code, (r.FACILITYTYPE or "").split(" - ")[-1]))
        x["hsisid"] = r.HSISID
        x["phone"] = r.PHONENUMBER if isinstance(r.PHONENUMBER, str) and re.search(r"\d{3}\D*\d{4}", r.PHONENUMBER) else None
        # the permit's date: a new owner gets a new permit, so this is not the day the restaurant opened
        x["permitted"] = (r.RESTAURANTOPENDATE or "")[:10].replace("/", "-") or None
        x["geocode"] = r.GEOCODESTATUS
        rows.append(x)
    return pd.DataFrame(rows)


def wake_inspections(through):
    """Every scored inspection on or before `through` -> HSISID, date, score, type ('Inspection' / 'Re-inspection'), grade.
    A score of 0 (19 rows) is no score: the grade card never shows 0, so those rows carry no result."""
    d = _csv("wake_inspections")
    d["d"] = d.DATE_.str[:10].str.replace("/", "-")
    d["score"] = pd.to_numeric(d.SCORE, errors="coerce")
    d = d[d.d.notna() & (d.d <= through) & d.score.gt(0)].copy()
    d["typ"] = np.where(d.TYPE.str.startswith("2"), "Re-inspection", "Inspection")
    d["grade"] = d.score.map(grade)
    return d[["HSISID", "d", "score", "typ", "grade"]].rename(columns={"HSISID": "hsisid"}).sort_values(["hsisid", "d"])


def wake_violations(through):
    """Cited items per inspection (HSISID + date): Food Code section, severity (Priority, Priority Foundation, Core), the item's
    official short description, points, and whether it was corrected during the inspection (CDI) or a repeat (R)."""
    d = _csv("wake_violations")
    d["d"] = d.INSPECTDATE.str[:10].str.replace("/", "-")
    d = d[d.d.notna() & (d.d <= through)]
    d["pts"] = pd.to_numeric(d.POINTVALUE, errors="coerce").fillna(0)
    return d[["HSISID", "d", "VIOLATIONCODE", "SEVERITY", "SHORTDESC", "pts", "VIOLATIONTYPE"]].rename(
        columns={"HSISID": "hsisid", "VIOLATIONCODE": "code", "SEVERITY": "sev", "SHORTDESC": "desc", "VIOLATIONTYPE": "vt"})


def load():
    df = load_wake()
    # one business can hold several records (two permits at one address under one name): same address and a name in common
    df["biz"] = np.arange(len(df))
    town = df.city.fillna("").str.upper().str.strip()
    for num, g in df[df.num.notna() & df.street.notna()].groupby("num"):
        idx = list(g.index)
        if len(idx) < 2 or len(idx) > 400:
            continue
        for x in range(len(idx)):
            for y in range(x + 1, len(idx)):
                a, b = idx[x], idx[y]
                if not street_compat(df.at[a, "street"], df.at[b, "street"]):
                    continue
                if not ((df.at[a, "zip"] and df.at[a, "zip"] == df.at[b, "zip"]) or (town[a] and town[a] == town[b])):
                    continue
                ka, kb = df.at[a, "keys"], df.at[b, "keys"]
                if not ka or not kb:
                    continue
                if any(name_sim(p, q) >= 85 or ((_stems(p) - GENERIC) & (_stems(q) - GENERIC)) for p in ka for q in kb):
                    old, new = df.at[b, "biz"], df.at[a, "biz"]
                    df.loc[df.biz == old, "biz"] = new
    df["county"] = "Wake County"
    return df
