#!/usr/bin/env python3
"""Writes the App Store listing and the App Review reply from the build's own counts (playbook/site-numbers.json, which
scripts/make-site.py rewrites on every run), so the copy never drifts from the data. Ported from tn-eats (modeled on wa-eats/playbook/06
and 13).

Usage (from nc-eats/): .venv/bin/python scripts/make-listing.py   (after make-site.py)
Writes playbook/06-app-store-listing.md, playbook/13-app-review-reply.md and playbook/app-store/listing.json (what
../scripts/asc_listing.py uploads once Nick creates the App Store Connect record and its FOLDERS line is added).
Checks before writing anything: Apple's length limits, no keyword repeating a name/subtitle word, no "best"/"top"/"#1", no price
claim outside the description's plain "free guide", the reply under 4,000 characters.
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
N = json.load(open(os.path.join(ROOT, "playbook", "site-numbers.json")))
R, T, LIC, HON, INS = N["restaurants"], N["towns"], N["on_an_official_list"], N["honors"], N["wake_inspected"]
MI, JBF = N["michelin"], N["james_beard"]
G = {k[6:]: v for k, v in N.items() if k.startswith("guide_") and isinstance(v, int)}
OLD = N["oldest"]
FLOOR = R // 1000 * 1000   # "22,000+": promo text and What's New outlive small data changes
SITE = "https://northcarolina.eatsranked.com/"   # until the CNAME resolves: https://nickstrom5.github.io/north-carolina-eats/

NAME = "North Carolina Eats"          # Nick, 2026-10-26: the family's ": Restaurants" doesn't fit 30, so it's in the subtitle
SUB = "Restaurants, BBQ & Biscuits"
# no word from the name or subtitle; towns are the biggest search win (rotate after a month of App Store Connect search-term data)
KW = "raleigh,charlotte,asheville,durham,greensboro,wilmington,barbecue,whole hog,lexington,hot dog,grades"
PROMO = (f"{G['bbqeast']} Eastern whole hog pits, {G['bbqlex']} Lexington barbecue joints and Carolina hot dogs, checked by hand, "
         f"plus Wake County's grades and {FLOOR:,}+ restaurants near you.")
WHATS_NEW = (f"First release: Eastern and Lexington barbecue, Carolina hot dogs, biscuits and livermush, Wake County's inspection grades "
             f"and {FLOOR:,}+ North Carolina restaurants.")

# the app's guides, each listed only once it has a place in it (Home leaves an empty guide out too)
GUIDE_LINES = [(k, line) for k, line in (
    ("bbqeast", f"• Eastern Whole Hog: {G['bbqeast']} pits that cook the whole hog the eastern way, chopped and dressed with vinegar and pepper."),
    ("bbqlex", f"• Lexington Barbecue: {G['bbqlex']} Piedmont pits for pork shoulder, red dip and red slaw."),
    ("hotdogs", f"• Carolina Hot Dogs: {G['hotdogs']} stands serving them all the way, with chili, slaw, onions and mustard."),
    ("calabash", f"• Calabash Seafood: {G['calabash']} places for lightly breaded, quickly fried seafood."),
    ("biscuits", f"• Biscuits & Livermush: {G['biscuits']} places for scratch biscuits and the western Piedmont's livermush."),
    ("moravian", f"• Moravian Bakeries: {G['moravian']} bakeries for sugar cake and paper-thin spice cookies."),
) if G.get(k)]
GUIDE_NAMES = {"bbqeast": "Eastern Whole Hog", "bbqlex": "Lexington Barbecue", "hotdogs": "Carolina Hot Dogs", "calabash": "Calabash Seafood",
               "biscuits": "Biscuits & Livermush", "moravian": "Moravian Bakeries"}
GUIDE_COUNTS = {"bbqeast": "Eastern whole hog pits", "bbqlex": "Lexington barbecue joints", "hotdogs": "Carolina hot dog stands",
                "calabash": "Calabash seafood houses", "biscuits": "biscuit and livermush places", "moravian": "Moravian bakeries"}


def join_words(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


n1 = MI.get("1 MICHELIN Star", 0)
ONE_STAR = "one-star restaurant" if n1 == 1 else f"{n1} one-star restaurants"
counted = join_words([f"{G[k]} {GUIDE_COUNTS[k]}" for k, _ in GUIDE_LINES])
home_path = ", ".join([GUIDE_NAMES[k] for k, _ in GUIDE_LINES][1:] + ["MICHELIN & James Beard"] + (["Oldest Places"] if OLD else [])
                      + ["Wake County Inspections", "Near Me"])

DESC = f"""North Carolina's restaurants, from a tray of Eastern whole hog to a Lexington plate with red slaw.

North Carolina Eats is a free guide to eating in North Carolina: {counted} we checked by hand, {HON} MICHELIN and James Beard honorees, Wake County's official inspection scores and grades for {INS:,} places, and {R:,} restaurants, cafés, bars and bakeries in {T} towns, from Murphy to Manteo. No account, no ads.

NORTH CAROLINA GUIDES
{chr(10).join(line for _, line in GUIDE_LINES)}
{f"• Oldest Places: {OLD} restaurants open at the same address since 1960 or earlier." + chr(10) if OLD else ""}• MICHELIN & James Beard: the MICHELIN Guide's {ONE_STAR}, {MI.get('Bib Gourmand', 0)} Bib Gourmands and Recommended places, and James Beard winners, nominees, semifinalists and America's Classics ({HON} places).
• Wake County Inspections: the county's own latest score for {INS:,} places, with the grade it earns (A at 90 or more), the date and the items cited.

FIND IT FAST
• Sort by distance, or browse the map by guide.
• Search by name, town, street or dish: "whole hog raleigh", "red slaw".
• Filter by town or cuisine, show Bib Gourmands only, or hide chains.
• Save places, and find hand-checked places from iPhone search (Spotlight).

LIVE DETAILS FROM APPLE MAPS
Tap "Ratings, hours & photos" on any place to open Apple Maps' own place card, with current hours, photos, ratings and directions.

HOW THE LISTS ARE BUILT
Every guide place was checked by hand in October 2026 against a 2025 or 2026 source: the place's own site or menu, dated local news, a Wake County inspection, the MICHELIN Guide or an official tourism listing. The rest come from Overture Maps open data, checked against Wake County's permit list. Wake County publishes its inspections, so Wake places show the county's latest score and the grade North Carolina's rule gives it; every other place links its county's reports in the state's own search. Website links are checked too. Nothing is ranked by star ratings, and the app computes no grades of its own.

PRIVATE BY DESIGN
No account, no tracking, no ads. Your location, if you share it, only sorts lists on your device. Saved places stay on your device.

Places open and close, so check before you go. Spot a mistake? Email nick@eatsranked.com.

An independent app, not affiliated with any restaurant, chain or government agency (including the State of North Carolina, the NC Department of Health and Human Services and Wake County), or with the MICHELIN Guide or the James Beard Foundation. MICHELIN and the MICHELIN Guide are trademarks of Michelin. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. Place data from Overture Maps Foundation (CDLA Permissive 2.0), Wake County Open Data (CC BY 4.0) and others; sources and licenses are on the About tab."""

REPLY = f"""Thank you. Here is the information requested. A screen recording from an iPhone running the latest iOS is attached. It starts at launch and shows the full flow.

1. Screen recording: attached. There is no account, login, user-generated content or paid content.

2. Purpose and audience: North Carolina Eats is a free guide to restaurants in North Carolina. Its focus is the state's food traditions: {counted}, each checked by hand in October 2026 against a 2025 or 2026 source, plus the MICHELIN Guide and James Beard honorees. It also lists {R:,} restaurants, cafés and bars statewide from open map data, checked against Wake County's permit list, and shows Wake County's published inspection scores for {INS:,} places. It is for North Carolina residents and visitors deciding where to eat, with no ads, account or tracking.

3. How to use it (no login, no setup, no sample files needed):
- Home → Eastern Whole Hog (or {home_path}) → tap any place.
- On a place, tap "Ratings, hours & photos" to open Apple Maps' own place card through MapKit. Directions, Call and Website are below it; further down, Wake County places show the county's latest inspection score and grade, and other places link their county's reports in the state's search, in Safari.
- Search from the Home search box by name, town, street or dish ("whole hog raleigh", "red slaw").
- The Map tab shows each guide as pins. "My location" and the Nearest sort use location only if allowed, on the device.
- The heart saves a place on the device (Saved tab). About lists the sources, licenses and the independence statement.
- On iPad, a sidebar replaces the tabs; a place opens in the right-hand column.
- Outside North Carolina (as App Review usually is), the map says so and stays on the state; distance sorting still works from where you are.
- "NC Eats" is the short Home Screen name of "North Carolina Eats".

4. External services and data:
- Apple MapKit: maps, local search to find a place's Apple Maps listing, and Apple's place card for live hours, photos and ratings.
- Core Location: optional, on-device only, for distance sorting.
- Core Spotlight: on-device indexing so places appear in iPhone search.
- Data updates: at most daily, the app checks the website below for newer restaurant data (nothing about the user is sent). No backend, accounts, analytics, ads, payments or AI services.
- Bundled data: Overture Maps Foundation places (CDLA Permissive 2.0; Foursquare records under Apache 2.0, AllThePlaces under CC0; license texts in the app); Wake County's permits and inspections (Wake County Open Data, CC BY 4.0); MICHELIN Guide and James Beard honors (facts only); our own research of public websites and local news. Other counties' reports are linked, not copied.
- The website with the privacy policy and support page is static and hosted on GitHub Pages: {SITE}

5. Regional differences: none. The content covers North Carolina; the app is offered in the United States and works the same everywhere.

6. Regulated or protected material: the app is not in a regulated industry and includes no protected third-party material. The data is open-licensed or public record, with attribution and licenses on the About tab. Ratings, hours and photos are shown only inside Apple's own place card through MapKit; the app stores no ratings or reviews. Inspection scores are Wake County's own, shown with the grade the state's rule gives them; the app computes no grades of its own. Every website link was checked before release, and adult venues are excluded. The app is independent and not affiliated with any restaurant, agency, the MICHELIN Guide or the James Beard Foundation.

Support: nick@eatsranked.com"""

# ---------------- checks (nothing is written unless all pass)
problems = []
for label, text, limit in (("name", NAME, 30), ("subtitle", SUB, 30), ("keywords", KW, 100), ("promotional text", PROMO, 170),
                           ("What's New", WHATS_NEW, 4000), ("description", DESC, 4000), ("review notes", REPLY, 4000)):
    if len(text) > limit:
        problems.append(f"{label}: {len(text)} characters, limit {limit}")
title_words = set(re.findall(r"[a-z]+", (NAME + " " + SUB).lower()))
for kw in KW.split(","):
    if kw != kw.strip() or not kw:
        problems.append(f"keyword {kw!r}: no spaces around commas, no empty entries")
    if set(kw.split()) & title_words:
        problems.append(f"keyword {kw!r} repeats a word from the name or subtitle")
for text, label in ((KW, "keywords"), (PROMO, "promotional text"), (SUB, "subtitle"), (WHATS_NEW, "What's New")):
    for bad in (r"\bbest\b", r"\btop\b", r"#1", r"\bfree\b", r"\bevery\b"):
        if re.search(bad, text, re.I):
            problems.append(f"{label}: contains {bad!r}")
if re.search(r"\bevery (?:restaurant|place)\b|\ball [\d,]+ ", DESC + REPLY, re.I):
    problems.append("description/reply: an 'every restaurant' or 'all N' claim the data can't back")
if problems:
    sys.exit("not written:\n  " + "\n  ".join(problems))

listing = {"bundleId": "com.northcarolinaeats.ios", "name": NAME, "subtitle": SUB, "privacyPolicyUrl": SITE + "privacy.html",
           "primaryCategory": "FOOD_AND_DRINK", "secondaryCategory": "TRAVEL", "description": DESC, "keywords": KW,
           "promotionalText": PROMO, "supportUrl": SITE, "marketingUrl": SITE, "reviewNotes": REPLY}
os.makedirs(os.path.join(ROOT, "playbook", "app-store"), exist_ok=True)
json.dump(listing, open(os.path.join(ROOT, "playbook", "app-store", "listing.json"), "w"), indent=1, ensure_ascii=False)

open(os.path.join(ROOT, "playbook", "06-app-store-listing.md"), "w").write(f"""# App Store listing (ASO)

Written by `scripts/make-listing.py` from `site-numbers.json` ({N['generated']}); re-run it after every data refresh, never hand-edit.
The machine copy is `app-store/listing.json` (read by `../scripts/asc_listing.py` once Nick creates the App Store Connect record and
adds `"com.northcarolinaeats.ios": "nc-eats"` to its FOLDERS). The URLs assume northcarolina.eatsranked.com is live; until Nick's
CNAME resolves, use https://nickstrom5.github.io/north-carolina-eats/.

## Name (30 max)
`{NAME}` ({len(NAME)})

## Subtitle (30 max)
`{SUB}` ({len(SUB)})

Together they index: north, carolina, eats, restaurants, bbq, biscuits. Home Screen name: NC Eats.

## Keywords (100 max)
`{KW}` ({len(KW)})

- No word repeats the name or subtitle; no trademarks (no Skylight Inn, Biltmore, Cook Out, Bojangles), no "best", "top" or "#1".
- Towns are the biggest win; Winston-Salem, Chapel Hill, Cary, Greenville, Boone and the Outer Banks didn't fit, nor did livermush.
  Rotate them in after a month of App Store Connect search-term data. Apple's public search can't be used for this research (itunes.apple.com's robots.txt blocks Claude).

## Promotional text (170 max, editable any time without review)
`{PROMO}` ({len(PROMO)})

## Description ({len(DESC)} of 4,000)
```
{DESC}
```

## What's New (1.0)
`{WHATS_NEW}`

## Screenshots
Framed by `scripts/appstore-screenshots.py`: `app-store/iphone/` (8, 1320x2868, the 6.9" slot) and `app-store/ipad/` (6, 2064x2752, the
13" slot). Upload one file at a time in file order and check the order after a reload. No negative board appears in any image, and
captions name no award body.

## Category and age rating
Primary Food & Drink, secondary Travel. Age rating: alcohol references "Infrequent" (bars, breweries, taprooms) → 13+; everything
else None/No. Pricing $0.00, available in the United States. Content rights: yes, third-party content, with the rights (open data, public
records, Apple's place card). Untick "Sign-in required".

## App Review
Reply and recording script: `13-app-review-reply.md`. Put the reply in App Review Information → Notes from the start.
""")

open(os.path.join(ROOT, "playbook", "13-app-review-reply.md"), "w").write(f"""# App Review: prepared before submitting (Guideline 2.1 "Information Needed")

Written by `scripts/make-listing.py` ({N['generated']}). Wisconsin's new-developer review asked for a screen recording from a physical
device, starting at launch, plus answers to six questions; North Carolina Eats should expect the same. Put the reply below in **App
Review Information → Notes** from the start ({len(REPLY):,} of 4,000 characters), and record the video before submitting. If Apple
raises Guideline 4.3(a), answer with North Carolina's own guides and sources (Eastern whole hog, Lexington barbecue, Carolina hot dogs,
biscuits and livermush, the MICHELIN Guide American South, Wake County's permits and inspection scores under rule .2662, the state's
inspection search for every county); never compare with the other state apps in the Notes.

## Screen recording (Nick, on his iPhone, latest iOS, 60–120 seconds, no sound)

Install from TestFlight first (the internal tester's email must be the Apple ID under Settings › your name › Media & Purchases on the
phone, or TestFlight says "not available"). Record with Control Center → Screen Recording:

1. Start on the Home Screen and tap **NC Eats**. The recording must begin with the launch.
2. Home: scroll the cards a little.
3. Tap **Eastern Whole Hog**, then **Sam Jones BBQ** (Raleigh).
4. Tap **Ratings, hours & photos**; Apple's place card opens. Close it, then scroll to the Health inspections section (Wake County's
   grade card and score).
5. Tap the **heart** (Save), then go back to Home.
6. Tap the search box and type `whole hog raleigh`. Open one result.
7. Tap the **Map** tab, then **North Carolina picks**, then a pin and its name.
8. Tap the **Saved** tab, where the saved place shows. Then tap **About** and scroll to the sources.

## Reply text

```
{REPLY}
```
""")
print(f"wrote listing.json, 06-app-store-listing.md, 13-app-review-reply.md | keywords {len(KW)}/100, promo {len(PROMO)}/170, "
      f"description {len(DESC):,}/4,000, reply {len(REPLY):,}/4,000")
