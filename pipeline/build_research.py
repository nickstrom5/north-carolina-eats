"""Writes data/research/app/*.json (hand-checked North Carolina guides) from the compact lists below. Ported from tn-eats.

Each entry cites a page that names the place for the food (robots-checked host: check_sources.py) and 2025-26 evidence that it is
operating, one of: the MICHELIN Guide's 2026 selection; a Wake County inspection in 2026 (data.wake.gov, the county's own record); a
page dated 2025-26; the place's own site showing a 2026 date; or a current listing by the state's or the town's tourism office
(VisitNC, Visit Lexington: undated pages read 2026-10-26, the weakest of these, named as such in the note). The address comes from the
map listing we already hold for that name in that town (site/northcarolina.json), never from memory; a name that isn't found exactly
once in its town (or at the street number given) is left out and listed in data/research/app/LEADS.md.
Usage: ../.venv/bin/python build_research.py   (then northcarolina.py)"""
import json, os, re
from brands import brand_of
from common import norm_name
ROOT = os.path.join(os.path.dirname(__file__), "..")
R = os.path.join(ROOT, "data", "research")
d = json.load(open(os.path.join(ROOT, "site", "northcarolina.json")))
C, M = d["cols"], d["meta"]
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower().replace("'", "").replace("’", ""))).strip()

# naming pages
VNC_BBQ = "https://www.visitnc.com/list/taste-north-carolina-barbecue-styles-history-new-twists"   # VisitNC, current listing (undated, (c) 2026)
VNC_DISH = "https://www.visitnc.com/list/14-must-try-dishes-and-food-items-north-carolina"         # VisitNC, current listing (undated, (c) 2026)
VNC_NASCAR = "https://www.visitnc.com/itinerary/fall-nascar-weekend-charlotte-concord-and-lexington"   # VisitNC itinerary for the Oct 11, 2026 race
LEX_TA = "https://www.visitlexingtonnc.com/barbecue"                     # Lexington Tourism Authority's current list (undated)
OS_LEX = "https://www.ourstate.com/5-stops-for-barbecue-lexington-nc/"   # Our State, Feb 14, 2024
OS_PIT = "https://www.ourstate.com/pit-stop-26-essential-north-carolina-barbecue-joints/"   # Our State, Feb 1, 2019
OS_TRAIL = "https://www.ourstate.com/north-carolina-historic-barbecue-trail/"                # Our State, Jan 29, 2016 (with a later editor's note)
OS_DOGS = "https://www.ourstate.com/10-hot-dog-joints-across-the-state/"                      # Our State, Jul 12, 2016
OS_CALA = "https://www.ourstate.com/lightly-breaded-perfectly-fried-the-legacy-of-calabash/"  # Our State, May 29, 2023
CP_MUSH = "https://cardinalpine.com/2025/10/15/7-things-to-know-about-the-upcoming-liver-mush-festival-in-shelby/"   # Oct 15, 2025
WAKE = "https://data.wake.gov/datasets/ebe3ae7f76954fad81411612d7c4fb17"   # Wake County food inspections (the county's own records)
MI = "https://guide.michelin.com/us/en/north-carolina/"
# the places' own sites (each read 2026-10-26)
LEXBBQ = "https://www.lexbbq.com/"                  # posts its 2026 holiday closures; "serving pork barbecue since 1962"
STAMEYS = "https://www.stameys.com/"                # "Lexington-style", pit-cooked over hardwood coals; (c) 2026
PARKERS = "https://www.parkersbbq.com/"             # "NC style Whole Hog BBQ", three Greenville locations; (c) 2026
SKYLIGHT = "https://www.skylightinnbbq.com/welcome"  # since 1947; hours; (c) 2026
BECKS = "https://www.becksrestaurant.com/"          # "Calabash Style Seafood"; (c) 2026
SUNRISE = "https://sunrisebiscuits.com/"            # "Bigger Better Biscuits", Chapel Hill and Louisburg; (c) 2026

# (name as the source writes it, town, street number to pick the location (or None), note, founded, founded_note, [sources])
GUIDES = {
 "eastern bbq": [
  ("Skylight Inn BBQ", "Ayden", "4618", "Whole hogs over wood since 1947, the crackling skin chopped into the meat.", None, None, [VNC_BBQ, SKYLIGHT]),
  ("Sam Jones BBQ", "Raleigh", "502", "Whole-hog barbecue from the Skylight Inn family; a MICHELIN Bib Gourmand.", None, None, [VNC_BBQ, MI + "raleigh_2149711/restaurant/sam-jones-bbq"]),
  ("B's Barbecue", "Greenville", "751", "Classic Eastern NC barbecue at a counter the McLawhorn family has run for generations (VisitNC's current list).", None, None, [VNC_BBQ]),
  ("Parker's Barbecue", "Greenville", "3109", "Whole-hog barbecue with a tangy vinegar sauce, on Memorial Drive.", None, None, [PARKERS]),
  ("Parker's Barbecue", "Greenville", "2020", "Whole-hog barbecue with a tangy vinegar sauce, on Greenville Blvd.", None, None, [PARKERS]),
  ("Parker's Barbecue", "Greenville", "1801", "Whole-hog barbecue with a tangy vinegar sauce, on Arlington Blvd.", None, None, [PARKERS]),
  ("The Pit Authentic Barbecue", "Raleigh", "328", "Whole-hog pork in the Warehouse District; MICHELIN Recommended; inspected by Wake County in 2026.", None, None, [VNC_BBQ, MI + "raleigh_2149711/restaurant/the-pit-authentic-barbecue", WAKE]),
  ("Prime Barbecue", "Knightdale", "403", "Eastern whole hog meets Texas brisket; a MICHELIN Bib Gourmand.", None, None, [VNC_BBQ, MI + "knightdale_2149824/restaurant/prime-barbecue"]),
  ("Stephenson's BBQ", "Benson", "50", "Eastern-style pork barbecue near Willow Spring (VisitNC's current list).", None, None, [VNC_BBQ, OS_PIT]),
 ],
 "lexington bbq": [
  ("Lexington Barbecue", "Lexington", "100", "Pork shoulder over oak and hickory coals with red slaw and a vinegar-and-ketchup dip; Wayne Monk's place since 1962.", None, None, [LEXBBQ, OS_LEX]),
  ("Barbecue Center", "Lexington", "900", "Pit-cooked Lexington barbecue on North Main Street; started in 1955 as a dairy bar.", None, None, [OS_LEX, LEX_TA, VNC_BBQ]),
  ("Speedy's BBQ", "Lexington", "408", "A Lexington institution with curb service, on Piedmont Drive.", None, None, [OS_LEX, LEX_TA]),
  ("Smokey Joe's Barbecue", "Lexington", "1101", "Lexington barbecue on South Main since 1972.", None, None, [OS_LEX, LEX_TA, VNC_DISH]),
  ("Speedy Lohr's BBQ", "Lexington", "3664", "On NC Highway 8 (Visit Lexington's current list).", None, None, [LEX_TA]),
  ("TarHeel Q", "Lexington", "6835", "On US 64 West (Visit Lexington's current list).", None, None, [LEX_TA]),
  ("Troutman's Barbecue", "Denton", "18466", "On NC Highway 109 in Denton (Visit Lexington's current list).", None, None, [LEX_TA]),
  ("Stamey's Barbecue of Tyro", "Lexington", "4524", "On NC Highway 150 in Tyro (Visit Lexington's current list).", None, None, [LEX_TA]),
  ("Stamey's Barbecue", "Greensboro", "2812", "Lexington-style pork pit-cooked over hardwood coals, on Battleground Avenue; the family's barbecue dates to 1930.", None, None, [STAMEYS, VNC_BBQ]),
  ("Stamey's Barbecue", "Greensboro", "2206", "Lexington-style pork pit-cooked over hardwood coals, on Gate City Blvd across from the coliseum.", None, None, [STAMEYS, VNC_BBQ]),
  ("Red Bridges Barbecue Lodge", "Shelby", "2000", "Lexington-style pork, family-owned since 1946 (VisitNC's current list).", None, None, [VNC_BBQ, OS_TRAIL]),
  ("Fuzzy's BBQ", "Madison", "407", "Piedmont-style barbecue in Madison since 1954 (VisitNC's current list).", None, None, [VNC_BBQ, OS_TRAIL]),
  ("Hursey's Bar-B-Q", "Burlington", "1834", "Hickory-smoked pork shoulder on South Church Street (VisitNC's current list).", None, None, [VNC_BBQ, OS_PIT]),
 ],
 "carolina hot dogs": [
  ("The Roast Grill", "Raleigh", "7", "Hot wieners with mustard, onions, chili and slaw (no ketchup) since 1940; inspected by Wake County in 2026.", None, None, [OS_DOGS, WAKE]),
  ("Snoopy's Hot Dogs and More", "Raleigh", "2431", "Dogs steamed in the bun with mustard, onions and chili; inspected by Wake County in 2026.", None, None, [OS_DOGS, WAKE]),
  ("Snoopy's Hot Dogs & More", "Raleigh", "1931", "Snoopy's first stand, on Wake Forest Road (a Wake County food-stand permit).", None, None, [OS_DOGS, WAKE]),
  ("Snoopy's Hot Dogs & More", "Raleigh", "3600", "Snoopy's on Hillsborough Street (a Wake County food-stand permit).", None, None, [OS_DOGS, WAKE]),
  ("Pulliams Hotdogs & BBQ", "Winston-Salem", "4400", "Regulars order them all the way: mustard, onions, slaw and chili.", None, None, [VNC_NASCAR, OS_DOGS]),
 ],
 "calabash": [
  ("Beck's Restaurant", "Calabash", "1014", "Calabash-style seafood: lightly breaded, perfectly fried, on River Road since the early 1940s.", None, None, [BECKS, OS_CALA]),
  ("Captain Nance's Seafood", "Calabash", "9939", "Calabash seafood from a shrimp-boat family, since 1974.", None, None, [VNC_DISH, OS_CALA]),
  ("Waterfront Seafood Shack", "Calabash", "9945", "Baskets of Calabash-style seafood on the river as the boats unload.", None, None, [VNC_DISH, OS_CALA]),
 ],
 "livermush": [
  ("Shelby Cafe", "Shelby", "220", "Livermush with breakfast, all day; a vendor at Shelby's 2025 Liver Mush Festival.", None, None, [CP_MUSH]),
 ],
 "biscuits": [
  ("Sunrise Biscuit Kitchen", "Chapel Hill", "1305", "\"Bigger Better Biscuits\" at the Franklin Street drive-thru.", None, None, [SUNRISE]),
  ("Biscuit Head", "Asheville", "733", "Big biscuits and gravy (VisitNC's current list), on Haywood Road.", None, None, [VNC_DISH]),
  ("Biscuit Head", "Asheville", "1994", "Big biscuits and gravy (VisitNC's current list), on Hendersonville Road.", None, None, [VNC_DISH]),
  ("Biscuit Head", "Asheville", "417", "Big biscuits and gravy (VisitNC's current list), on Biltmore Avenue.", None, None, [VNC_DISH]),
 ],
 "oldest": [],
}
ADDR = {}
KINDS = {"eastern bbq": ["eastern bbq"], "lexington bbq": ["lexington bbq"], "carolina hot dogs": ["carolina hot dogs"], "calabash": ["calabash"],
         "livermush": ["livermush"], "biscuits": ["biscuits"], "moravian": ["moravian"], "oldest": ["oldest"]}


def key(s):
    """The name key without a leading "the": "Loveless Cafe" is our "The Loveless Cafe"."""
    return re.sub(r"^the ", "", norm(s))


def find(name, town, num):
    k = key(name)
    hits = [i for i, n in enumerate(C["name"]) if C["city"][i] is not None and M["cities"][C["city"][i]] == town
            and (key(n) == k or key(n).startswith(k + " ") or k.startswith(key(n) + " ") or key(n).replace(" ", "") == k.replace(" ", "")
                 or (key(n).split()[:2] == k.split()[:2] and len(k.split()) >= 2))]
    if num:
        hits = [i for i in hits if (C["addr"][i] or "").split(" ")[0] == num]
    return hits


leads, n_out = [], {}
for kind, rows in GUIDES.items():
    out = []
    for name, town, num, note, founded, fnote, srcs in rows:
        hits = find(name, town, num)
        if not hits and name in ADDR:
            out.append({"name": name, "address": ADDR[name], "city": town, "zip": None, "kinds": KINDS[kind], "dishes": [], "note": note,
                        "founded": founded, "founded_note": fnote, "website": None, "open": True, "evidence_date": "2026-10",
                        "sources": srcs, "match_names": []})
            continue
        if len(hits) != 1:
            leads.append(f"- {kind}: {name} ({town}{', ' + num if num else ''}) — {len(hits)} matches in our data; not added"); continue
        i = hits[0]
        out.append({"name": C["name"][i], "address": C["addr"][i], "city": town, "zip": str(C["zip"][i]) if C["zip"][i] else None,
                    "kinds": KINDS[kind], "dishes": [], "note": note, "founded": founded, "founded_note": fnote, "website": None, "open": True,
                    "evidence_date": "2026-10", "sources": srcs, "match_names": [name.upper()] if norm(name) != norm(C["name"][i]) else []})
        if brand_of(norm_name(name)):   # a chain shows under its own spelling at every branch ("Hattie B's Hot Chicken"), whatever the listing says
            out[-1]["display"] = name
        if C["name"][i] != name and not brand_of(norm_name(name)):
            out[-1]["display"] = name   # the source's (and usually the place's own) spelling
    fn = re.sub(r"[^a-z]+", "_", kind).strip("_")
    json.dump(out, open(f"{R}/app/{fn}.json", "w"), indent=1, ensure_ascii=False)
    n_out[kind] = len(out)

open(f"{R}/app/LEADS.md", "w").write("# North Carolina research leads (not yet verified)\n\nWritten by pipeline/build_research.py.\n\n" + "\n".join(leads) + """

## Waiting for 2025-26 evidence we may use (named by a source, but nothing current found yet)
- Eastern barbecue: Bum's Restaurant (Ayden; VisitNC lists it, no style or date), Grady's Barbecue (Dudley; Our State 2013 only),
  Morris Barbeque (Hookerton; Saturdays; own site (c) 2013), Parker's Barbecue (Wilson; own site (c) 2022), Clyde Cooper's (Raleigh;
  a 2026 Wake inspection, but no page calls it eastern-style), Sam Jones BBQ (Winterville; check samjonesbbq.com's locations).
- Lexington/Piedmont: Little Richard's (Winston-Salem, Clemmons; own site undated), Short Sugar's (Reidsville; site unreachable),
  BackCountry Barbeque (Lexington; not in our map data), Bar-B-Q King (Lincolnton) and Herb's Pit (Murphy; not in our map data),
  Switzerland Cafe (Little Switzerland; own site (c) 2016).
- Hot dogs: Dick's Hot Dog Stand (Wilson, 1921), Bill's Hot Dogs (Washington, 1928; not in our map data), Paul's Place (Rocky Point),
  Kermit's (Winston-Salem; journalnow is behind a TollBit wall), Zack's (Burlington), Jay Bee's (Statesville), Hap's Grill
  (Salisbury), The Dog House (Durham): Our State 2016 names them; no 2025-26 page found. Shorty's (Wake Forest): no active Wake permit,
  so it may have closed.
- Calabash: Dockside Seafood House (not in our map data), Calabash Seafood Hut (Our State 2023 only). Ella's of Calabash burned in April
  2023 (Our State); rebuilding not confirmed.
- Fish camps (Gaston County): Twin Top Fish Camp, Catfish Cove, The Captain's Cap (Our State lists about 2020); Lineberger's is closed.
- Livermush: Countryside BBQ (Marion), Circle G (Charlotte), Tony's Ice Cream (Gastonia): Our State 2019 only.
- Moravian bakeries: Winkler Bakery (Old Salem; oldsalem.org sells Moravian cookies and sugar cake mix but gives no bakery hours),
  Dewey's Bakery (deweys.com answered 429 twice).
- Oldest places: needs a page that ties a founding year to the current address (Snappy Lunch 1923, Dick's 1921, The Roast Grill 1940,
  Sunny Side Oyster Bar 1935, Sam & Omie's 1937 are candidates).
- Closed: Wilber's Barbecue (Goldsboro) and Jack Cobb & Son (Farmville), per Our State's editor's note.
- Blocked or unusable: ncbbqsociety.com redirects to an unrelated stem-cell site (taken over); journalnow.com and greensboro.com
  redirect Claude to TollBit; project543.visitnc.com robots-blocks Claude; plus the newspapers in playbook/12-sources.md.
""")
print(n_out, "| leads:", len(leads))
