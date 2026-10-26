"""Writes the public website in docs/ from the same data the app ships (data/app/places.json plus the data/app/detail-*.json files that
hold Wake County permits and inspection histories, phones and websites).

Pages: the landing page; the statewide hand-checked guides with at least MIN_GUIDE places (Eastern North Carolina whole hog, Lexington
barbecue, Carolina hot dogs, biscuits and livermush; Calabash seafood, Moravian bakeries and the oldest places join once their research
reaches that size); MICHELIN & James Beard; North Carolina's restaurant grades explained (Wake County's published scores, and every
other county's page in the state's own search); one page per city or town with enough hand-checked or honored places to say something
real, plus a cities index; the web app (/explore/); privacy; terms; 404; sitemap.xml, robots.txt, site.webmanifest and
playbook/site-numbers.json. Everything listed is hand-checked research or public records; nothing comes from Google, Yelp or any
ratings site, and nothing is ranked by ratings. Ported from tn-eats/scripts/make-site.py (inspections after oh-eats).

Rules the copy keeps (scripts/qa-site.py checks them):
- Every number is counted from the data here, never typed in. North Carolina has no statewide restaurant list, so our lists are "places
  we list": no sentence claims "every" or "all N" restaurants.
- "Checked" only for the hand-checked lists (`hc`, a 2025-26 source for each place).
- A grade is the letter rule 15A NCAC 18A .2662 gives the score Wake County published (the card by the door), never one of ours; no
  page lists or names places by a low score. Other counties' results stay in the state's search, linked, never copied.
- Alcohol is unknown everywhere ("—", never "no"): North Carolina's ABC permits aren't published as a list.
- Claims stay claims: founding years are tied to a dated source, and "first", "oldest" or "original" are the source's words.
- Every page carries a hash-pinned Content-Security-Policy; inline scripts and styles are hashed after the page is final.

Usage (from nc-eats/): .venv/bin/python scripts/make-site.py           (github.io address, BASE /north-carolina-eats)
                       NC_DOMAIN=northcarolina.eatsranked.com .venv/bin/python scripts/make-site.py   (once Nick's CNAME resolves)
Re-run it after every data rebuild, then check the pages with scripts/qa-site.py. Never hand-edit docs/*.html.
"""
import base64
import datetime as dt
import glob
import gzip
import hashlib
import html
import json
import math
import os
import re
import struct
import urllib.parse
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS = f"{ROOT}/docs"
# Where the site lives. Until Nick's Cloudflare record (CNAME northcarolina -> nickstrom5.github.io, DNS only) resolves, GitHub Pages
# serves the project address. When `dig northcarolina.eatsranked.com` shows the CNAME, run with NC_DOMAIN=northcarolina.eatsranked.com
# and push: this writes docs/CNAME, and GitHub then forwards the old github.io links (the ones inside shipped app builds).
CUSTOM_DOMAIN = os.environ.get("NC_DOMAIN", "").strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
REPO = "north-carolina-eats"
DOMAIN = f"https://{CUSTOM_DOMAIN}" if CUSTOM_DOMAIN else f"https://nickstrom5.github.io/{REPO}"
BASE = "" if CUSTOM_DOMAIN else f"/{REPO}"     # path prefix for root-relative links
BRAND = "North Carolina Eats"
APP_NAME = "North Carolina Eats"      # Nick, 2026-10-26: "North Carolina Eats: Restaurants" is over Apple's 30, so "Restaurants" is the subtitle
TAGLINE = "Restaurants, BBQ & biscuits"
EMAIL = "nick@eatsranked.com"   # Nick, 2026-10-12: the site's contact address (Cloudflare Email Routing)
PUBLISHED = "2026-10-26"        # the site's first publication (Article datePublished)
SITE_REV = "2026-10-26"         # the last change to this generator's own copy or code: bump it when you change the words
POLICY_UPDATED = "2026-10-26"   # privacy policy and terms: bump only when their text changes
PRIVACY_UPDATED = "2026-10-26"   # the privacy policy alone: the app's data updates (OTA-DATA.md)
CHECKED = "fall 2026"
STORAGE_PREFIX = "nceats-"      # the web app's localStorage keys (other state sites share the nickstrom5.github.io origin)
# North Carolina Eats is one of the Eats Ranked state sites: the hub (eatsranked.com) lists it as a subOrganization, and every page says so
# from this side too (the footer line and the Organization's parentOrganization), in Wisconsin's words.
HUB = {"@type": "Organization", "@id": "https://eatsranked.com/#organization", "name": "Eats Ranked", "url": "https://eatsranked.com/"}
ORG_ID = f"{DOMAIN}/#org"
# the site's Organization as other pages name it (author, publisher): the same @id as the full node on the landing page
ORG_REF = {"@type": "Organization", "@id": ORG_ID, "name": BRAND, "url": f"{DOMAIN}/",
           "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/icon-512.png", "width": 512, "height": 512}, "parentOrganization": HUB}

# ---------------------------------------------------------------- data: the core file plus the region detail files
D = json.load(open(f"{ROOT}/data/app/places.json"))
assert D.get("generated"), "data/app/places.json has no 'generated' field: the pipeline hasn't finished writing it"
DETAIL_SRC = {}
for _f in sorted(glob.glob(f"{ROOT}/data/app/detail-*.json")):
    DETAIL_SRC.update(json.load(open(_f)))
assert DETAIL_SRC, "data/app/detail-*.json are missing"


def merged(r):
    """One place with its detail fields put back: the core's "in" is [county, grade, date, score]; the detail's "in" is {n, h, i}."""
    out = dict(r)
    ins = r.get("in")
    if isinstance(ins, list) and len(ins) == 4:
        out["in"] = {"j": ins[0], "b": ins[1], "d": ins[2], "s": ins[3]}
    for k, v in (DETAIL_SRC.get(r["id"]) or {}).items():
        if k == "in" and isinstance(v, dict):
            out["in"] = {**(out.get("in") or {}), **v}
        else:
            out[k] = v
    return out


RECS = [merged(r) for r in D["places"]]
TODAY = max(str(D.get("generated") or SITE_REV)[:10], SITE_REV)   # sitemap lastmod and dateModified move with the data or the copy
PERMITS_UPDATED = D.get("permits_updated") or ""
CITIES, CUISINES, COUNTIES = D["cities"], D["cuisines"], D["counties"]
BBQEAST, BBQLEX, HOTDOG, CALABASH, BISCUIT, MORAVIAN, OLDEST = 1, 2, 4, 8, 16, 32, 64
MI = ["", "MICHELIN Recommended", "Bib Gourmand", "1 MICHELIN Star", "2 MICHELIN Stars", "3 MICHELIN Stars"]
# Wake County's open data (data.wake.gov, CC BY 4.0): its permits and its inspections, the one county that publishes them in bulk
WAKE_PERMITS = D.get("permits_url") or "https://data.wake.gov/datasets/124c2187da8c41c59bde04fa67eb2872"
WAKE_INSPECTIONS = D.get("inspections_url") or "https://data.wake.gov/datasets/ebe3ae7f76954fad81411612d7c4fb17"
# the state's inspection search (NC DHHS, all 100 counties): a county's page is PORTAL + its number. Linked, never copied.
PORTAL = D["portal"]
COUNTY_NO = D["county_no"]
assert len(COUNTY_NO) == 100 and COUNTY_NO["Wake County"] == 92 and COUNTY_NO["Mecklenburg County"] == 60, "the portal numbers counties alphabetically"
GRADING_RULES = "https://ehs.dph.ncdhhs.gov/docs/rules/Sanitation-of-FoodEstablishments-15ANCAC18A-2600.pdf"   # 15A NCAC 18A .2600
INS_THROUGH = (D.get("inspections_through") or {}).get("wak") or ""
RESULTS, ITYPES = D.get("results") or [], D.get("itypes") or []
assert RESULTS == ["A", "B", "C"] and D.get("ins_jur") == ["wak"], (RESULTS, D.get("ins_jur"))


def portal_url(county):
    return PORTAL + str(COUNTY_NO[county]) if county in COUNTY_NO else PORTAL.split("?")[0]


def score_text(x):
    """96.0 -> "96", 96.5 -> "96.5": the county's own number, as printed on the card."""
    x = float(x)
    return str(int(x)) if x == int(x) else f"{x:g}"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def hdate(iso):
    """2026-09-24 -> September 24, 2026"""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{MONTHS[int(m[2]) - 1]} {int(m[3])}, {m[1]}" if m else str(iso or "")


def hmonth(iso):
    m = re.match(r"(\d{4})-(\d{2})", str(iso or ""))
    return f"{MONTHS[int(m[2]) - 1]} {m[1]}" if m else str(iso or "")


def plural(n, one, many=None):
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def words_num(n):
    return NUM_WORDS[n] if 0 <= n < len(NUM_WORDS) else f"{n:,}"


def safe_url(u):
    """Only http(s) links leave the site; a bare host ("example.com/menu") gets https://. Anything else is dropped."""
    u = str(u or "").strip()
    if re.fullmatch(r"https?://[^\s\"'<>\\]+", u, re.I):
        return u
    if re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}(?:[/?#][^\s\"'<>\\]*)?", u, re.I):
        return "https://" + u
    return ""


# Websites we must not link (pipeline/website_blocklist.json): hacked, expired or another business's site. A blocked link is
# dropped, never the place. qa-site.py fails if a blocked domain or URL appears anywhere in docs/.
BLOCKLIST = json.load(open(f"{ROOT}/pipeline/website_blocklist.json"))
for _b in BLOCKLIST:
    assert _b.get("match", "domain") in ("domain", "url") and (_b.get("url") or _b.get("domain")), f"bad blocklist entry {_b}"
BLOCKED_LINKS = []   # (place, link) pairs the blocklist dropped from this build


def url_key(u):
    """A URL compared without its scheme, a leading www., a trailing slash or letter case."""
    return re.sub(r"^(?:https?:)?//(?:www\.)?", "", str(u or "").strip().lower()).rstrip("/")


def blocked_site(u):
    host = (urllib.parse.urlsplit(u).hostname or "").rstrip(".").removeprefix("www.")
    for b in BLOCKLIST:
        if b.get("match", "domain") == "url":
            if url_key(u) == url_key(b.get("url") or b["domain"]):
                return b
        else:
            d = b["domain"].strip().lower().rstrip(".").removeprefix("www.")
            if host == d or host.endswith("." + d):
                return b
    return None


class P:
    """One place, with the same meaning the app gives each field (NorthCarolinaEats/Models/Place.swift)."""

    def __init__(self, r):
        self.r = r
        self.name = str(r["n"])
        self.city = CITIES[r["c"]] if r.get("c") is not None else ""
        self.county = COUNTIES[r["co"]] if r.get("co") is not None else None
        self.cuisine = CUISINES[r["cu"]] if r.get("cu") is not None else ""
        self.addr = (r.get("a") or "").strip().rstrip(",").strip()
        self.zip = str(r.get("z") or "")
        self.lat, self.lon = r.get("la"), r.get("lo")
        self.tags = r.get("g") or 0
        self.chain = (r.get("ch") or 0) >= 5
        self.venue = r.get("v") == 1
        self.ip = r.get("ip")
        self.founded = r.get("f") if isinstance(r.get("f"), int) else None
        self.fn = r.get("fn") or ""
        self.dishes = (r.get("dish") or "").replace("; ", ", ")
        self.season = r.get("seas") or ""
        self.note = r.get("note") or ""
        self.site = safe_url(r.get("w"))
        if self.site and blocked_site(self.site):
            BLOCKED_LINKS.append((self.name, self.site))
            self.site = ""   # the link goes, the place stays
        self.jbf = r.get("jbf") or ""
        self.h = r.get("h") or 0
        self.mi = r.get("mi") if r.get("mi") in range(1, len(MI)) else 0
        self.hc = r.get("hc") == 1   # hand-checked against a 2025-26 source; the only places the themed guides list
        self.lic = r.get("lic") or []   # Wake County food service permits: [[list, number]]
        ins = r.get("in") if isinstance(r.get("in"), dict) else {}
        # Wake County's latest inspection: its score and the letter rule .2662 gives it (the card by the door)
        self.ins = ins if isinstance(ins.get("b"), int) and 0 <= ins["b"] < len(RESULTS) and ins.get("d") and ins.get("s") is not None else None
        self.grade = RESULTS[self.ins["b"]] if self.ins else None

    def featured_key(self):
        # the app's "Featured first": honored places, then documented founding year, then name
        return (-(self.ip if self.ip is not None else -1), self.founded or 9999, self.name.lower())

    def jb_label(self):
        return ("America's Classic" if self.h & 1 else "James Beard winner" if self.h & 2 else "James Beard finalist" if self.h & 4
                else "James Beard semifinalist" if self.h & 8 else None)

    def promo_ok(self):
        """North Carolina publishes no ratings we show, so any listed place may be named in promotional copy (never by its score)."""
        return True

    def in_guide(self, tag):
        return self.hc and bool(self.tags & tag)


PLACES = [P(r) for r in RECS]
REST = [p for p in PLACES if not p.venue]

# every hand-checked guide the app has; a guide gets its own page once it holds MIN_GUIDE places (the research lands guide by guide)
ALL_GUIDES = [("bbqeast", BBQEAST), ("bbqlex", BBQLEX), ("hotdogs", HOTDOG), ("calabash", CALABASH), ("biscuits", BISCUIT), ("moravian", MORAVIAN)]
MIN_GUIDE = 4
L_ALL = {k: sorted([p for p in REST if p.in_guide(t)], key=P.featured_key) for k, t in ALL_GUIDES}
GUIDE_TAGS = [(k, t) for k, t in ALL_GUIDES if len(L_ALL[k]) >= MIN_GUIDE]
L = {k: L_ALL[k] for k, _ in GUIDE_TAGS}
HON_L = sorted([p for p in REST if p.mi or p.jbf], key=P.featured_key)
OLD_L = sorted([p for p in REST if p.founded and p.in_guide(OLDEST)], key=lambda p: (p.founded, p.name.lower()))
HAS_OLD = len(OLD_L) >= MIN_GUIDE
HC_ANY = [p for p in REST if p.hc and (p.tags & (BBQEAST | BBQLEX | HOTDOG | CALABASH | BISCUIT | MORAVIAN | OLDEST))]   # on a hand-checked guide
INS_L = [p for p in REST if p.ins]
GRADE_N = Counter(p.grade for p in INS_L)

# ---------------------------------------------------------------- regions: the app's six (each county to the nearest anchor), mountains to sea
REGIONS = list(D.get("regions") or [])
REGION_NAME = {r: r for r in REGIONS}
REGION_ORDER = ["Asheville & the Mountains", "Charlotte & the Southern Piedmont", "Greensboro, Winston-Salem & the Triad",
                "Raleigh, Durham & the Triangle", "Wilmington & the Southern Coast", "Eastern North Carolina & the Outer Banks"]
assert set(REGION_ORDER) == set(REGIONS), REGIONS
for p in PLACES:
    rg = p.r.get("rg")
    p.region = REGIONS[rg] if isinstance(rg, int) and 0 <= rg < len(REGIONS) else None


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- html helpers
e = html.escape


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("'", "").replace("&", "and")).strip("-")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def join_words(xs, conj="and"):
    xs = [x for x in xs if x]
    if len(xs) <= 1:
        return "".join(xs)
    return ", ".join(xs[:-1]) + f" {conj} " + xs[-1]


def fit(cands, lo, hi, what=""):
    seen = []
    # a description that misses the window by a few characters gets a fixed tail
    more = [c.rstrip(".") + t for c in cands for t in (", with addresses and websites.", ". Free iPhone app coming soon.", ", with addresses.",
                                                         ". Free iPhone app.", ", with maps.")] if lo >= 100 else []
    for o in list(cands) + more:
        if lo <= len(o) <= hi:
            return o
        seen.append(o)
    raise ValueError(f"nothing fits {lo}-{hi} for {what}: {[(len(o), o) for o in seen[:12]]}")


# The app icon in miniature (scripts/make-brand.swift, same geometry, y flipped): a buttermilk biscuit, golden top and baked bottom
# with two layer lines, on flag red.
LOGO = ('<svg viewBox="0 0 64 64" width="30" height="30" aria-hidden="true"><defs><clipPath id="lg-b">'
        '<path d="M9.6 40.96Q9.6 46.08 14.72 46.08H49.28Q54.4 46.08 54.4 40.96V26.88C54.4 20.48 44.8 17.92 32 17.92C19.2 17.92 9.6 20.48 9.6 26.88Z"/>'
        '</clipPath></defs><rect width="64" height="64" rx="14" fill="#B31942"/>'
        '<g clip-path="url(#lg-b)"><rect width="64" height="64" fill="#F3D9A6"/><rect y="43.2" width="64" height="20.8" fill="#D69443"/>'
        '<rect width="64" height="26.56" fill="#D69443"/></g>'
        '<path d="M14.08 37.44H49.92M14.08 32H49.92" stroke="#E4B871" stroke-width="2.3" stroke-linecap="round"/></svg>')
FAVICON = "data:image/svg+xml," + LOGO.replace('width="30" height="30" ', "").replace(' aria-hidden="true"', "").replace("<svg ", "<svg xmlns='http://www.w3.org/2000/svg' ").replace('"', "'").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")

# Nick's palette (2026-10-26): the North Carolina flag. Navy #13294B for text and accents (14.5:1 on white), red #B31942 as a fill under
# white text (6.7:1) and for small accents, a cool #F3F5FA page tint, soft red #F6DCE2 for tags. Lettering: condensed heavy system faces
# for headings, the system monospaced face for numbers; no web fonts are loaded (the CSP allows only this site).
CSS = """
  :root {
    --bg: #f3f5fa; --surface: #fff; --surface2: #e6ebf3; --rule: #dce2ec;
    --ink: #0f1b33; --ink2: #28375a; --muted: #566079;
    --accent: #13294b; --accent2: #2a4570; --on-accent: #fff; --orange: #b31942; --on-orange: #fff; --lime: #d69443; --soft: #f6dce2; --limesoft: #f3d9a6;
    --focus: #b31942;
    --radius: 16px;
    --display: "Avenir Next Condensed", "Helvetica Neue Condensed", "Roboto Condensed", "Arial Narrow", system-ui, sans-serif;
    --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #0b1426; --surface: #111e38; --surface2: #172747; --rule: #263a63; --ink: #eef2fa; --ink2: #d3dcef; --muted: #a9b6d0; --accent: #a9c0f0; --accent2: #c6d6f6; --on-accent: #0b1426; --focus: #ff8aa4; }
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  @media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 17px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
  a { color: var(--accent); text-underline-offset: 2px; }
  a:focus-visible, summary:focus-visible, button:focus-visible, select:focus-visible, input:focus-visible, [tabindex]:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; border-radius: 6px; }
  .skip { position: absolute; left: -9999px; top: 0; background: var(--orange); color: var(--on-orange); padding: 10px 14px; font-weight: 700; z-index: 10; }
  .skip:focus { left: 8px; top: 8px; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 0 20px; }
  header.site { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 18px 0 14px; }
  .stripes { display: block; margin: 0 0 4px; border-radius: 4px; overflow: hidden; line-height: 0; }
  .stripes svg { display: block; width: 100%; height: 20px; }
  .stripes .sky { fill: var(--surface2); }   /* the sky behind the ridges follows the theme */
  .logo { display: flex; align-items: center; gap: 10px; font: 800 24px/1 var(--display); text-transform: uppercase; letter-spacing: .01em; color: var(--accent); text-decoration: none; }
  .logo svg { flex: 0 0 auto; border-radius: 7px; }
  header.site nav { display: flex; flex-wrap: wrap; gap: 4px 16px; justify-content: flex-end; }
  header.site nav a { color: var(--ink2); text-decoration: none; font-size: 15px; }
  header.site nav a:hover { color: var(--accent); text-decoration: underline; }
  h1, h2 { font-family: var(--display); font-weight: 800; color: var(--accent); letter-spacing: -.005em; }
  h1 { font-size: clamp(40px, 8.5vw, 64px); line-height: .95; margin: 0 0 18px; text-transform: uppercase; overflow-wrap: break-word; text-shadow: 3px 3px 0 var(--orange); }
  .kicker { font: 600 13px/1.4 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--accent); margin: 0 0 12px; }
  .kicker::before { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--orange); margin: 0 8px 1px 0; }
  h2 { font-size: 34px; line-height: 1.02; margin: 0 0 10px; text-transform: uppercase; }
  h3 { font-size: 18px; margin: 0; line-height: 1.3; }
  .lede { font-size: 19px; color: var(--ink2); margin: 0 0 26px; }
  .hero { padding: 44px 0 28px; }
  section { padding: 36px 0; border-top: 1px solid var(--rule); }
  section.hero { border: 0; }
  .sub { color: var(--ink2); margin: 0 0 22px; }
  .cta-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .btn { display: inline-flex; align-items: center; gap: 10px; background: var(--orange); color: var(--on-orange); font-weight: 700; padding: 14px 20px; border-radius: 14px; text-decoration: none; font-size: 17px; }
  .btn-ghost { background: transparent; color: var(--accent); border: 2px solid var(--accent); }
  .pill { font-size: 14px; color: var(--muted); }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 28px 0 0; padding: 0; list-style: none; }
  .stats li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px; }
  .stats b { display: block; font: 600 28px/1 var(--mono); color: var(--accent); }
  .stats span { font-size: 14px; color: var(--muted); }
  .steps { display: grid; gap: 12px; list-style: none; margin: 0; padding: 0; }
  .step { display: flex; gap: 14px; background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px; }
  .step .n { flex: 0 0 32px; height: 32px; border-radius: 50%; background: var(--orange); color: var(--on-orange); font-weight: 800; display: grid; place-items: center; }
  .step p { margin: 4px 0 0; color: var(--ink2); }
  .shots { display: flex; gap: 14px; overflow-x: auto; margin: 0 -20px; padding: 4px 20px 14px; scroll-snap-type: x proximity; list-style: none; }
  .shots li { flex: 0 0 auto; width: 210px; scroll-snap-align: start; }
  .shots img { display: block; width: 210px; height: auto; border-radius: 24px; border: 1px solid var(--rule); background: var(--surface2); }
  .shots p { font-size: 14px; color: var(--muted); margin: 8px 2px 0; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .card { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px; }
  .card h3 { font: 800 21px/1.1 var(--display); text-transform: uppercase; letter-spacing: .01em; }
  a.card.gc { display: flex; flex-direction: column; gap: 6px; border: 0; border-radius: 18px; min-height: 150px; }
  a.card.gc b { font: 600 32px/1 var(--mono); margin-bottom: auto; }
  a.card.gc p, a.card.gc h3 { color: inherit; }
  a.card.gc p { opacity: .92; }
  a.card.gc.gc-bbqeast, a.card.gc.gc-bbqlex, a.card.gc.gc-hotdogs, a.card.gc.gc-calabash, a.card.gc.gc-biscuits, a.card.gc.gc-moravian { background: #b31942; color: #fff; }
  a.card.gc.gc-oldest, a.card.gc.gc-honors, a.card.gc.gc-inspections { background: #13294b; color: #fff; }
  .card p { margin: 6px 0 0; color: var(--ink2); }
  a.card { display: block; text-decoration: none; color: var(--ink); }
  a.card:hover h3 { text-decoration: underline; color: var(--accent); }
  .cities { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; margin: 0; }
  .cities a { display: inline-block; padding: 8px 12px; border-radius: 999px; border: 1px solid var(--rule); background: var(--surface); text-decoration: none; color: var(--ink); font-size: 15px; }
  .cities a:hover { border-color: var(--accent); }
  .cities a[aria-current] { border-color: var(--accent); font-weight: 700; }
  details { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 2px 18px; margin-bottom: 10px; }
  summary { cursor: pointer; padding: 14px 0; font-weight: 600; list-style: none; display: flex; justify-content: space-between; gap: 12px; }
  summary::-webkit-details-marker { display: none; }
  summary::after { content: "+"; color: var(--accent); font-weight: 800; }
  details[open] summary::after { content: "\\2013"; }
  details p { margin: 0 0 16px; color: var(--ink2); }
  .final { text-align: center; }
  .final .cta-row { justify-content: center; }
  nav.crumbs { font-size: 14px; color: var(--muted); padding: 16px 0 0; }
  nav.crumbs ol { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
  nav.crumbs li + li::before { content: "/"; margin-right: 6px; color: var(--rule); }
  nav.crumbs a { color: var(--muted); }
  .places { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
  .places li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px 16px; min-width: 0; overflow-wrap: anywhere; scroll-margin-top: 12px; }
  .places li:target { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }
  .places .where { margin: 2px 0 0; font-size: 15px; color: var(--muted); }
  .places .facts { margin: 8px 0 0; font-size: 15px; color: var(--ink2); }
  .places .facts b { color: var(--ink); font-weight: 600; }
  .places .note { margin: 6px 0 0; font-size: 15px; color: var(--ink2); }
  .places .fine { margin: 6px 0 0; }
  .places .link { font-size: 14px; margin: 6px 0 0; }
  .tag { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; background: var(--soft); color: #5c0a22; border-radius: 6px; padding: 1px 6px; margin: 0 4px 2px 0; }
  .tag-mi { background: #b31942; color: #fff; }
  .tag-jb { background: #13294b; color: #fff; }
  .tag-plain { background: #e6ebf3; color: #0f1b33; }
  .grades { list-style: none; padding: 0; margin: 0 0 16px; display: flex; flex-wrap: wrap; gap: 10px 24px; }
  .grades li { display: flex; align-items: center; gap: 8px; }
  .card-grade { display: inline-grid; place-items: center; min-width: 30px; height: 30px; padding: 0 6px; border: 2px solid #111; background: #fff; color: #111; font: 800 18px/1 var(--display); border-radius: 4px; }
  .toc { columns: 2; padding-left: 20px; margin: 0; }
  table { border-collapse: collapse; width: 100%; font-size: 15px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--rule); vertical-align: top; }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  .tbl { overflow-x: auto; }
  .res { display: inline-block; font: 800 12px/1.4 -apple-system, system-ui, sans-serif; letter-spacing: .04em; text-transform: uppercase; padding: 2px 6px; border-radius: 6px; }
  .res-ok { background: #ddefe3; color: #0e5a2b; } .res-mid { background: #ffe9c2; color: #6b3a00; } .res-low { background: #f9d5db; color: #7a0019; }
  .groups { list-style: none; padding: 0; margin: 0 0 18px; display: grid; gap: 12px; }
  .groups > li { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 14px 16px; }
  .groups ul { margin: 8px 0 0; padding-left: 20px; color: var(--ink2); font-size: 15px; }
  .groups .count { margin: 8px 0 0; font-weight: 600; }
  .fine { font-size: 14px; color: var(--muted); }
  .legal h2 { font-size: 26px; margin-top: 28px; }
  .legal p, .legal li { color: var(--ink2); }
  footer { padding: 32px 0 56px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--rule); margin-top: 20px; }
  footer nav { display: flex; flex-wrap: wrap; gap: 8px 16px; }
  footer a { color: var(--muted); }
  footer p { margin: 12px 0 0; }
  @media (max-width: 600px) {
    .grid2 { grid-template-columns: 1fr; }
    .stats { grid-template-columns: 1fr 1fr; }
    .toc { columns: 1; }
    .toc a { display: inline-block; padding: 3px 0; }
    header.site { flex-direction: column; align-items: flex-start; }
    header.site nav { justify-content: flex-start; }
    header.site nav a, footer nav a, nav.crumbs a { display: inline-block; padding: 10px 0; }
    footer nav { gap: 0 18px; }
    th, td { padding: 8px 4px; font-size: 14px; }
    .tbl th, .tbl td { padding: 8px 3px; font-size: 13px; }
    .res { font-size: 11px; letter-spacing: .02em; padding: 2px 4px; }
    nav.crumbs ol { align-items: center; }
  }
"""


def jsonld(obj):
    big = obj.get("@type") == "ItemList"
    raw = json.dumps(obj, ensure_ascii=False, indent=None if big else 1, separators=(",", ":") if big else None)
    return '<script type="application/ld+json">\n' + raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026") + "\n</script>"


def crumbs(trail):
    """trail: [(name, url)] ending with the current page."""
    items = "".join(f'<li><a href="{u}">{e(n)}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{e(n)}</li>'
                    for i, (n, u) in enumerate(trail))
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u} for i, (n, u) in enumerate(trail)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>', ld


def store_button(label="Ask for early access"):
    # A plain mailto button until launch: no Apple logo (Apple's marketing rules allow it only in the official badge). When
    # APP_STORE_URL is set in page() below, swap this for Apple's "Download on the App Store" badge artwork. Only Nick's internal
    # TestFlight group exists (2026-10-13): the mailto asks, and no page copy promises an invite or a link.
    return (f'<a class="btn store-btn" href="mailto:{EMAIL}?subject=North%20Carolina%20Eats%20early%20access&amp;body=Send%20me%20the%20TestFlight%20link.">'
            f'<span class="store-label">{label}</span></a>')


STORE_NOTE = "The free North Carolina Eats app for iPhone and iPad is on its way to the App Store."


def sha256_src(s):
    return "'sha256-" + base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode() + "'"


def csp_for(doc):
    """A strict policy for one finished page: only its own inline <script>/<style> blocks (by hash), same-origin data and images."""
    scripts = re.findall(r"<script>(.*?)</script>", doc, re.S)          # executable inline scripts (JSON-LD blocks are data, not run)
    styles = re.findall(r"<style>(.*?)</style>", doc, re.S)
    return ("default-src 'none'; "
            f"script-src {' '.join(sha256_src(s) for s in scripts) or chr(39) + 'none' + chr(39)}; "
            f"style-src {' '.join(sha256_src(s) for s in styles) or chr(39) + 'none' + chr(39)}; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'")


CSP_SLOT = "__CSP__"
written, noindexed = [], []
NAV = [("/eastern-north-carolina-barbecue.html", "Eastern BBQ"), ("/lexington-barbecue.html", "Lexington BBQ"),
       ("/north-carolina-restaurant-grades.html", "Grades"), ("/cities/", "Cities"), ("/explore/", "Search")]
# from Murphy to Manteo: Blue Ridge ridges at the left easing into the coastal plain and the dunes at the right, three navy shades over
# a red rule (the app's Home band and the share image's horizon, flattened to 20 px)
RAYS = ('<svg viewBox="0 0 1200 20" preserveAspectRatio="none" aria-hidden="true"><rect class="sky" x="0" y="0" width="1200" height="20"/>'
        '<path d="M0 20V9L60 3 115 8 170 1 230 8 290 4 350 10 420 8 520 12 640 10 760 13 900 12 1040 14 1200 13V20Z" fill="#5d7aa6"/>'
        '<path d="M0 20V12L70 7 130 11 190 6 250 11 320 9 400 13 520 13 660 14 820 14 980 15 1120 15 1200 15V20Z" fill="#2a4570"/>'
        '<path d="M0 20V15L120 12 260 14 420 15 620 16 800 16 960 16.5 1060 16 1110 16.5 1150 16 1200 16.5V20Z" fill="#13294b"/>'
        '<rect x="0" y="17" width="1200" height="3" fill="#b31942"/></svg>')


def page(path, title, desc, body, lds=(), robots="index,follow,max-image-preview:large", og_alt=None, extra_css="", og_type="article"):
    assert 50 <= len(title) <= 60 or path == "404.html", (path, len(title), title)
    assert 140 <= len(desc) <= 160 or path == "404.html", (path, len(desc), desc)
    assert body.count("<h1") == 1, path
    assert 'style="' not in body, f"{path}: inline style attributes break the CSP"
    url = DOMAIN + "/" + ("" if path == "index.html" else path.removesuffix("index.html"))
    indexed = "noindex" not in robots
    if not any("parentOrganization" in json.dumps(x) for x in lds):   # every page names its publisher and the Eats Ranked parent
        lds = list(lds) + [{"@context": "https://schema.org", **ORG_REF}]
    og_alt = og_alt or f"{BRAND}: {TAGLINE}. North Carolina restaurants, with hand-checked Eastern and Lexington barbecue, hot dogs and biscuits."
    ld = "\n".join(jsonld(x) for x in lds)
    canon = f'<link rel="canonical" href="{url}">\n' if indexed else ""
    og_url = f'<meta property="og:url" content="{url}">\n' if indexed else ""
    nav = "\n".join(f'      <a href="{u}">{t}</a>' for u, t in NAV)
    doc = f"""<!DOCTYPE html>
<html lang="en" data-base="{BASE}">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{CSP_SLOT}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{canon}<meta name="robots" content="{robots}">
<meta name="theme-color" content="#13294b">
<!-- Smart App Banner: once the App Store Connect record exists, replace APP_ID with the numeric Apple ID and uncomment.
<meta name="apple-itunes-app" content="app-id=APP_ID">
-->
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
{og_url}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DOMAIN}/og.png">
<link rel="icon" type="image/svg+xml" href="{FAVICON}">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<style>{CSS}{extra_css}</style>
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="wrap">
  <header class="site">
    <a class="logo" href="/" aria-label="{BRAND} home">{LOGO}{BRAND}</a>
    <nav aria-label="Main">
{nav}
    </nav>
  </header>
  <div class="stripes" aria-hidden="true">{RAYS}</div>
{body}
  <footer>
    <nav aria-label="Footer">
      <a href="/">{BRAND} app</a>
      <a href="/explore/">Search North Carolina restaurants</a>
{chr(10).join(f'      <a href="{u}">{e(t)}</a>' for u, t in GUIDE_LINKS)}
      <a href="/cities/">Cities and towns</a>
      <a href="/privacy.html">Privacy policy</a>
      <a href="/terms.html">Terms of use</a>
      <a href="mailto:{EMAIL}">Email us</a>
    </nav>
    <p>{SOURCES_LINE}</p>
    <p>© 2026 {BRAND}. Part of <a href="{HUB['url']}" rel="noopener">Eats Ranked</a>, restaurant apps state by state.</p>
    <p>Created by <a href="https://work-with-nick.com/" rel="author">Nick Soderstrom</a>.</p>
  </footer>
</div>
<script>
  // Once the App Store listing exists, paste its URL here (looks like https://apps.apple.com/app/id123456789).
  // Every button switches from "Ask for early access" to "Download on the App Store" automatically (then use Apple's badge artwork,
  // see store_button() in scripts/make-site.py). Also fill in the apple-itunes-app meta tag in <head> on every page, and put the
  // MobileApplication "offers" back in the landing page's JSON-LD (re-run scripts/make-site.py after editing it there).
  var APP_STORE_URL = "";
  if (APP_STORE_URL) {{
    document.querySelectorAll(".store-btn").forEach(function (b) {{ b.href = APP_STORE_URL; b.rel = "noopener"; }});
    document.querySelectorAll(".store-label").forEach(function (l) {{ l.textContent = "Download on the App Store"; }});
    document.querySelectorAll(".store-note").forEach(function (n) {{ n.textContent = "Free for iPhone and iPad."; }});
  }}
</script>
</body>
</html>
"""
    if BASE:   # served under /north-carolina-eats/: every root-relative link and asset gets the prefix
        doc = re.sub(r'(href|src|srcset)="/', rf'\1="{BASE}/', doc)
    doc = doc.replace(CSP_SLOT, csp_for(doc), 1)   # hashed last, over the exact bytes the browser will see
    os.makedirs(os.path.dirname(f"{DOCS}/{path}"), exist_ok=True)
    open(f"{DOCS}/{path}", "w").write(doc)
    (written if indexed else noindexed).append(path)
    return path


class Anchors:
    """Gives each place an id (name-zip) the first time it appears on a page, so ItemList items can point to page#id."""
    RESERVED = {"main", "about", "list", "honors", "oldest", "inspections", "cuisines", "more", "towns", "how", "what", "guides", "cities",
                "faq", "download", "screens", "pricing", "privacy", "groups", "counties", "lookup", "closures", "tiers", "lg-r", "lg-f", "lg-p",
                "lg-b", "cities-list", "grades", "wake", "portal"} | {k for k, _ in ALL_GUIDES}

    def __init__(self, page_url):
        self.page_url, self.used, self.of = page_url, set(self.RESERVED), {}

    def take(self, p):
        if id(p) in self.of:
            return None
        base = slug(p.name + (" " + p.zip if p.zip else "")) or "place"
        a, n = base, 2
        while a in self.used:
            a, n = f"{base}-{n}", n + 1
        self.used.add(a)
        self.of[id(p)] = a
        return a

    def url(self, p):
        return f"{self.page_url}#{self.of[id(p)]}"


CHIPS = [(BBQEAST, "Eastern whole hog"), (BBQLEX, "Lexington barbecue"), (HOTDOG, "Carolina hot dogs"), (CALABASH, "Calabash seafood"),
         (BISCUIT, "Biscuits &amp; livermush"), (MORAVIAN, "Moravian bakery")]


def place_item(p, anchors=None, show_fn=False, honors=False):
    facts = []
    if p.dishes:
        facts.append(f"<b>On the menu:</b> {e(p.dishes)}")
    if p.founded:
        facts.append(f"<b>Since</b> {e(str(p.founded))}")
    if p.season:
        facts.append(f"<b>Season:</b> {e(p.season)}")
    kinds = []
    if p.mi:
        kinds.append(('<span class="tag tag-mi">', e(MI[p.mi])))
    if p.jb_label():
        kinds.append(('<span class="tag tag-jb">', e(p.jb_label())))
    if p.hc:
        kinds += [('<span class="tag">', k) for t, k in CHIPS if p.tags & t]
    where = ", ".join(x for x in (p.addr, p.city) if x)
    aid = anchors.take(p) if anchors else None
    out = [f'<li id="{e(aid)}">' if aid else "<li>", f"<h3>{e(p.name)}</h3>", f'<p class="where">{e(where)}</p>']
    if kinds or facts:
        out.append('<p class="facts">' + "".join(f"{tag}{k}</span>" for tag, k in kinds) + (" " + " · ".join(facts) if facts else "") + "</p>")
    if p.note:
        out.append(f'<p class="note">{e(p.note)}</p>')
    if show_fn and p.fn:
        out.append(f'<p class="fine">{e(p.fn)}</p>')
    if honors and p.jbf:   # restaurateur-level honors have no chip, so say what the honor is
        out.append('<p class="fine">' + e("; ".join("James Beard: " + x for x in p.jbf.split("; "))) + "</p>")
    if p.site:
        host = re.sub(r"^https?://(www\.)?", "", p.site, flags=re.I).split("/")[0]
        out.append(f'<p class="link"><a href="{e(p.site)}" rel="noopener nofollow">{e(host)}</a></p>')
    out.append("</li>")
    return "".join(out)


def restaurant_ld(p, item_url):
    addr = {"@type": "PostalAddress"}
    if p.addr:
        addr["streetAddress"] = p.addr
    if p.city:
        addr["addressLocality"] = p.city
    addr["addressRegion"] = "NC"
    if p.zip:
        addr["postalCode"] = p.zip
    addr["addressCountry"] = "US"
    x = {"@type": "Restaurant", "name": p.name, "url": item_url, "address": addr}
    if p.lat is not None and p.lon is not None:
        x["geo"] = {"@type": "GeoCoordinates", "latitude": p.lat, "longitude": p.lon}
    if p.site:
        x["sameAs"] = p.site
    if p.founded:
        x["foundingDate"] = str(p.founded)
    if p.cuisine and p.cuisine not in ("Other", "Restaurant", "American & Other"):
        x["servesCuisine"] = p.cuisine
    return x


def item_list(name, places, url, anchors):
    """An all-on-one-page list: each item's url is its anchor on this page; the restaurant's own site goes in sameAs."""
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "url": url, "numberOfItems": len(places),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": restaurant_ld(p, anchors.url(p))} for i, p in enumerate(places)]}


def article_ld(url, headline, desc):
    return {"@context": "https://schema.org", "@type": "Article", "headline": headline, "description": desc,
            "datePublished": PUBLISHED, "dateModified": TODAY, "inLanguage": "en", "mainEntityOfPage": url,
            "image": f"{DOMAIN}/og.png", "author": ORG_REF, "publisher": ORG_REF}


# ---------------------------------------------------------------- counts shared by several pages
N_REST = len(REST)
N_TOWNS = len({p.city for p in REST if p.city})
N_COUNTIES = len({p.county for p in REST if p.county})
N_OFFICIAL = sum(1 for p in REST if p.r.get("t") == 2)
N_HC = len(HC_ANY)
MI_N = Counter(p.mi for p in HON_L if p.mi)
MI_COUNT = {MI[k]: v for k, v in sorted(MI_N.items())}
N_JBF = sum(1 for p in HON_L if p.jbf)
N_CLASSICS = sum(1 for p in HON_L if p.h & 1)
INS_PATH = "north-carolina-restaurant-grades.html"
HON_PATH = "north-carolina-michelin-james-beard.html"
OLD_PATH = "north-carolina-oldest-restaurants.html"
GUIDE_PATH = {"bbqeast": "eastern-north-carolina-barbecue.html", "bbqlex": "lexington-barbecue.html", "hotdogs": "carolina-hot-dogs.html",
              "calabash": "calabash-seafood.html", "biscuits": "north-carolina-biscuits-livermush.html", "moravian": "moravian-bakeries.html"}
GUIDE_NAME = {"bbqeast": "Eastern whole hog barbecue", "bbqlex": "Lexington barbecue", "hotdogs": "Carolina hot dogs",
              "calabash": "Calabash seafood", "biscuits": "Biscuits & livermush", "moravian": "Moravian bakeries"}
GUIDE_LINKS = ([("/" + GUIDE_PATH[k], GUIDE_NAME[k]) for k, _ in GUIDE_TAGS]
               + ([("/" + OLD_PATH, "Oldest restaurants")] if HAS_OLD else [])
               + [("/" + HON_PATH, "MICHELIN & James Beard"), ("/" + INS_PATH, "Restaurant grades, explained")])

SOURCES_LINE = (f"Place data: hand-checked research by {BRAND} ({CHECKED}); Wake County Environmental Health & Safety's food service permits "
                f"and food inspections (Wake County Open Data, CC BY 4.0, retrieved {PERMITS_UPDATED}, inspections through {hdate(INS_THROUGH)}); "
                "Overture Maps Foundation places (CDLA Permissive 2.0) and addresses (open address sources under "
                "permissive licenses, docs.overturemaps.org/attribution); map outlines © OpenStreetMap contributors, Overture Maps Foundation (ODbL). "
                "Not affiliated with or endorsed by the State of North Carolina, NC DHHS, Wake County or any other county, any restaurant or "
                "chain, the MICHELIN Guide or the James Beard Foundation. MICHELIN "
                "and the MICHELIN Guide are trademarks of Michelin; James Beard Foundation and James Beard Award are trademarks of the James Beard "
                "Foundation. Places open and close, so check before you go.")


def by_region(places, key=lambda p: (p.city, p.name.lower())):
    groups = defaultdict(list)
    for p in places:
        groups[p.region or "Elsewhere"].append(p)
    order = REGION_ORDER + ["Elsewhere"]
    return [(REGION_NAME.get(r, "Elsewhere in North Carolina"), sorted(groups[r], key=key)) for r in order if groups.get(r)]


def region_sections(places, noun, plural_noun, anchors, **item_kw):
    toc = '<ul class="toc">' + "".join(f'<li><a href="#{slug(r)}">{e(r)}</a> ({len(ps)})</li>' for r, ps in by_region(places)) + "</ul>"
    secs = []
    for r, ps in by_region(places):
        anchors.used.update({slug(r), "h-" + slug(r)})
        secs.append(f'<section id="{slug(r)}" aria-labelledby="h-{slug(r)}"><h2 id="h-{slug(r)}">{e(r)}</h2>'
                    f'<p class="sub">{plural(len(ps), noun, plural_noun)}, by town.</p><ol class="places">'
                    + "".join(place_item(p, anchors, **item_kw) for p in ps) + "</ol></section>")
    return toc, "\n".join(secs)


# ---------------------------------------------------------------- city pages: which towns get one
CITY_WANTED = ["Raleigh", "Charlotte", "Asheville", "Durham", "Greensboro", "Winston-Salem", "Chapel Hill", "Carrboro", "Cary", "Lexington",
               "Greenville", "Wilmington", "Fayetteville", "High Point", "Shelby", "Calabash", "Ayden", "Knightdale", "Burlington", "Boone",
               "Hendersonville", "Concord", "Davidson", "Cornelius", "Pittsboro", "Salisbury", "Wake Forest", "Apex", "Morrisville"]
MIN_LISTED = 4   # hand-checked, honored or oldest places in the town itself: fewer, and the town gets no page yet


def town_listed(c):
    return [p for p in REST if p.city == c and ((p.hc and p.tags) or p.mi or p.jbf)]


CITY_PAGES = [c for c in CITY_WANTED if any(p.city == c and p.lat is not None for p in REST) and len(town_listed(c)) >= MIN_LISTED]
CITY_SKIPPED = {c: len(town_listed(c)) for c in CITY_WANTED if c not in CITY_PAGES}


def city_url(c):
    return f"/cities/{slug(c)}.html"


def city_links(current=None):
    return '<ul class="cities">' + "".join(f'<li><a href="{city_url(c)}"{" aria-current=" + chr(34) + "page" + chr(34) if c == current else ""}>{e(c)}</a></li>'
                                           for c in CITY_PAGES) + "</ul>"


def other_guides(skip):
    return "Other guides: " + ", ".join(f'<a href="{u}">{e(t)}</a>' for u, t in GUIDE_LINKS if u != skip) + "."


def guide_page(path, h1, kicker, title_opts, desc_opts, lede, about_html, places, noun, plural_noun, list_name, region=True, **item_kw):
    url = f"{DOMAIN}/{path}"
    # counts are small or large enough that the written lengths can miss the 140-160 window: each option also gets fixed tails
    tails = (", with addresses and websites.", ", with each place's address and website.", ". Free iPhone app coming soon.", ", with addresses.",
             ". Free iPhone app.", ", with maps.")
    desc_opts = list(desc_opts) + [d.rstrip(".") + t for d in desc_opts for t in tails]
    title_opts = list(title_opts) + [t + f" | {BRAND}" for t in title_opts if BRAND not in t]
    title, desc = fit(title_opts, 50, 60, path + " title"), fit(desc_opts, 140, 160, path + " description")
    nav, bc = crumbs([("Home", "/"), (h1, "/" + path)])
    anchors = Anchors(url)
    if region:
        toc, secs = region_sections(places, noun, plural_noun, anchors, **item_kw)
        jump = f"<h2>Jump to a region</h2>\n    {toc}"
    else:
        secs = (f'<section id="list" aria-labelledby="h-list"><h2 id="h-list">Oldest first</h2><ol class="places">'
                f'{"".join(place_item(p, anchors, **item_kw) for p in places)}</ol></section>')
        jump = ""
    body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{kicker}</p>
    <h1>{e(h1)}</h1>
    <p class="lede">{lede}</p>
    <div class="cta-row">{store_button()}<span class="pill store-note">{STORE_NOTE}</span></div>
  </section>
  <section id="about">
    {about_html}
    <p class="fine">{other_guides("/" + path)} City pages: {", ".join(f'<a href="{city_url(c)}">{e(c)}</a>' for c in CITY_PAGES)}.</p>
    {jump}
  </section>
{secs}
  </main>"""
    page(path, title, desc, body, [article_ld(url, h1, desc), bc, item_list(list_name, places, url, anchors)])


def towns_text(places, k):
    return join_words([t for t, _ in Counter(p.city for p in places).most_common(k)])


def towns_counts(places, k=8):
    return ", ".join(f"{t} ({n})" for t, n in Counter(p.city for p in places).most_common(k))


def top_dishes(places, k=6, skip=()):
    c = Counter()
    for p in places:
        # sorted: a set's order changes from run to run, and ties in most_common() would reorder the copy on every rebuild
        for d in sorted({x.strip().lower() for x in re.split(r"[;,]", p.r.get("dish") or "") if x.strip()}):
            if d not in skip:
                c[d] += 1
    return ", ".join(f"{d} ({n})" for d, n in c.most_common(k) if n > 1)


HOW_BUILT = ("Our method: a place made the list only if a 2025 or 2026 source backed it up (its own site or menu, a dated local news "
             "story, a Wake County inspection, the MICHELIN Guide or a current listing by the state's or the town's tourism office) and its "
             "street address matched. No current source, or a website gone dark, and it stayed off. Review sites played no part, and places "
             "run by region and town rather than by anybody's score. Barbecue joints often close early or when the meat runs out, so check "
             "before you drive.")
APP_LINE = (f"On your phone, {BRAND} orders this list by how far each place is from you, and a tap opens Apple Maps' live card with "
            "hours, photos and directions.")


def checked_kicker():
    return f"{BRAND} · checked by hand, {CHECKED}"


def seasonal_line(places):
    n = sum(1 for p in places if p.season)
    return f" {plural(n, 'place')} on this list {'notes a season' if n == 1 else 'note a season'}; seasonal is not closed." if n else ""


# ---------------------------------------------------------------- the hand-checked guides (each once it holds MIN_GUIDE places)
assert all(len(v) > 1 for v in L.values()), "the guide copy writes plural nouns"


def guide(k, h1, titles, descs, lede, about, list_name, noun="place"):
    G = L[k]
    plural_noun = noun[:-1] + "ies" if noun.endswith("y") else noun + "s"
    dishes = top_dishes(G)
    guide_page(GUIDE_PATH[k], h1, checked_kicker(), titles, descs, lede, about + f"""
    <h2>The list at a glance</h2>
    <p>Towns with the most: {e(towns_counts(G))}.{(" The dishes we found most often: " + e(dishes) + ".") if dishes else ""}</p>
    <p>{HOW_BUILT}</p>
    <p>{APP_LINE}</p>""", G, noun, plural_noun, list_name)


def towns_phrase(G, k=3):
    """"Greenville, Raleigh, Ayden and 2 other towns": the towns with the most places on a list, then how many more."""
    towns = [t for t, _ in Counter(p.city for p in G if p.city).most_common()]
    if len(towns) <= k:
        return join_words(towns)
    return ", ".join(towns[:k]) + " and " + plural(len(towns) - k, "other town")


def classic_line(G):
    """The guide's America's Classics, named by the James Beard Foundation (a fact we can source), or nothing."""
    ac = [p for p in G if p.h & 1]
    return (f" {join_words([f'{e(p.name)} in {e(p.city)}' for p in ac])} {'is a' if len(ac) == 1 else 'are'} James Beard America's "
            f"Classic{'' if len(ac) == 1 else 's'}.") if ac else ""


if "bbqeast" in L:
    G = L["bbqeast"]
    guide("bbqeast", "Eastern North Carolina whole hog",
          [f"Eastern North Carolina Barbecue: {len(G)} Hand-Checked Pits", f"Eastern NC Whole Hog Barbecue: {len(G)} Places | {BRAND}",
           f"Eastern North Carolina Whole Hog: {len(G)} Checked Places"],
          [f"{plural(len(G), 'place')} for Eastern North Carolina whole hog barbecue, chopped and dressed with vinegar and pepper, each checked in {CHECKED} against a 2025–26 source.",
           f"Eastern North Carolina barbecue: {plural(len(G), 'place')} cooking the whole hog in {towns_phrase(G, 3)}, each checked in {CHECKED} against a 2025–26 source."],
          f"{plural(len(G), 'place')} in the east of the state that cook the whole hog and season the chopped pork with a thin vinegar-and-pepper sauce, in {e(towns_phrase(G))}. Each was checked in {CHECKED} against a 2025–26 source.",
          f"""<h2>The whole hog</h2>
    <p>East of Raleigh, barbecue means the whole hog, cooked low and slow, chopped (at some pits with bits of crisp skin mixed back in) and dressed with vinegar, salt and red and black pepper. There's no tomato in the sauce. Coleslaw and cornbread or hushpuppies come alongside.{classic_line(G)}</p>""",
          "Eastern North Carolina whole hog barbecue", "place")

if "bbqlex" in L:
    G = L["bbqlex"]
    guide("bbqlex", "Lexington barbecue",
          [f"Lexington-Style Barbecue: {len(G)} Hand-Checked Piedmont Pits", f"Lexington & Piedmont Barbecue: {len(G)} Checked | {BRAND}",
           f"Lexington Barbecue: {len(G)} Hand-Checked Places | {BRAND}"],
          [f"{plural(len(G), 'Piedmont pit')} for Lexington-style barbecue: pork shoulder with red dip and red slaw, each checked in {CHECKED} against a 2025–26 source, by town.",
           f"Lexington barbecue: {plural(len(G), 'place')} for pit-cooked pork shoulder, dip and red slaw in {towns_phrase(G, 3)}, each checked in {CHECKED} against a 2025–26 source."],
          f"{plural(len(G), 'place')} for Piedmont barbecue: pork shoulders cooked slowly, chopped or sliced, with a vinegar-and-tomato dip and red slaw, in {e(towns_phrase(G))}. Each was checked in {CHECKED} against a 2025–26 source.",
          f"""<h2>Shoulders, dip and red slaw</h2>
    <p>West of the Triangle, the Piedmont cooks pork shoulders rather than whole hogs, at the old places over hardwood coals, and serves them chopped, coarse-chopped or sliced. The sauce, called dip, is vinegar with tomato or ketchup and pepper, and the slaw is red: cabbage dressed with the same dip instead of mayonnaise. Lexington, in Davidson County, gave the style its name.{classic_line(G)}</p>""",
          "Lexington and Piedmont barbecue", "place")

if "hotdogs" in L:
    G = L["hotdogs"]
    guide("hotdogs", "Carolina hot dogs",
          [f"Carolina Hot Dogs All the Way: {len(G)} Hand-Checked Places", f"North Carolina Hot Dogs: {len(G)} Hand-Checked Places",
           f"Carolina Hot Dogs: {len(G)} Checked Stands | {BRAND}"],
          [f"{plural(len(G), 'place')} for a Carolina hot dog all the way: chili, slaw, onions and mustard, in {towns_phrase(G, 2)}, each checked in {CHECKED} against a 2025–26 source.",
           f"Carolina hot dogs: {plural(len(G), 'stand')} and counters serving dogs all the way, with chili, slaw, onions and mustard, each checked in {CHECKED} against a 2025–26 source."],
          f"{plural(len(G), 'stand')} and counters for the North Carolina hot dog, ordered all the way: mustard, chili, chopped onions and coleslaw. Each was checked in {CHECKED} against a 2025–26 source.",
          """<h2>All the way</h2>
    <p>A North Carolina hot dog comes "all the way" with mustard, a fine meat chili, chopped onions and coleslaw, the slaw doing the job ketchup does elsewhere. Raleigh's Roast Grill has served hot wieners that way since 1940, and won't put ketchup on them.</p>""",
          "Carolina hot dogs", "place")

if "calabash" in L:
    G = L["calabash"]
    guide("calabash", "Calabash seafood",
          [f"Calabash Seafood: {len(G)} Hand-Checked Places | {BRAND}", f"Calabash-Style Seafood: {len(G)} Hand-Checked Restaurants"],
          [f"{plural(len(G), 'place')} for Calabash-style seafood, lightly breaded and quickly fried, in Calabash and along the coast, each checked in {CHECKED} against a 2025–26 source.",
           f"Calabash seafood: {plural(len(G), 'place')} frying shrimp, oysters and fish the Calabash way, each checked in {CHECKED} against a 2025–26 source, listed by town."],
          f"{plural(len(G), 'place')} for Calabash-style seafood: shrimp, oysters and fish in a light coating, fried quickly and served with hushpuppies. Each was checked in {CHECKED} against a 2025–26 source.",
          """<h2>Calabash style</h2>
    <p>Calabash, a fishing village at the state's southern edge, gave its name to a way of frying seafood: a light coating of flour or meal, a quick fry, and a heaping plate with hushpuppies and slaw.</p>""",
          "Calabash seafood", "place")

if "biscuits" in L:
    G = L["biscuits"]
    guide("biscuits", "North Carolina biscuits & livermush",
          [f"North Carolina Biscuits & Livermush: {len(G)} Checked Places", f"NC Biscuits & Livermush: {len(G)} Hand-Checked | {BRAND}"],
          [f"{plural(len(G), 'place')} for North Carolina biscuits and livermush, the Piedmont's fried pork-and-cornmeal breakfast, each checked in {CHECKED} against a 2025–26 source.",
           f"{plural(len(G), 'place')} for scratch biscuits and livermush in {towns_phrase(G, 3)}, each checked in {CHECKED} against a 2025–26 source, listed by region and town."],
          f"{plural(len(G), 'place')} for big scratch biscuits and for livermush, pork liver and cornmeal set in a loaf, sliced and fried crisp, in {e(towns_phrase(G))}. Each was checked in {CHECKED} against a 2025–26 source.",
          """<h2>Biscuits and livermush</h2>
    <p>Livermush is pork liver and other pork cooked with cornmeal and spices, set in a loaf, then sliced and fried. It belongs to the western Piedmont and the foothills, and Shelby holds a Liver Mush Festival. Biscuits are everywhere, from drive-thrus to sit-down biscuit kitchens.</p>""",
          "North Carolina biscuits and livermush", "place")

if "moravian" in L:
    G = L["moravian"]
    guide("moravian", "Moravian bakeries",
          [f"Moravian Bakeries: {len(G)} Hand-Checked Places | {BRAND}", f"Moravian Sugar Cake & Cookies: {len(G)} Checked Bakeries"],
          [f"{plural(len(G), 'bakery', 'bakeries')} for Moravian sugar cake and paper-thin spice cookies, in {towns_phrase(G, 2)}, each checked in {CHECKED} against a 2025–26 source.",
           f"Moravian bakeries: {plural(len(G), 'place')} for sugar cake and thin Moravian cookies, each checked in {CHECKED} against a 2025–26 source, listed by region and town."],
          f"{plural(len(G), 'bakery', 'bakeries')} for the Moravian baking of old Salem: yeasted sugar cake and spice cookies rolled paper-thin. Each was checked in {CHECKED} against a 2025–26 source.",
          """<h2>Sugar cake and thin cookies</h2>
    <p>The Moravians who founded Salem, now part of Winston-Salem, in 1766 brought their baking with them: sugar cake, a yeasted coffee cake pocked with butter and brown sugar, and spice cookies rolled paper-thin.</p>""",
          "Moravian bakeries", "bakery")

# ---------------------------------------------------------------- MICHELIN & James Beard
MI_SHORT = {5: "3-Star", 4: "2-Star", 3: "1-Star", 2: "Bib Gourmand", 1: "Recommended"}
mi_parts = [f"{words_num(MI_N[k])} {MI_SHORT[k]}" for k in (5, 4, 3, 2, 1) if MI_N.get(k)]
N_MI = sum(MI_N.values())
mi_line = (join_words(mi_parts) + (" restaurants" if N_MI != 1 else " restaurant")) if mi_parts else ""
guide_page(HON_PATH, "North Carolina MICHELIN & James Beard restaurants", f"{BRAND} · honors current as of {CHECKED}",
           [f"North Carolina MICHELIN & James Beard Restaurants", f"MICHELIN & James Beard Restaurants in North Carolina",
            f"NC MICHELIN & James Beard Restaurants | {BRAND}"],
           [f"{plural(len(HON_L), 'North Carolina restaurant')} in the MICHELIN Guide American South or honored by the James Beard Foundation, listed by region and town.",
            f"{plural(len(HON_L), 'North Carolina restaurant')} with a MICHELIN Guide distinction or a James Beard honor, from Asheville to Charlotte and Raleigh, by region and town."],
           f"{plural(len(HON_L), 'North Carolina restaurant')} recognized by MICHELIN or the James Beard Foundation. The MICHELIN Guide American South's 2026 selection lists {plural(N_MI, 'North Carolina place')} ({e(mi_line)}); {plural(N_JBF, 'place')} hold a James Beard award, a 2026 nomination or semifinalist nod, or an America's Classics award.",
           f"""<h2>What counts as an honor here</h2>
    <p>Two sources, both reported as facts rather than scores. One is the MICHELIN Guide American South, which first covered North Carolina in 2025 and revealed its 2026 selection in October 2026, as MICHELIN lists it. The other is the James Beard Foundation: its winners, its 2026 nominees and semifinalists, and America's Classics awards from any year ({plural(N_CLASSICS, 'place')}). Semifinalists are labeled as exactly that, and where an honor went to a chef, the line under the place says so. Reader polls, "best of" roundups and review-site stars don't count.</p>
    <p class="fine">MICHELIN and the MICHELIN Guide are trademarks of Michelin. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. {BRAND} is not affiliated with either.</p>""",
           HON_L, "restaurant", "restaurants", "North Carolina MICHELIN Guide and James Beard restaurants", honors=True)

# ---------------------------------------------------------------- oldest (a page once the research holds MIN_GUIDE places)
if HAS_OLD:
    oldest_named = next((p for p in OLD_L if p.promo_ok()), None)
    assert all(p.founded <= 1960 for p in OLD_L), "the oldest-places copy says 'since 1960 or earlier'"
    from_line = f" The oldest, {e(oldest_named.name)} in {e(oldest_named.city)}, goes back to {oldest_named.founded}." if oldest_named else ""
    guide_page(OLD_PATH, "North Carolina's oldest restaurants", checked_kicker(),
               [f"North Carolina's Oldest Restaurants: {len(OLD_L)} Places", f"Oldest Restaurants in North Carolina: {len(OLD_L)} Places",
                f"North Carolina's Oldest Restaurants, Year by Year"],
               [f"{plural(len(OLD_L), 'North Carolina restaurant')} open since 1960 or earlier, oldest first, each with a note on the dated source its year rests on.",
                f"North Carolina's oldest restaurants: {plural(len(OLD_L), 'place')} open since 1960 or earlier, oldest first, with the dated source behind each founding year."],
               f"Barbecue pits, lunch counters and seafood houses that have fed North Carolina since 1960 or before: {plural(len(OLD_L), 'place')} in all, oldest first, each checked in {CHECKED} against a 2025–26 source.{from_line} The note under each place names what its year rests on.",
               """<h2>Which year counts</h2>
    <p>We count from the year a place opened as it stands today, going by a dated 2025–26 source that ties the year to it. A brand's earlier start somewhere else doesn't count, and neither do the years before a move. If two sources give different years, the later one wins. Know a North Carolina place from 1960 or earlier that's missing? Send us the source.</p>""",
               OLD_L, "place", "places", "North Carolina's oldest restaurants", region=False, show_fn=True)

# ---------------------------------------------------------------- the grades explainer (counts only: no place is named or listed by score)
url = f"{DOMAIN}/{INS_PATH}"
n_ins = len(INS_L)
nav, bc = crumbs([("Home", "/"), ("North Carolina restaurant grades", "/" + INS_PATH)])
title = fit(["North Carolina Restaurant Grades: A, B and C, Explained", "How North Carolina Restaurant Grades Work | NC Eats",
             "North Carolina Restaurant Grades & Inspections, Explained"], 50, 60, "grades title")
desc = fit([f"How North Carolina grades restaurants A, B or C from the inspection score, Wake County's published scores for {n_ins:,} places, and each county's records.",
            f"North Carolina's A, B and C restaurant grades come from the inspection score. What they mean, Wake County's scores for {n_ins:,} places, and every county's link.",
            f"What North Carolina's A, B and C restaurant grade cards mean, Wake County's published scores for {n_ins:,} places, and where each county posts its reports."],
           140, 160, "grades description")
grade_items = "".join(f'<li><span class="card-grade">{e(g)}</span> {plural(GRADE_N.get(g, 0), "place")}</li>' for g in RESULTS)
counties_html = '<ul class="cities">' + "".join(f'<li><a href="{e(portal_url(c))}" rel="noopener">{e(c.removesuffix(" County"))}</a></li>'
                                                for c in sorted(COUNTY_NO, key=COUNTY_NO.get)) + "</ul>"
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} guide · public records</p>
    <h1>North Carolina restaurant grades, explained</h1>
    <p class="lede">A North Carolina restaurant hangs its grade card from the county health department where customers see it on the way in, as the state's rules require, and a new card goes up after every inspection. The letter comes from the inspection score under a state rule, 15A NCAC 18A .2662: A for a score of 90 or more, B for 80 to under 90, C for 70 to under 80. Below 70, the permit is revoked.</p>
    <div class="cta-row"><a class="btn" href="#portal">Find your county's inspections</a><a class="btn btn-ghost" href="{GRADING_RULES}" rel="noopener">The state's rules (PDF)</a></div>
  </section>
  <section id="wake">
    <h2>Wake County's scores</h2>
    <p class="sub">Wake County is the one county that publishes its food service permits and inspections as open data. For {plural(n_ins, "Wake County place")} we list, the app and the <a href="/explore/#g=inspections">web search</a> show the latest score and the letter it earns, the date, earlier inspections and the items the inspector cited, in the county's words. Records through {e(hdate(INS_THROUGH))}.</p>
    <p>At their latest inspection, by the county's score:</p>
    <ul class="grades">{grade_items}</ul>
    <p>The letter is the one rule .2662 assigns to the county's own score, so it matches the card by the door; {BRAND} computes no grade of its own, and a score the county didn't publish shows as a dash. Points come off for each Food Code item the inspector finds out of compliance. One inspection is a snapshot of one day. No page here lists places by score; the web search can sort Wake's list by it.</p>
    <p class="fine">Source: Wake County Environmental Health &amp; Safety, <a href="{WAKE_PERMITS}" rel="noopener">Restaurants in Wake County</a> and <a href="{WAKE_INSPECTIONS}" rel="noopener">Food Inspections</a>, Wake County Open Data, CC BY 4.0, retrieved {e(hdate(PERMITS_UPDATED))}; filtered and matched to map listings, with inspectors' names and comments left out. Wake County's notice: “Wake County Geographic Information Services shall not be held liable for any errors in these data. This includes errors of omission, commission, errors concerning the content of the data, and relative and positional accuracy of the data. These data cannot be construed to be a legal document. Primary sources from which these data were compiled must be consulted for verification of information contained in these data.”</p>
  </section>
  <section id="portal">
    <h2>Every county's inspections</h2>
    <p class="sub">The other 99 counties post their inspections only in the state's inspection search, run for NC DHHS, county by county: each report with its date, score and grade. It isn't published as open data, so we link each county's page and copy nothing. In the app and the web search, every place outside Wake links its own county's page.</p>
    {counties_html}
    <p class="fine">Some health departments also give sanitation awards; under the rule, an award must look different from a grade card and say "award". They aren't grades, and we don't show them.</p>
  </section>
  <section id="lookup">
    <h2>What else {BRAND} shows</h2>
    <p>In Wake County, a place's food service permit number. Alcohol shows as unknown everywhere, never as no: North Carolina's ABC permits aren't published as a list. The rest is hand-checked research and honors from the MICHELIN Guide and the James Beard Foundation.</p>
    <p class="fine">{other_guides("/" + INS_PATH)}</p>
  </section>
  </main>"""
page(INS_PATH, title, desc, body, [article_ld(url, "North Carolina restaurant grades, explained", desc), bc])

# ---------------------------------------------------------------- city pages
city_stats = {}
SEC_DEFS = [  # key, long title phrase, short title phrase, h1 phrase, description phrase builder (guides with a page only)
    (k, *v) for k, *v in [
        ("bbqeast", "Eastern Whole Hog", "Whole Hog", "whole hog barbecue", lambda n: plural(n, "hand-checked whole hog pit")),
        ("bbqlex", "Lexington Barbecue", "Barbecue", "Lexington barbecue", lambda n: plural(n, "Lexington barbecue joint")),
        ("hotdogs", "Carolina Hot Dogs", "Hot Dogs", "hot dogs", lambda n: plural(n, "Carolina hot dog stand")),
        ("calabash", "Calabash Seafood", "Seafood", "Calabash seafood", lambda n: plural(n, "Calabash seafood house")),
        ("biscuits", "Biscuits & Livermush", "Biscuits", "biscuits", lambda n: plural(n, "biscuit and livermush place")),
        ("moravian", "Moravian Bakeries", "Bakeries", "Moravian bakeries", lambda n: plural(n, "Moravian bakery", "Moravian bakeries")),
    ] if k in L
]
SEC_ORDER = [k for k, *_ in SEC_DEFS] + ["hon", "oldest"]
CITY_INFO = {}
# a town's county: the one most of its places are in (a city page outside Wake links that county's page in the state's search)
COUNTY_OF = {c: Counter(p.county for p in REST if p.city == c and p.county).most_common(1)[0][0] for c in CITY_PAGES}
for c in CITY_PAGES:
    here = [p for p in REST if p.city == c]
    info = {k: sorted([p for p in L[k] if p.city == c], key=P.featured_key) for k, _ in GUIDE_TAGS}
    info["hon"] = sorted([p for p in HON_L if p.city == c], key=P.featured_key)
    info["oldest"] = [p for p in OLD_L if p.city == c] if HAS_OLD else []
    info["ins"] = [p for p in INS_L if p.city == c]
    info["wake"] = any(p.county == "Wake County" for p in here)
    info["cuis"] = Counter(p.cuisine for p in here if p.cuisine and p.cuisine not in ("Other", "American & Other")).most_common(10)
    info["n_town"] = len(here)
    listed, seen = [], set()
    for k in SEC_ORDER:
        for p in info[k]:
            if id(p) not in seen:
                seen.add(id(p)); listed.append(p)
    info["listed"] = listed
    CITY_INFO[c] = info
    city_stats[c] = {"restaurants": len(here), "listed": len(listed), "wake_inspected": len(info["ins"]), **{k: len(info[k]) for k in SEC_ORDER}}


def city_sections(info):
    """The sections a city page has, biggest first: (key, long, short, h1 phrase, description phrase)."""
    out = [(k, lt, st, h1p, dp(len(info[k]))) for k, lt, st, h1p, dp in SEC_DEFS if info[k]]
    if info["hon"]:
        has_mi, has_jb = any(p.mi for p in info["hon"]), any(p.jbf for p in info["hon"])
        long = "MICHELIN & James Beard" if has_mi and has_jb else "MICHELIN" if has_mi else "James Beard"
        out.append(("hon", long, "MICHELIN" if has_mi else "James Beard", long if long != "James Beard" else "James Beard honorees",
                    plural(len(info["hon"]), "MICHELIN or James Beard honoree")))
    if info["oldest"]:
        k_old = len(info["oldest"])   # "1 of North Carolina's oldest restaurants", not "the oldest restaurants" (one place isn't the town's all)
        out.append(("oldest", "Oldest Restaurants", "Oldest Places", "oldest restaurants",
                    f"1 of North Carolina's oldest restaurants (from {info['oldest'][0].founded})" if k_old == 1
                    else f"{k_old} of North Carolina's oldest restaurants (back to {info['oldest'][0].founded})"))
    return sorted(out, key=lambda s: (-len(info[s[0]]), SEC_ORDER.index(s[0])))


def tjoin(xs):
    if len(xs) == 1:
        return xs[0]
    conj = " and " if any("&" in x for x in xs) else " & "
    return ", ".join(xs[:-1]) + conj + xs[-1]


def city_title(c, secs):
    cands = []
    for k in range(min(len(secs), 3), 0, -1):
        for col in (1, 2):
            J = tjoin([s[col] for s in secs[:k]])
            # "<town> restaurants" is what people search, so those forms come first
            forms = ([f"{c} Restaurants: {J}", f"{c}, NC Restaurants: {J}", f"{c} Restaurants: {J} | NC Eats", f"{c}, North Carolina Restaurants: {J}"]
                     if "Restaurant" not in J else [])
            forms += [f"{c} {J} | {BRAND}", f"{c}, NC {J} | {BRAND}", f"{c}, North Carolina {J}", f"{c}, NC {J}", f"{c} {J}"]
            if "Restaurant" not in J:
                forms += [f"{c} {J} & Restaurants", f"{c} {J} & Restaurants | NC Eats", f"{c}, North Carolina {J} & Restaurants"]
            cands += forms
    cands += [f"{c} Restaurants: What {c} Eats | {BRAND}", f"{c}, North Carolina Restaurants by Kind", f"{c}, NC Restaurants, Cafés & Bars | {BRAND}",
              f"{c}, North Carolina Restaurants, Cafés and Bars", f"{c} Restaurants, Cafés & Bars | {BRAND}", f"{c}, NC: Restaurants, BBQ & More | {BRAND}",
              f"{c}, NC: Barbecue, Grades & Restaurants | {BRAND}", f"{c}, North Carolina: Restaurants & Places to Eat", f"{c}, NC Restaurants & Places to Eat | {BRAND}"]
    return fit(cands, 50, 60, c + " title")


def city_desc(c, info, secs):
    n_town = info["n_town"]
    leads = [f"In {c}, North Carolina", f"{c}, North Carolina", f"{c}, NC"]
    tails = [f". Search {n_town:,} {c} restaurants, cafés and bars", f". Search {n_town:,} local places to eat",
             f", plus {n_town:,} local places to eat on a searchable map", f", plus {n_town:,} more local places to eat", ""]
    extras = ["", f" Checked in {CHECKED}.", " Free iPhone app coming soon.", f" Checked in {CHECKED}. Free iPhone app coming soon."]
    if info["ins"]:   # a Wake town: its places carry the county's own scores
        tails = [t + (" with Wake County's grades" if t else "") for t in tails] + tails

    def gen():
        for k in range(len(secs), 0, -1):
            J = join_words([s[4] for s in secs[:k]])
            for lead in leads:
                for tail in tails:
                    for x in extras:
                        yield f"{lead}: {J}{tail}.{x}"
    return fit(list(dict.fromkeys(s.replace("..", ".") for s in gen())), 140, 160, c + " description")


SEC_HEAD = {"bbqeast": ("Eastern whole hog barbecue", "bbqeast"), "bbqlex": ("Lexington barbecue", "bbqlex"), "hotdogs": ("Carolina hot dogs", "hotdogs"),
            "calabash": ("Calabash seafood", "calabash"), "biscuits": ("Biscuits and livermush", "biscuits"), "moravian": ("Moravian bakeries", "moravian")}
GUIDE_COUNT_NOUN = {"bbqeast": "Eastern whole hog pits", "bbqlex": "Lexington and Piedmont barbecue joints", "hotdogs": "Carolina hot dog stands",
                    "calabash": "Calabash seafood houses", "biscuits": "biscuit and livermush places", "moravian": "Moravian bakeries"}
SINGULAR = {"biscuit and livermush places": "biscuit and livermush place", "Moravian bakeries": "Moravian bakery",
            "Calabash seafood houses": "Calabash seafood house"}

for c in CITY_PAGES:
    info = CITY_INFO[c]
    path = f"cities/{slug(c)}.html"
    url = DOMAIN + "/" + path
    anchors = Anchors(url)
    secs = city_sections(info)
    title = city_title(c, secs)
    desc = city_desc(c, info, secs)
    k = 3
    while k > 1 and len(join_words([s[3] for s in secs[:k]])) > 48:   # a heading, not the whole table of contents
        k -= 1
    h1_bits = [s[3] for s in secs[:k]]
    h1 = f"{c} restaurants" + (": " + join_words(h1_bits + (["more"] if len(secs) > k else [])) if secs else "")
    nav, bc = crumbs([("Home", "/"), ("Cities", "/cities/"), (c, "/" + path)])
    counts = [s[4] for s in secs]
    n_hc = sum(1 for p in info["listed"] if p.hc and p.tags)
    lede = (f"What {e(c)} has on our lists: {e(join_words(counts))}. "
            + (f"Each hand-checked place had a 2025 or 2026 source when we looked in {CHECKED}. " if n_hc else "")
            + f"In all, {BRAND} maps {info['n_town']:,} restaurants, cafés, bars and bakeries in {e(c)}, nearest first on your phone.")
    parts = [f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} · {e(c)}, North Carolina</p>
    <h1>{e(h1)}</h1>
    <p class="lede">{lede}</p>
    <div class="cta-row">{store_button()}<span class="pill store-note">{STORE_NOTE}</span></div>
  </section>"""]
    for s in secs:
        key = s[0]
        if key in SEC_HEAD:
            head, gk = SEC_HEAD[key]
            parts.append(f'<section id="{key}" aria-labelledby="h-{key}"><h2 id="h-{key}">{e(head)} in {e(c)}</h2><p class="sub">Each one checked in {CHECKED} against a 2025–26 source. For all of North Carolina: <a href="/{GUIDE_PATH[gk]}">{plural(len(L[gk]), SINGULAR.get(GUIDE_COUNT_NOUN[gk], GUIDE_COUNT_NOUN[gk][:-1]), GUIDE_COUNT_NOUN[gk])}</a>.</p><ol class="places">'
                         + "".join(place_item(p, anchors) for p in info[key]) + "</ol></section>")
        elif key == "hon":
            parts.append(f'<section id="honors" aria-labelledby="h-honors"><h2 id="h-honors">MICHELIN &amp; James Beard in {e(c)}</h2><p class="sub">Restaurants in the MICHELIN Guide American South or named by the James Beard Foundation, reported as facts rather than scores. Across North Carolina: <a href="/{HON_PATH}">{plural(len(HON_L), "North Carolina MICHELIN and James Beard restaurant")}</a>.</p><ol class="places">'
                         + "".join(place_item(p, anchors, honors=True) for p in info["hon"]) + "</ol></section>")
        elif key == "oldest":
            parts.append(f'<section id="oldest" aria-labelledby="h-oldest"><h2 id="h-oldest">Oldest restaurants in {e(c)}</h2><p class="sub">Open since 1960 or before, going by a dated source, listed from the oldest. Each note gives the source of the year. Across North Carolina: <a href="/{OLD_PATH}">North Carolina\'s oldest restaurants</a>.</p><ol class="places">'
                         + "".join(place_item(p, anchors, show_fn=True) for p in info["oldest"]) + "</ol></section>")
    if info["ins"]:   # Wake County's own scores, as counts: no place is listed by its score here
        ig = Counter(p.grade for p in info["ins"])
        bits = join_words([f"{g} ({ig[g]:,})" for g in RESULTS if ig.get(g)])
        parts.append(f'<section id="inspections" aria-labelledby="h-inspections"><h2 id="h-inspections">Inspection grades in {e(c)}</h2><p class="sub">'
                     f"Wake County publishes its inspections, and {plural(len(info['ins']), 'place')} we list in {e(c)} have a published score. At their "
                     f"latest inspection, by the grade the county's score earns: {e(bits)}. Records through {e(hdate(INS_THROUGH))}. Each place's score, "
                     f'date and cited items are in the <a href="/explore/#g=inspections&amp;town={e(urllib.parse.quote(c))}">web search</a>; what the '
                     f'letters mean: <a href="/{INS_PATH}">North Carolina restaurant grades, explained</a>.</p></section>')
    elif c in COUNTY_OF:
        parts.append(f'<section id="inspections" aria-labelledby="h-inspections"><h2 id="h-inspections">Inspection grades in {e(c)}</h2><p class="sub">'
                     f"{e(COUNTY_OF[c])} posts its inspection reports, with each score and grade, in the state's inspection search: "
                     f'<a href="{e(portal_url(COUNTY_OF[c]))}" rel="noopener">{e(COUNTY_OF[c])}\'s inspections</a>. It isn\'t published as data, so we link it '
                     f'and copy nothing. What the letters mean: <a href="/{INS_PATH}">North Carolina restaurant grades, explained</a>.</p></section>')
    if info["cuis"]:
        rows = "".join(f'<tr><td>{e(k)}</td><td class="n">{n:,}</td></tr>' for k, n in info["cuis"])
        srcs = "open map data and Wake County’s permits" if info["wake"] else "open map data"
        parts.append(f'<section id="cuisines" aria-labelledby="h-cuisines"><h2 id="h-cuisines">What {e(c)} eats</h2><p class="sub">Kinds of food among the {info["n_town"]:,} places we list in {e(c)}, counted from {srcs}.</p><table><thead><tr><th scope="col">Kind of place</th><th scope="col" class="n">Places</th></tr></thead><tbody>{rows}</tbody></table></section>')
    parts.append(f'<section id="more" aria-labelledby="h-more"><h2 id="h-more">Other North Carolina towns with a page</h2>{city_links(current=c)}<p class="fine"><a href="/cities/">The cities and towns index</a></p></section>\n  </main>')
    lds = [article_ld(url, h1, desc), bc]
    if info["listed"]:
        lds.append(item_list(f"{c}: " + join_words([s[3] for s in secs]), info["listed"], url, anchors))
    page(path, title, desc, "\n".join(parts), lds)


# ---------------------------------------------------------------- cities index
url = f"{DOMAIN}/cities/"
nav, bc = crumbs([("Home", "/"), ("Cities", "/cities/")])
cards = []
for c in CITY_PAGES:
    info = CITY_INFO[c]
    bits = [f"{s[3]} ({len(info[s[0]])})" for s in city_sections(info)]
    line = (join_words(bits) + ". " if bits else "") + f"{info['n_town']:,} places to eat in all."
    cards.append(f'<a class="card" href="{city_url(c)}"><h3>{e(c)}</h3><p>{e(line[0].upper() + line[1:])}</p></a>')
first, last = CITY_PAGES[:2], CITY_PAGES[-2:]
title = fit([f"North Carolina Cities & Towns: Restaurant Guides", f"North Carolina City Restaurant Guides: {len(CITY_PAGES)} Towns",
             f"NC Cities & Towns: Restaurant Guides | {BRAND}"], 50, 60, "cities title")
desc = fit([f"Restaurant guides for {len(CITY_PAGES)} North Carolina cities and towns, from {join_words(first)} to {join_words(last)}: barbecue, MICHELIN and James Beard.",
            f"City-by-city North Carolina restaurant guides for {len(CITY_PAGES)} cities and towns: Eastern and Lexington barbecue, hot dogs, biscuits and honors.",
            f"Restaurant guides for {len(CITY_PAGES)} North Carolina cities and towns: whole hog and Lexington barbecue, hot dogs, biscuits, MICHELIN and James Beard."],
           140, 160, "cities description")
skipped_line = (f" Other towns get a page once they have at least {MIN_LISTED} hand-checked or honored places; until then, "
                f'<a href="/explore/">search them</a>.')
body = f"""{nav}
  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND} · cities and towns</p>
    <h1>North Carolina cities and towns</h1>
    <p class="lede">A page for North Carolina cities and towns that have enough hand-checked or honored places to say something real: the whole hog and Lexington barbecue, hot dog stands, biscuit counters and MICHELIN and James Beard honorees that are actually there, with Wake County's inspection grades in Wake towns.{skipped_line}</p>
  </section>
  <section id="cities-list">
    <h2>Pick a town</h2>
    <div class="grid2">{"".join(cards)}</div>
  </section>
  </main>"""
page("cities/index.html", title, desc, body, [bc], og_type="website")

# ---------------------------------------------------------------- web app (docs/explore/): data split + page
# The web app lists restaurants only (the venues the app hides by default, such as stadium stands and gas-station counters, stay out).
# Three kinds of file, to keep the first load small for ~17,000 places:
# - core.json: the list, search and map columns. Places are ordered by region, county, town, zip and street, so neighbouring rows
#   share their town, zip and street words and gzip well; coordinates are integer steps of 0.0001° from the previous row ("dla"/"dlo"),
#   and Wake County's latest inspection is its grade ("ib", an index into results), its score ("isc") and a day number from 2000-01-01
#   ("idn").
# - ids.json: each place's stable id (the app's id), in core order. Fetched right after the list renders; saved places and shared
#   #p= links wait for it.
# - detail-<county>.json: phones, websites, notes, county and city records and inspection histories, keyed by core index,
#   one file per county (Wake's is the biggest), fetched when someone opens (or points at) a place there.
os.makedirs(f"{DOCS}/data", exist_ok=True)
DFILES = [slug(c) for c in COUNTIES] + ["other"]   # detail file per county index; "other" for a place with no county
CAL = {a: {"groups": {g: {"n": v.get("n"), "official": v.get("official")} for g, v in (c.get("groups") or {}).items()}}
       for a, c in (D.get("calibration") or {}).items() if isinstance(c, dict)}
DAY0 = "2000-01-01"


def day_num(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return (dt.date(int(m[1]), int(m[2]), int(m[3])) - dt.date(2000, 1, 1)).days if m else None


def street_key(a):
    m = re.match(r"\s*(\d+)\s*(.*)", a or "")
    return (m[2].lower(), int(m[1]) if len(m[1]) < 9 else 0) if m else ((a or "").lower(), 0)


def web_order(p):
    rg = REGION_ORDER.index(p.region) if p.region else len(REGION_ORDER)
    return (rg, p.county or "", p.city or "", p.zip, street_key(p.addr), p.name.lower(), p.r["id"])


WEB = sorted(REST, key=web_order)
CORE_KEYS = ["n", "c", "co", "cu", "t", "s", "a", "z", "b", "ch", "g", "hc", "ip", "f", "h", "mi", "dish"]
cols = {k: [] for k in CORE_KEYS + ["dla", "dlo", "jb", "ib", "isc", "idn"]}
ids, shards = [], defaultdict(dict)
prev = [0, 0]
for i, p in enumerate(WEB):
    r = p.r
    ids.append(r["id"])
    for k in CORE_KEYS:
        v = r.get(k)
        if k == "a" and v:
            v = p.addr
        cols[k].append(v)
    for k, j, v in (("dla", 0, p.lat), ("dlo", 1, p.lon)):
        if v is None:
            cols[k].append(None)
        else:
            q = round(v * 10000)
            cols[k].append(q - prev[j])
            prev[j] = q
    dk = r["co"] if r.get("co") is not None else len(COUNTIES)   # the detail file this place's extras go in
    if r.get("co") is None:
        cols["co"][-1] = len(COUNTIES)
    cols["jb"].append(1 if r.get("jbf") else None)
    ins = p.ins or {}
    cols["ib"].append(ins.get("b"))
    cols["isc"].append(ins.get("s"))
    cols["idn"].append(day_num(ins.get("d")))
    d = {k: r[k] for k in ("ph", "note", "seas", "fn", "jbf", "lic") if r.get(k)}
    if p.site:
        d["w"] = p.site
    if ins.get("h"):
        d["in"] = {"n": ins.get("n"), "h": ins["h"], "i": ins.get("i") or []}
    if d:
        shards[dk][str(i)] = d
assert len(set(ids)) == len(ids), "place ids must be unique (saved places and #p= links use them)"
for f in glob.glob(f"{DOCS}/data/detail*.json"):   # files from an older layout or a region that emptied
    os.remove(f)
# columns that are mostly empty (hand-checked and honored facts, Wake's inspections) go as [[index, value], ...] instead of 23,000 nulls
sparse = {k: [[i, v] for i, v in enumerate(cols.pop(k)) if v is not None]
          for k in list(cols) if sum(v is not None for v in cols[k]) < len(WEB) * 0.05}
core = {"generated": D["generated"], "permits_updated": PERMITS_UPDATED, "inspections_through": INS_THROUGH, "day0": DAY0,
        "portal": PORTAL, "county_no": [COUNTY_NO.get(c) for c in COUNTIES] + [None],
        "n": len(WEB), "cities": CITIES, "cuisines": CUISINES, "counties": COUNTIES + ["North Carolina"],
        "brands": D["brands"], "srcs": D["srcs"], "results": RESULTS, "itypes": ITYPES, "calibration": CAL, "cols": cols, "sparse": sparse,
        "dfiles": [f if dk in shards else None for dk, f in enumerate(DFILES)]}   # null: that county has no extras, so no file
assert all("," not in x for x in ids)
# ids and details are keyed by row, so a file from one build must never meet another build's core.json (a browser cache can outlive a
# deploy by GitHub's 10 minutes): every file carries the build's version, the page fetches with ?v=, and the web app refuses a mismatch
DATA_VER = hashlib.sha256(json.dumps([core, ids, shards], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
DETAIL_FILES = {}
for dk, d in sorted(shards.items()):
    fn = f"detail-{DFILES[dk]}.json"
    json.dump({"_v": DATA_VER, **d}, open(f"{DOCS}/data/{fn}", "w"), separators=(",", ":"), ensure_ascii=False)
    DETAIL_FILES[fn] = len(d)
json.dump({"ver": DATA_VER, **core}, open(f"{DOCS}/data/core.json", "w"), separators=(",", ":"), ensure_ascii=False)
json.dump({"v": DATA_VER, "ids": ",".join(ids)}, open(f"{DOCS}/data/ids.json", "w"), separators=(",", ":"))   # one string: smaller than an array
for f in glob.glob(f"{DOCS}/data/*_shapes.json"):
    os.remove(f)
json.dump(json.load(open(f"{ROOT}/data/nc/nc_shapes.json")), open(f"{DOCS}/data/nc_shapes.json", "w"), separators=(",", ":"))


def sizes(path):
    raw = open(path, "rb").read()
    return len(raw), len(gzip.compress(raw, 9))


SIZES = {os.path.relpath(f, DOCS): sizes(f) for f in sorted(glob.glob(f"{DOCS}/data/*.json"))}

EXPLORE_CSS = """
  [hidden] { display: none !important; }
  .ex-hero { padding: 28px 0 8px; }
  .ex-hero h1 { font-size: clamp(30px, 6vw, 44px); }
  .ex-controls { background: var(--bg); padding: 10px 0 8px; border-bottom: 1px solid var(--rule); }
  .ex-guides { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; scrollbar-width: none; }
  @media (min-width: 601px) { .ex-guides { flex-wrap: wrap; overflow: visible; } }
  @media (max-width: 600px) { .ex-guides { padding-right: 32px; -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 32px), transparent); mask-image: linear-gradient(to right, #000 calc(100% - 32px), transparent); } }
  .ex-guides button, .ex-view button, .ex-small { flex: 0 0 auto; border: 1px solid var(--rule); background: var(--surface); color: var(--accent); border-radius: 999px; padding: 7px 12px; font: 600 14px/1.2 system-ui, sans-serif; font-family: inherit; cursor: pointer; }
  .ex-guides button[aria-pressed="true"], .ex-view button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
  .ex-row1 { display: flex; gap: 8px; align-items: center; }
  .ex-row1 input[type=search] { flex: 1; min-width: 0; font: 16px/1.3 system-ui, sans-serif; font-family: inherit; padding: 10px 12px; border: 2px solid var(--accent); border-radius: 12px; background: var(--surface); color: var(--ink); }
  .ex-row2 { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; font-size: 14px; }
  .ex-row2 select { font: 14px system-ui, sans-serif; font-family: inherit; padding: 6px 8px; border: 1px solid var(--rule); border-radius: 8px; background: var(--surface); color: var(--ink); max-width: 46vw; }
  .ex-view { margin-left: auto; display: flex; gap: 4px; }
  #ex-count { margin: 8px 0 0; font-size: 14px; color: var(--muted); }
  #ex-sub { margin: 4px 0 0; font-size: 14px; color: var(--ink2); }
  #ex-locmsg { font-size: 13px; color: var(--muted); margin: 4px 0 0; }
  .ex-list { list-style: none; padding: 0; margin: 10px 0; }
  .ex-list li + li { border-top: 1px solid var(--rule); }
  .ex-row { width: 100%; display: flex; gap: 12px; align-items: center; text-align: left; background: none; border: 0; padding: 12px 4px; cursor: pointer; color: var(--ink); font: inherit; }
  .ex-row:hover { background: var(--surface2); }
  .ex-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; overflow-wrap: anywhere; }
  .ex-main b { font-weight: 650; }
  .ex-town { font-size: 14px; color: var(--muted); }
  .tag-dash { background: transparent; color: var(--muted); border: 1px dashed var(--rule); }
  .ex-metric { text-align: right; display: flex; flex-direction: column; align-items: flex-end; max-width: 46%; }
  .ex-metric b { font: 800 22px/1 var(--display); color: var(--accent); }
  .ex-metric small { font-size: 11px; color: var(--muted); }
  .ex-rank { flex: 0 0 34px; height: 34px; display: grid; place-items: center; font: 800 20px var(--display); color: var(--accent); border-radius: 8px; }
  .ex-rank.top { background: var(--orange); color: var(--on-orange); }
  .ex-empty { padding: 24px 4px; color: var(--muted); }
  #ex-more { display: block; margin: 8px auto 24px; }
  #ex-mapwrap { position: relative; height: min(72vh, 720px); margin: 10px 0 20px; border: 1px solid var(--rule); border-radius: 16px; overflow: hidden; background: #dfe6f2; }
  #ex-map { width: 100%; height: 100%; display: block; touch-action: none; cursor: grab; }
  .ex-zoom { position: absolute; right: 10px; top: 10px; display: flex; flex-direction: column; gap: 6px; }
  .ex-zoom button { width: 44px; height: 44px; border-radius: 10px; border: 1px solid #dce2ec; background: #fff; color: #002d72; font: 700 22px/1 system-ui, sans-serif; cursor: pointer; }
  #ex-maphint { position: absolute; left: 10px; top: 10px; margin: 0; font-size: 13px; background: #fff; padding: 3px 8px; border-radius: 999px; color: #28385a; pointer-events: none; }
  #ex-mapattr { position: absolute; right: 0; bottom: 0; margin: 0; font-size: 11px; background: rgba(255,255,255,.85); padding: 2px 6px; border-radius: 6px 0 0 0; color: #28385a; pointer-events: none; }
  .ex-panel { position: fixed; z-index: 20; right: 0; top: 0; bottom: 0; width: min(440px, 100%); overflow-y: auto; background: var(--surface); border-left: 1px solid var(--rule); box-shadow: -8px 0 24px rgba(0,0,0,.12); padding: 18px 20px 40px; }
  @media (max-width: 600px) { .ex-panel { top: auto; height: 86vh; border-left: 0; border-top: 4px solid var(--orange); border-radius: 18px 18px 0 0; } }
  .ex-close { position: sticky; top: 0; float: right; width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--rule); background: var(--surface); font-size: 24px; line-height: 1; cursor: pointer; color: var(--ink); }
  .ex-kicker { margin: 0; font-size: 12px; font-weight: 700; letter-spacing: .1em; color: var(--accent2); }
  .ex-panel h2 { font-size: 34px; margin: 4px 0 6px; text-transform: uppercase; overflow-wrap: anywhere; }
  .ex-addr, .ex-dist { margin: 0 0 4px; color: var(--ink2); font-size: 15px; }
  .ex-actions { margin: 14px 0 8px; display: grid; gap: 8px; }
  .ex-apple { justify-content: center; }
  .ex-act-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .ex-act-row a, .ex-act-row button { flex: 1; min-width: 88px; text-align: center; padding: 10px; border: 1px solid var(--rule); border-radius: 12px; text-decoration: none; color: var(--accent); font: 600 14px system-ui, sans-serif; font-family: inherit; background: var(--surface); cursor: pointer; }
  .ex-act-row button[aria-pressed="true"] { background: var(--soft); color: #5c0716; }
  .ex-sec { margin-top: 18px; }
  .ex-sec h3 { font-size: 12px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--rule); padding-bottom: 6px; margin-bottom: 8px; }
  .ex-sec p, .ex-sec li { font-size: 15px; color: var(--ink2); margin: 6px 0; }
  .ex-sec ul { padding-left: 18px; }
  .ex-kv { display: flex; justify-content: space-between; gap: 12px; font-size: 15px; padding: 3px 0; }
  .ex-kv span { color: var(--ink2); flex: 0 0 auto; max-width: 40%; }
  .ex-kv b { text-align: right; overflow-wrap: anywhere; }
  .ex-fine { font-size: 13px !important; color: var(--muted) !important; }
  .ex-result { display: flex; align-items: center; gap: 10px; font-weight: 600; flex-wrap: wrap; }
  .ex-app { margin-top: 22px; font-size: 14px; color: var(--muted); }
  body.ex-open { overflow: hidden; }
  .ex-backdrop { position: fixed; inset: 0; z-index: 19; background: rgba(15, 27, 51, .32); }
  /* phones: 16px or more in the search box and the selects, or iOS Safari zooms the page when one gets focus */
  @media (max-width: 600px) { .ex-row1 input[type=search], .ex-row2 select { font-size: 16px; } }
  /* the sort's longest choice ("MICHELIN, then James Beard") at 16px: wider than 46vw, so on phones it may use the row */
  @media (max-width: 600px) { #ex-sort { max-width: calc(100vw - 100px); } }
  .ex-res { display: inline-block; font: 800 12px/1.4 -apple-system, system-ui, sans-serif; letter-spacing: .04em; text-transform: uppercase; padding: 3px 8px; border-radius: 6px; text-align: center; }
  .ex-res-ok { background: #ddefe3; color: #0e5a2b; } .ex-res-mid { background: #ffe9c2; color: #6b3a00; } .ex-res-low { background: #f9d5db; color: #7a0019; } .ex-res-x { background: var(--surface2); color: var(--ink2); }
  /* the county's grade card: black on white, as the rule has it, in both color schemes */
  .ex-card { display: inline-grid; place-items: center; min-width: 34px; height: 34px; padding: 0 6px; border: 2px solid #111; background: #fff; color: #111; font: 800 20px/1 var(--display); border-radius: 4px; }
  .ex-gs { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
  .ex-grade { display: flex; align-items: center; gap: 12px; margin: 4px 0 8px; }
  .ex-grade b { font: 600 22px/1 var(--mono); color: var(--ink); }
  .ex-hist { list-style: none; padding: 0 !important; margin: 4px 0; }
  .ex-hist li { display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid var(--rule); padding: 4px 0; margin: 0 !important; }
  .ex-cited li { margin: 4px 0 !important; }
"""
url = f"{DOMAIN}/explore/"
N_HC_GUIDES = len(HC_ANY)
title = fit(["North Carolina Restaurant Search: Barbecue, Grades & Map", "Search North Carolina Restaurants: BBQ, Grades & Map",
             "NC Restaurant Search: Barbecue, Wake Grades & Map | NC Eats"], 50, 60, "explore title")
desc = fit([f"Look up {N_REST:,} North Carolina restaurants by name, town, street or dish, map {N_HC_GUIDES} hand-checked places and see Wake County's grades.",
            f"Search {N_REST:,} North Carolina restaurants by name, town, street or dish, map {N_HC_GUIDES} hand-checked barbecue joints and see Wake's grades.",
            f"Search {N_REST:,} North Carolina restaurants by name, town or dish, browse {N_HC_GUIDES} hand-checked places on a map and see Wake County's scores."],
           140, 160, "explore description")
nav, bc = crumbs([("Home", "/"), ("Search", "/explore/")])
LIST_WORDS = {"bbqeast": "Eastern whole hog", "bbqlex": "Lexington barbecue", "hotdogs": "Carolina hot dog", "calabash": "Calabash seafood",
              "biscuits": "biscuit and livermush", "moravian": "Moravian bakery"}
# the app's guides, each once it has a place in it (Home leaves an empty one out too); the web app's GUIDES has them all
WEB_GUIDES = [(k, t) for k, t in (("bbqeast", "Eastern whole hog"), ("bbqlex", "Lexington barbecue"), ("hotdogs", "Carolina hot dogs"),
                                   ("calabash", "Calabash seafood"), ("biscuits", "Biscuits & livermush"), ("moravian", "Moravian bakeries"))
              if L_ALL[k]]
guide_buttons = "".join(f'<button type="button" data-g="{k}" aria-pressed="false">{e(t)}</button>' for k, t in
                        WEB_GUIDES + [("honors", "MICHELIN & James Beard")] + ([("oldest", "Oldest")] if OLD_L else [])
                        + [("inspections", "Wake County inspections"), ("all", "All restaurants"), ("saved", "Saved")])
explore_js = open(f"{ROOT}/scripts/explore.js").read()
JS_KEYS = sorted(set(re.findall(r'store\.set\("([a-z]+)"', explore_js)))   # the keys the web app writes, each under STORAGE_PREFIX
assert JS_KEYS and "localStorage.setItem(PREFIX + k" in explore_js and len(re.findall(r"localStorage\.setItem", explore_js)) == 1
assert "</script" not in explore_js.lower()
assert f'"{STORAGE_PREFIX}"' in explore_js, "explore.js must keep its localStorage keys under " + STORAGE_PREFIX
body = f"""{nav}
  <main id="main">
  <section class="ex-hero">
    <p class="kicker">{BRAND} · on the web</p>
    <h1>Search North Carolina restaurants</h1>
    <p class="sub">Pick a list, or type a name, a town, a street or a dish. Behind the search: {N_REST:,} North Carolina restaurants, cafés, bars and bakeries; {N_HC_GUIDES} hand-checked places on the {e(join_words([LIST_WORDS[k] for k, _ in WEB_GUIDES]))} lists; {len(HON_L)} MICHELIN and James Beard honorees; and Wake County's inspection scores for {len(INS_L):,} places. It's the data the iPhone and iPad app will ship with, and what you save stays in this browser.</p>
  </section>
  <p id="ex-loading" hidden>Loading the restaurant list…</p>
  <noscript><p>The search needs JavaScript. The guides work without it: {", ".join(f'<a href="/{GUIDE_PATH[k]}">{e(GUIDE_NAME[k][0].lower() + GUIDE_NAME[k][1:])}</a>' for k in list(L)[:3])}, <a href="/{INS_PATH}">restaurant grades, explained</a>.</p></noscript>
  <div id="ex-app" hidden data-ver="{DATA_VER}">
    <div class="ex-controls">
      <div class="ex-guides" role="group" aria-label="Guides">{guide_buttons}</div>
      <div class="ex-row1">
        <label class="skip" for="ex-q">Search</label>
        <input id="ex-q" type="search" placeholder="Name, town, street or dish" autocomplete="off" enterkeyhint="search">
        <button type="button" id="ex-locate" class="ex-small">Near me</button>
      </div>
      <div class="ex-row2">
        <label>Sort <select id="ex-sort" aria-label="Sort"></select></label>
        <select id="ex-town" aria-label="Town"></select>
        <select id="ex-cuisine" aria-label="Kind of place"></select>
        <label><input type="checkbox" id="ex-chains"> Hide chains</label>
        <label id="ex-bibwrap" hidden><input type="checkbox" id="ex-bib"> <span>Bib Gourmand <span id="ex-bibn"></span></span></label>
        <button type="button" id="ex-clear" class="ex-small" hidden>Clear filters</button>
        <div class="ex-view" role="group" aria-label="View"><button type="button" data-v="list" aria-pressed="true">List</button><button type="button" data-v="map" aria-pressed="false">Map</button></div>
      </div>
      <p id="ex-sub"></p>
      <p id="ex-count" aria-live="polite"></p>
      <p id="ex-locmsg"></p>
    </div>
    <div id="ex-listwrap"><ol id="ex-list" class="ex-list"></ol><button type="button" id="ex-more" class="ex-small" hidden></button></div>
    <div id="ex-mapwrap" hidden>
      <canvas id="ex-map" aria-label="Map of North Carolina with a dot for each place in the list. The list view has the same places."></canvas>
      <div class="ex-zoom"><button type="button" id="ex-zin" aria-label="Zoom in">+</button><button type="button" id="ex-zout" aria-label="Zoom out">−</button></div>
      <p id="ex-maphint"></p>
      <p id="ex-mapattr">Outlines © OpenStreetMap contributors, Overture Maps Foundation</p>
    </div>
  </div>
  <div id="ex-backdrop" class="ex-backdrop" hidden></div>
  <aside id="ex-panel" class="ex-panel" hidden aria-labelledby="ex-pname"></aside>
  </main>
<script>
{explore_js}
</script>"""
webapp_ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": f"{BRAND} web app", "url": url,
             "applicationCategory": "TravelApplication", "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
             "description": desc, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
             "publisher": ORG_REF}
page("explore/index.html", title, desc, body, [webapp_ld, bc], extra_css=EXPLORE_CSS, og_type="website")

# ---------------------------------------------------------------- landing page
# alt text says what each capture shows (docs/screenshots, made by scripts/capture-screenshots.sh; copies by scripts/site-images.sh)
shots = [("home", "The North Carolina Eats home screen: a search box and guide cards for Eastern Whole Hog, Lexington Barbecue, Carolina Hot Dogs and Biscuits & Livermush, each with its count of places.", "A guide for each North Carolina craving."),
         ("eastern_bbq", "The hand-checked Eastern whole hog list in North Carolina Eats, with each place's town.", "Whole hog, east of Raleigh."),
         ("detail", "Sam Jones BBQ in North Carolina Eats: its address, Bib Gourmand and Eastern whole hog tags, a button for Apple Maps' ratings, hours and photos, Directions and Call buttons, and Wake County's latest inspection score and grade.", "Each place, with Wake County's grade."),
         ("inspections", "Wake County's inspections in North Carolina Eats: each place's street address, grade card, score and month.", "Wake County's own scores."),
         ("map", "The North Carolina Eats map around Raleigh, with pins and numbered clusters and filter buttons for North Carolina picks and honors.", "The map, by guide."),
         ("honors", "The MICHELIN and James Beard list in North Carolina Eats.", "MICHELIN Guide and James Beard honorees.")]
shot_html = []
for i, (name, alt, cap) in enumerate(shots):
    png = f"{DOCS}/img/screen-{name}.png"
    if not os.path.exists(png):
        continue
    w, h = png_size(png)
    lazy = ' loading="lazy"'   # the section sits below the fold at every width
    webp = os.path.exists(f"{DOCS}/img/screen-{name}.webp")
    src = (f'<source srcset="/img/screen-{name}.webp" type="image/webp">' if webp else "")
    shot_html.append(f'<li><picture>{src}<img src="/img/screen-{name}.png" alt="{e(alt)}" width="{w}" height="{h}"{lazy} decoding="async"></picture><p>{e(cap)}</p></li>')

EAST_L, LEX_L = L_ALL["bbqeast"], L_ALL["bbqlex"]
GUIDE_PHRASE = {"bbqeast": "Eastern whole hog barbecue", "bbqlex": "Lexington barbecue", "hotdogs": "Carolina hot dogs", "calabash": "Calabash seafood",
                "biscuits": "biscuits and livermush", "moravian": "Moravian bakeries"}
GUIDE_WORDS = join_words([GUIDE_PHRASE[k] for k, _ in WEB_GUIDES])
faq = [
    ("Is North Carolina Eats free?", "Completely: no price, no ads, no in-app purchases and no account to create. It's an iPhone and iPad app on its way to the App Store, with no Android version yet; until it's out, the web search here works in any browser."),
    ("Where do the lists come from?", f"Two kinds of source. The {join_words([LIST_WORDS[k] for k, _ in WEB_GUIDES])} lists are our own research from {CHECKED}, with a 2025 or 2026 source behind each place: its website or menu, a dated local news story, a Wake County inspection or an official tourism listing. The wider directory of {N_REST:,} restaurants starts from Overture Maps' open place data, keeps the kinds of listing that proved reliable against Wake County's permit list, and adds Wake restaurants from that list."),
    ("Where can I get Eastern and Lexington barbecue?", f"Our Eastern list has {len(EAST_L)} hand-checked whole hog places in {plural(len({p.city for p in EAST_L if p.city}), 'town')}, and our Lexington list {len(LEX_L)} Piedmont pits in {plural(len({p.city for p in LEX_L if p.city}), 'town')}. In the web search, either list puts the nearest first once you share your location."),
    ("How do North Carolina restaurant grades work?", "Every county inspects restaurants under the state's rules and posts a grade card by the door: A for a score of 90 or more, B for 80 to under 90, C for 70 to under 80. Wake County publishes its inspections as data, so Wake places show the latest official score, its grade, the date and the items cited. The other counties' reports are in the state's inspection search, linked from each place; we copy no score and compute no grade."),
    ("Does it show which places serve alcohol?", "No. North Carolina's ABC permits aren't published as a list, so alcohol shows as unknown everywhere, never as no."),
    ("Does it show ratings and reviews?", "Not from us. Tapping a place opens Apple Maps' own card inside the app, with Apple's current ratings, hours, photos and directions. None of our lists is sorted by anyone's rating."),
    ("Does it need my location?", "No. Location only matters for putting the nearest places first. If you share it, it stays on your iPhone or iPad and never reaches us, and the app works fine without it. On this website, Near me reads your location inside your browser and nowhere else."),
    ("A place has closed, or something's wrong. How do I tell you?", f"Write to {EMAIL} with the place's name, its town and what changed. Corrections ship with the next data update."),
]
faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "@id": f"{DOMAIN}/#faq",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
app_ld = {"@context": "https://schema.org", "@graph": [
    # No "offers" until the app is on the App Store (put it back with the listing URL: price 0, USD).
    {"@type": "MobileApplication", "@id": f"{DOMAIN}/#app", "name": APP_NAME,
     "alternateName": ["NC Eats", "North Carolina Eats: Restaurants, BBQ & Biscuits"],
     "description": f"A free guide to {N_REST:,} North Carolina restaurants, with hand-checked lists of {GUIDE_WORDS}, {len(HON_L)} MICHELIN and James Beard honorees, and Wake County's official inspection scores. Sort by distance, open Apple Maps' live place card for hours and photos, and save places for your next trip.",
     "url": f"{DOMAIN}/", "image": f"{DOMAIN}/og.png", "operatingSystem": "iOS, iPadOS", "applicationCategory": "TravelApplication",
     "applicationSubCategory": "Food & Drink", "inLanguage": "en", "publisher": {"@id": ORG_ID}},
    {"@type": "Organization", "@id": ORG_ID, "name": BRAND, "url": f"{DOMAIN}/",
     "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/icon-512.png", "width": 512, "height": 512}, "email": EMAIL,
     "contactPoint": {"@type": "ContactPoint", "contactType": "customer support", "email": EMAIL, "availableLanguage": "en"},
     # the Eats Ranked hub lists this site as a subOrganization; say so from this side too
     "parentOrganization": HUB},
    {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "name": BRAND, "alternateName": ["NC Eats", "North Carolina Eats app"], "url": f"{DOMAIN}/",
     "inLanguage": "en", "publisher": {"@id": ORG_ID}}]}
if shot_html:
    app_ld["@graph"][0]["screenshot"] = f"{DOMAIN}/img/screen-{next(n for n, *_ in shots if os.path.exists(f'{DOCS}/img/screen-{n}.png'))}.png"
title = fit(["North Carolina Eats: Barbecue, Biscuits & Restaurant App", "North Carolina Eats: BBQ, Biscuits & Restaurant Guide"], 50, 60, "landing title")
desc = fit([f"Eastern whole hog, Lexington barbecue, hot dogs and biscuits: a free iPhone and iPad guide to {N_REST:,} North Carolina restaurants, with Wake's grades.",
            f"A free iPhone and iPad guide to {N_REST:,} North Carolina restaurants, with hand-checked Eastern and Lexington barbecue, hot dogs and biscuits.",
            f"Free iPhone and iPad guide to {N_REST:,} North Carolina restaurants: hand-checked barbecue and biscuits, MICHELIN and James Beard, Wake's grades."],
           140, 160, "landing description")
city_cards = "".join(f'<li><a href="{city_url(c)}">{e(c)}</a></li>' for c in CITY_PAGES)
screens = f"""
  <section id="screens">
    <h2>Inside the app</h2>
    <ul class="shots" tabindex="0" aria-label="North Carolina Eats app screenshots">
      {"".join(shot_html)}
    </ul>
  </section>""" if shot_html else ""
CARD_LINE = {"bbqeast": " that cook the whole hog", "bbqlex": ", shoulder, dip and red slaw", "hotdogs": ", all the way",
             "calabash": ", lightly fried", "biscuits": " for biscuits and livermush", "moravian": " for sugar cake and thin cookies"}
guide_cards = "".join(f'<a class="card gc gc-{k}" href="/{GUIDE_PATH[k]}"><b>{len(L[k])}</b><h3>{e(GUIDE_NAME[k])}</h3><p>{plural(len(L[k]), "hand-checked place")}{CARD_LINE[k]}.</p></a>'
                      for k, _ in GUIDE_TAGS)
old_card = (f'<a class="card gc gc-oldest" href="/{OLD_PATH}"><b>{len(OLD_L)}</b><h3>North Carolina\'s oldest restaurants</h3>'
            f'<p>{plural(len(OLD_L), "place")} open since 1960 or earlier.</p></a>') if HAS_OLD else ""
body = f"""  <main id="main">
  <section class="hero">
    <p class="kicker">{BRAND}: {TAGLINE} for iPhone and iPad</p>
    <h1>North Carolina restaurants, whole hog to biscuits</h1>
    <p class="lede">Looking for Eastern whole hog, a Lexington tray with red slaw, a hot dog all the way or a biscuit with livermush? {BRAND} starts with lists we checked place by place, adds the MICHELIN Guide and James Beard honorees and Wake County's inspection grades, and maps {N_REST:,} restaurants, cafés, bars and bakeries in {N_TOWNS:,} North Carolina towns.</p>
    <div class="cta-row">{store_button()}<a class="btn btn-ghost" href="/explore/">Search on the web</a><span class="pill store-note">No charge, no ads, no sign-in. The App Store release is on its way.</span></div>
    <ul class="stats" aria-label="What's in the app">
      <li><b>{N_HC_GUIDES}</b><span>hand-checked places</span></li>
      <li><b>{len(HON_L)}</b><span>MICHELIN &amp; James Beard</span></li>
      <li><b>{len(INS_L):,}</b><span>Wake County grades</span></li>
      <li><b>{N_REST:,}</b><span>restaurants</span></li>
    </ul>
  </section>

  <section id="what">
    <h2>Built around how North Carolina eats</h2>
    <p class="sub">Star ratings won't tell you which pit still cooks the whole hog, or where the slaw comes red. {BRAND} is organized the way people here eat: {e(GUIDE_WORDS)}, each place checked in {CHECKED} against a 2025–26 source. Wake County places carry the county's own inspection score and grade, every other place links its county's reports, and Apple Maps' live card supplies ratings, hours and photos.</p>
  </section>

  <section id="how">
    <h2>How it works</h2>
    <ol class="steps">
      <li class="step"><div class="n" aria-hidden="true">1</div><div><h3>Start with a craving.</h3><p>{e(join_words([t for _, t in WEB_GUIDES] + ["MICHELIN & James Beard", "Wake County inspections"], "or"))}. Or type a name, a town, a street or a dish to search the {N_REST:,} we list.</p></div></li>
      <li class="step"><div class="n" aria-hidden="true">2</div><div><h3>Find the closest one.</h3><p>Put the nearest first, narrow it to one town or one kind of food, or pan the map from Murphy to Manteo.</p></div></li>
      <li class="step"><div class="n" aria-hidden="true">3</div><div><h3>Head out.</h3><p>Check today's hours and photos on Apple Maps' card, call ahead, get directions, or save the place for the next road trip.</p></div></li>
    </ol>
  </section>
{screens}
  <section id="guides">
    <h2>North Carolina food guides</h2>
    <p class="sub">Each of the app's lists has its own page here, free to read.</p>
    <div class="grid2">
      {guide_cards}
      {old_card}
      <a class="card gc gc-honors" href="/{HON_PATH}"><b>{len(HON_L)}</b><h3>MICHELIN &amp; James Beard</h3><p>{plural(len(HON_L), "honored North Carolina restaurant")}.</p></a>
      <a class="card gc gc-inspections" href="/{INS_PATH}"><b>A·B·C</b><h3>Restaurant grades, explained</h3><p>What the card by the door means, Wake County's scores for {plural(len(INS_L), "place")}, and every county's reports.</p></a>
    </div>
  </section>

  <section id="cities">
    <h2>Barbecue, biscuits and more by city</h2>
    <p class="sub">From the mountains to the coast, the towns with enough hand-checked or honored places for a page of their own. The <a href="/cities/">cities and towns index</a> sums up what's on each.</p>
    <ul class="cities">{city_cards}</ul>
  </section>

  <section id="pricing">
    <h2>Free, with no catch</h2>
    <p class="sub">The app costs nothing, shows no ads and sells nothing inside, and there's no account to make. The lists ship inside the app, so they open right away and keep working when the signal drops out in the mountains or on the Outer Banks.</p>
  </section>

  <section id="privacy">
    <h2>What stays on your phone</h2>
    <p class="sub">{BRAND} collects nothing about you: no sign-in, no analytics, no ads. Location, if you turn it on, only puts the nearest places first, and your saved places are kept on the phone or iPad. The website has no cookies and no trackers. <a href="/privacy.html">The privacy policy</a> has the details.</p>
  </section>

  <section id="faq">
    <h2>Questions</h2>
    {faq_html}
  </section>

  <section id="download" class="final">
    <h2>Find your next tray of barbecue</h2>
    <p class="sub">The iPhone and iPad app is almost here, and it's free. Ask for early access.</p>
    <div class="cta-row">{store_button()}</div>
  </section>
  </main>"""
page("index.html", title, desc, body, [app_ld, faq_ld], og_type="website")

# ---------------------------------------------------------------- privacy and terms
nav, bc = crumbs([("Home", "/"), ("Privacy policy", "/privacy.html")])
body = f"""{nav}
  <main id="main" class="legal">
  <section class="hero">
    <h1>Privacy policy</h1>
    <p class="lede">Short version: the {BRAND} app collects nothing about you, and this website doesn't track you. Last updated {PRIVACY_UPDATED}.</p>
  </section>
  <section>
    <h2>The app</h2>
    <ul>
      <li><b>No account, no analytics, no ads.</b> The app has no sign-in, no advertising and no analytics or crash-reporting code. We receive no data from it.</li>
      <li><b>Location.</b> If you allow it, your location is used on your device to sort places by distance and show where you are on the map. It is never sent to us. You can turn it off in Settings at any time.</li>
      <li><b>Saved places and filters</b> are stored only on your device and are deleted when you delete the app.</li>
      <li><b>Apple Maps.</b> When you open a place's ratings, hours and photos, or ask for directions, the app asks Apple Maps for that place. Apple handles that request under <a href="https://www.apple.com/legal/privacy/" rel="noopener">Apple's privacy policy</a>, as it does for any app that shows a map.</li>
      <li><b>Data updates.</b> When you open the app, it checks this website for newer restaurant data, at most once a day (or an hour later if a check didn't go through), and downloads it when there is some. These requests carry no location or identifiers. GitHub, which hosts this site, may keep standard server logs of them, as it does for any visit here.</li>
      <li><b>Spotlight.</b> The app adds its hand-checked and honored places to your device's search index so you can find them from Spotlight. That index stays on your device.</li>
      <li><b>Calls, websites and email</b> you start from a place open in the Phone app, your browser or Mail, and are handled by them.</li>
    </ul>
    <p>When the app is on the App Store, its privacy label will be "Data Not Collected".</p>
    <h2>This website</h2>
    <p>The site is static pages hosted on GitHub Pages. It sets no cookies and loads no analytics, fonts or scripts from anyone else.</p>
    <ul>
      <li><b>Saved places and your last guide.</b> The search page (<a href="/explore/">/explore/</a>) keeps the places you save and the last guide you opened in your browser's local storage, on this device only, under the keys {join_words([f"<code>{STORAGE_PREFIX}{k}</code>" for k in JS_KEYS])}. Nothing is sent to us. Clearing this site's data in your browser removes them.</li>
      <li><b>Location.</b> If you tap Near me or choose the Nearest sort, your browser asks whether to share your location. If you allow it, the location is used only inside your browser to sort places by distance and is never sent to us or anyone else.</li>
    </ul>
    <p>GitHub may keep standard server logs, such as IP addresses, for security; see <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub's privacy statement</a>.</p>
    <h2>Email</h2>
    <p>If you email us, we use your message and address only to reply and to fix the listing you told us about. We don't add you to a mailing list or share your address. Mail to {EMAIL} reaches our inbox through Cloudflare Email Routing; see <a href="https://www.cloudflare.com/privacypolicy/" rel="noopener">Cloudflare's privacy policy</a>.</p>
    <h2>Children</h2>
    <p>The app collects no personal information from anyone, including children.</p>
    <h2>Changes and contact</h2>
    <p>If this policy changes, the new version will be posted here with a new date. Questions: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  </section>
  </main>"""
page("privacy.html", fit(["North Carolina Eats Privacy Policy: No Tracking, No Accounts", "North Carolina Eats Privacy Policy: No Tracking"], 50, 60),
     fit(["How North Carolina Eats treats your data: the iPhone app collects none, your location and saved places stay on your device, and this site uses no cookies.",
          "How North Carolina Eats treats your data: the app collects none, your location and saved places stay on your device, and this site sets no cookies."], 140, 160),
     body, [bc])

nav, bc = crumbs([("Home", "/"), ("Terms of use", "/terms.html")])
body = f"""{nav}
  <main id="main" class="legal">
  <section class="hero">
    <h1>Terms of use</h1>
    <p class="lede">The plain-language terms for the {BRAND} app and this website. Last updated {POLICY_UPDATED}.</p>
  </section>
  <section>
    <h2>What the app is</h2>
    <p>{BRAND} is a free guide to restaurants in North Carolina. It is provided as is, for personal use, without charge and without warranties of any kind.</p>
    <h2>Check before you go</h2>
    <p>Restaurants open, close, change their hours and change their menus, and many barbecue joints and hot dog stands keep short hours. Dishes and founding years are what each place or a named source said when we checked in {CHECKED}. We work to keep the lists right, but we can't promise that any listing is current or complete. Call the restaurant before you make the trip.</p>
    <h2>Inspections and public records</h2>
    <p>For Wake County places, the app and this site show Wake County's published inspection scores, the dates and the items cited, with the letter the state's grading rule (15A NCAC 18A .2662) gives each score; we compute no grade of our own. Places in other counties link the state's inspection search for their county; no score is copied. Food service permit numbers come from Wake County's open data, retrieved on the date shown in the app, and inspections run through the date shown there. For official records, use each agency's own site.</p>
    <h2>Other people's content</h2>
    <p>Ratings, reviews, hours and photos in each place card come from Apple Maps and are Apple's and its providers', under Apple's terms. Restaurant names and trademarks belong to their owners. MICHELIN and the MICHELIN Guide are trademarks of Michelin; James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. {BRAND} is not affiliated with any restaurant, chain, award body or government agency.</p>
    <h2>Data sources and licenses</h2>
    <ul>
      <li>Wake County Environmental Health &amp; Safety: Restaurants in Wake County, Food Inspections and Food Inspection Violations (Wake County Open Data), under the Creative Commons Attribution 4.0 license, filtered and matched to map listings, with inspectors' names and comments left out. Wake County's notice: “Wake County Geographic Information Services shall not be held liable for any errors in these data. This includes errors of omission, commission, errors concerning the content of the data, and relative and positional accuracy of the data. These data cannot be construed to be a legal document. Primary sources from which these data were compiled must be consulted for verification of information contained in these data.” No endorsement by Wake County is claimed.</li>
      <li>Overture Maps Foundation places data, under the Community Data License Agreement, Permissive 2.0, including data from Meta, Microsoft, DAC, BrightQuery, AllThePlaces (CC0 1.0) and Foursquare (Apache 2.0).</li>
      <li>Overture Maps Foundation divisions, used for the state and county outlines on the map, under the Open Database License: © OpenStreetMap contributors, Overture Maps Foundation.</li>
      <li>Overture Maps Foundation addresses data, compiled from open address sources under permissive licenses (see docs.overturemaps.org/attribution), used to place records on the map.</li>
      <li>The MICHELIN Guide American South selection and the James Beard Foundation's awards, nominees, semifinalists and America's Classics: honors reported as facts.</li>
      <li>Eastern whole hog, Lexington barbecue, Carolina hot dogs, Calabash seafood, biscuits and livermush, and founding years: our own research, with a source recorded for every place.</li>
    </ul>
    <h2>Corrections</h2>
    <p>If a listing is wrong, or you own a restaurant and want something fixed, email <a href="mailto:{EMAIL}">{EMAIL}</a>. We fix mistakes in the next update.</p>
    <h2>Liability</h2>
    <p>To the extent the law allows, we are not liable for any loss arising from use of the app or site, including a wasted drive to a closed restaurant.</p>
    <h2>Changes</h2>
    <p>We may update these terms; the current version and its date are always on this page. See also the <a href="/privacy.html">privacy policy</a>.</p>
  </section>
  </main>"""
page("terms.html", fit(["North Carolina Eats Terms of Use: A Free Guide, As Is", "North Carolina Eats Terms of Use: Provided As Is"], 50, 60),
     fit(["The terms for North Carolina Eats and this site: a free guide provided as is, public records shown as the agencies published them, and how to report a mistake.",
          "The terms for North Carolina Eats and this site: a free guide provided as is, Wake County's records shown as published, and how to report a mistake.",
          "Terms for North Carolina Eats and this site: a free restaurant guide provided as is, public records shown as published, and how to report a mistake."], 140, 160),
     body, [bc])

body = f"""  <main id="main">
  <section class="hero">
    <h1>Page not found</h1>
    <p class="lede">No page lives at this address. Head back to the <a href="/">{BRAND} home page</a>, the <a href="/{GUIDE_PATH['bbqeast']}">Eastern barbecue list</a> or the <a href="/explore/">North Carolina restaurant search</a>.</p>
  </section>
  </main>"""
page("404.html", f"Not found: {BRAND}", "No page lives at this address.", body, robots="noindex,follow")
noindexed.remove("404.html")


# ---------------------------------------------------------------- plumbing
for f in os.listdir(f"{DOCS}/cities"):   # a city the data lost: drop its old page instead of leaving it live and stale
    if f.endswith(".html") and f"cities/{f}" not in written + noindexed:
        os.remove(f"{DOCS}/cities/{f}")
        print("removed stale", f"cities/{f}")
urls = ["" if w == "index.html" else w.replace("index.html", "") for w in written]
urls.sort(key=lambda u: (u != "", u.startswith("cities/"), u))
open(f"{DOCS}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                       + "".join(f"  <url><loc>{DOMAIN}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(f"{DOCS}/robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
json.dump({"name": BRAND, "short_name": "NC Eats", "description": f"{TAGLINE[0].upper() + TAGLINE[1:]}: a guide to {N_REST:,} North Carolina restaurants.",
           "start_url": f"{BASE}/", "display": "browser", "background_color": "#f3f5fa", "theme_color": "#13294b",
           "icons": [{"src": f"{BASE}/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": f"{BASE}/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(f"{DOCS}/site.webmanifest", "w"), indent=2)
if CUSTOM_DOMAIN:
    open(f"{DOCS}/CNAME", "w").write(CUSTOM_DOMAIN + "\n")
elif os.path.exists(f"{DOCS}/CNAME"):
    os.remove(f"{DOCS}/CNAME")   # no custom domain yet: GitHub serves the project address
open(f"{DOCS}/.nojekyll", "w").write("")
os.makedirs(f"{ROOT}/playbook", exist_ok=True)
json.dump({"generated": TODAY, "domain": DOMAIN, "restaurants": N_REST, "places_incl_hidden": len(PLACES), "towns": N_TOWNS, "counties": N_COUNTIES,
           "on_an_official_list": N_OFFICIAL, "hand_checked_on_a_guide": N_HC, "wake_inspected": len(INS_L), "wake_grades": dict(GRADE_N),
           **{"guide_" + k: len(v) for k, v in L_ALL.items()}, "guide_pages": list(L), "oldest": len(OLD_L), "honors": len(HON_L), "michelin": MI_COUNT,
           "james_beard": N_JBF, "americas_classics": N_CLASSICS, "permits_updated": PERMITS_UPDATED, "inspections_through": INS_THROUGH,
           "city_pages": city_stats, "cities_without_a_page": CITY_SKIPPED, "noindex_pages": noindexed,
           "web_app_data_bytes": {k: {"raw": r, "gzip": g} for k, (r, g) in SIZES.items()}},
          open(f"{ROOT}/playbook/site-numbers.json", "w"), indent=1, ensure_ascii=False)
print("wrote", len(written) + len(noindexed) + 1, "pages:", ", ".join(written))
if noindexed:
    print("noindex:", ", ".join(noindexed))
print(f"restaurants {N_REST:,} in {N_TOWNS} towns | official {N_OFFICIAL:,} | hand-checked on a guide {N_HC} | "
      + " | ".join(f"{k} {len(v)}" for k, v in L_ALL.items()) + f" | oldest {len(OLD_L)} | honors {len(HON_L)} | Wake inspected {len(INS_L):,} {dict(GRADE_N)}")
print("city pages:", ", ".join(CITY_PAGES), "| no page (listed places):", CITY_SKIPPED)
print(f"website blocklist: {len(BLOCKLIST)} entries, {len(BLOCKED_LINKS)} links dropped:", "; ".join(f"{n} {u}" for n, u in BLOCKED_LINKS) or "none")
for k, (r, g) in SIZES.items():
    print(f"  {k}: {r / 1024:,.0f} KB raw, {g / 1024:,.0f} KB gzip")
