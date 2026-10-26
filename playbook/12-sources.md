# North Carolina sources (checked 2026-10-26)

Every host below was robots-checked with `pipeline/check_sources.py` (ClaudeBot, Claude-User, anthropic-ai; RFC 9309 matcher; an empty
202 counts as a bot check) in its own step, before any other request. User agent on every scripted request:
`NorthCarolinaEatsBuild/1.0 (+nick@eatsranked.com)`. Raw files are in `data/raw/official/` (git-ignored, never public).

North Carolina has a **statewide official grade**, but only **Wake County** publishes its permits and inspections as open data. Every
other county's results are in the state's search portal, which we link and never copy.

## The official grade (verified in the rule text)

15A NCAC 18A .2600, "Rules Governing the Food Protection and Sanitation of Food Establishments" (PDF linked from
ehs.dph.ncdhhs.gov/rules.htm, `docs/rules/Sanitation-of-FoodEstablishments-15ANCAC18A-2600.pdf`; robots allow):
- **.2662 Grading**: a score of at least 90 percent is grade **A**; 80 to under 90 **B**; 70 to under 80 **C**. Under 70 the permit is
  revoked (G.S. 130A-23(d)). The card is black on white; local health departments may also give sanitation *awards*, which must look
  different and say "award" (never shown as a grade).
- **.2660**: the card hangs where customers see it on entering; every inspection issues a new card.
- **.2661**: the inspection form records the score; points come off per violated Food Code item.

So the app shows **the county's published score and the letter .2662 gives it** (the same letter as the card by the door), labeled
official, with the date. We compute no grade of our own, and a score the county didn't publish is "—".

## Official records

| Source | What | Terms | Cadence | Status |
|---|---|---|---|---|
| **Wake County Environmental Health & Safety** via Wake County's Open Data hub (data.wake.gov, ArcGIS Hub): "Restaurants in Wake County" `124c2187da8c41c59bde04fa67eb2872`, "Food Inspections" `ebe3ae7f76954fad81411612d7c4fb17`, "Food Inspection Violations" `9b04d0c39abd4e049cbd4656a0a04ba3` | Facilities: HSISID (= the state ID), name, address, phone, permit date, facility type, point (85% geocoded). Inspections since 2012-09-20: HSISID, date, score, type (inspection / re-inspection), inspector. Violations: HSISID, date, Food Code section, severity (Priority / Priority Foundation / Core), the item's short description, points, CDI (corrected during inspection) / R (repeat) / VR flags, inspector, comments | **CC BY 4.0** (hub `license`; "Wake County GIS shall not be held liable for any errors…; primary sources must be consulted for verification") | Layers republished nightly (hub `modified` 2026-10-25 23:30) | **used**. The layers live on `maps.wake.gov`, whose robots.txt is `User-agent: * / Disallow: /`, so that server is never called; only the hub's own CSV downloads (`data.wake.gov/api/download/v1/items/<id>/csv`, robots allow, Crawl-delay 60 honored). **The hub's export lags the layer**: it serves a file ending **2026-09-14** (81,528 inspections, 315,059 violations, 4,152 facilities) while the layer reports 82,144 / 316,215 / 4,181 records; asking for a fresh export (`redownload=true`) returned the same bytes. "Records through" is that last date. 19 inspections with score 0 are placeholders (the card never shows 0): no result. Inspector names and comment text are never read into the app or the leaderboard |
| **NC DHHS statewide inspection portal** (Custom Data Processing, `public.cdpehs.com/NCENVPBL/ESTABLISHMENT/ShowESTABLISHMENTTablePage.aspx?ESTTST_CTY=<n>`, counties numbered alphabetically: 60 Mecklenburg, 90 Union, 92 Wake) | Inspection date, premises name, address, State ID#, establishment type, final score, grade, inspector ID, report link. One page read on 2026-10-26 (Mecklenburg): 128,603 items, latest 10/25/2026 | No API and no reuse terms; robots.txt answers 404 (nothing disallowed); page says "Copyright © Custom Data Processing, Inc." | Daily | **linked, not copied**. Each place outside Wake links its county's page (the page renders server-side; the filters are ASP.NET postbacks, so there is no per-place link). It has "Export to Excel/CSV" buttons: **not used without Nick's yes** (prompt). A public-records request for a statewide extract is drafted in `playbook/records-requests.md` |
| Other counties | The prompt's survey: Mecklenburg, Guilford, Forsyth, Cumberland, Durham, New Hanover publish no bulk data; Durham (2017 Excel) and Pitt (2014–2017 ArcGIS) are history only | — | — | **not used**. mecknc.gov's robots.txt disallows ClaudeBot and anthropic-ai; unioncountync.gov and inspections.myhealthdepartment.com/ucnc answer a bot check; buncombenc.gov/849 answers a bot check and redirects to a vendor's sales page (never linked); Buncombe's Accela search (robots allow) is search only |
| **Alcohol**: NC ABC Commission permit search (abc2.nc.gov/Search/Permit) | On-premises permit types (malt, wine, mixed beverages) by business | robots.txt 404 | — | **not used**: a search form with no export; never crawled. "Serves alcohol" is "—" everywhere, never "No". Records request drafted |
| **Property values**: Wake parcels (`maps.wake.gov` Property/Parcels) | Building value, year built | CC BY 4.0 (item page) | — | **not used**: the server's robots.txt disallows all agents. No property board |

## Statewide base

| Source | What | Terms | Cadence | Rows |
|---|---|---|---|---|
| Overture Maps places `2026-10-21.0` (newest release) | Map listings, state and county outlines (land division areas, so the sounds and the Outer Banks follow the shore), address points | CDLA-Permissive-2.0 / Apache-2.0 + Foursquare NOTICE | Monthly | 45,517 North Carolina eating/drinking listings (`region = 'NC'`); 587,208 places in the state; 6.10 M address points; 100 counties |
| UCSD Google Local 2021 (`meta-North_Carolina.json.gz`, mcauleylab.ucsd.edu, 37.1 MB; no robots.txt) | 2021 ratings, reviews, price, 2021 closures: **web leaderboard only, never the app** | research dataset | frozen Sep 2021 | 28,783 food listings (3,285 closed by 2021); 21,953 matched to Overture listings |
| BLS QCEW, NAICS 722, 2026 Q1 (from the prompt) | Private eating and drinking places: 23,884 | public | quarterly | benchmark only |

Spillover towns over the Virginia, Tennessee, Georgia and South Carolina lines are clipped three ways: Overture's own `region = 'NC'`,
an NC ZIP (27xxx–28xxx), and the state outline with a 100 m buffer.

## Calibration (2026-10-26, `data/nc/calibration*.json`)

Wake County permits every place that sells food prepared on site, so its list is a **real rate**, not a floor (unlike Tennessee's
beer permits). Each Wake map listing was checked against the 4,152 active permits (same business name nearby, or the same street
address with a distinctive name word in common).

| Kind of listing | On Wake's permit list |
|---|---|
| Meta + open in Google 2021 | 79.9% of 1,726 |
| Meta only | 40.6% of 1,547 |
| Brand feed (chain store lists) only | 57.9% of 76 |
| Microsoft only | 34.8% of 187 |
| Foursquare/BrightQuery/Microsoft + Google 2021 | 24.3% of 538 |
| BrightQuery only | 13.1% of 475 |
| Foursquare only | 11.7% of 377 |
| Google 2021 says closed / Overture says closed | 2.8% / 2.5% |
| App grouping: Meta ≥ 0.95 | 76.4% of 2,235 |
| App grouping: Meta 0.90–0.95 with a website | 42.6% of 352 |
| App grouping: Meta 0.90–0.95, no website | 22.1% of 86 |
| App grouping: Meta < 0.90 | 21.5% of 615 |
| App grouping: BrightQuery ≥ 0.95 | 21.8% of 473 |

Same order as Colorado, Texas, Idaho, Arizona and Tennessee, so the same keep rules: web = Meta and chain store lists (plus official
and hand-checked), minus what Google showed closed in 2021; app = Meta ≥ 0.95, Meta 0.90–0.95 with a website, chain store lists,
official, hand-checked. The other way, the open map listings hold **70.6%** of Wake's 3,123 permitted restaurants, food stands and
limited food services; permitted restaurants among the rest are added from the list (191 shown after the non-restaurant rules: Wake's
"Restaurant" permit also covers hotel breakfast rooms, employer cafeterias, retirement dining rooms, golf snack bars and cinemas, so a
row from the permit list alone needs a food word or a chain's name, and named employers, hotels, campuses and clubs stay hidden).

Result (first build): **web 28,655 restaurants** in 645 towns (QCEW 23,884: +20%, as in other states' web builds); **app 22,933
restaurants** (−4%). Wake inspection results on 2,102 app places (latest grades: almost all A; 12 B on the web build, no C).

## Honors (data/research)

- **MICHELIN Guide American South 2026** (revealed 2026-10-21). guide.michelin.com answers scripts with an empty 202 (bot challenge,
  never retried); read 2026-10-26 with Claude's web fetcher. North Carolina: **58 restaurants: 1 One Star** (Counter, Charlotte),
  **11 Bib Gourmand** (Luminosa, Little Chango, Mother in Asheville; Mala Pata, Sam Jones BBQ, Ajja in Raleigh; Prime Barbecue,
  Knightdale; Lang Van and The Story of "Mi Cariño", Charlotte; Ideal's, Durham; Tesoro, Carrboro), **46 Selected**, no Green Stars.
  The prompt's September list (47, 7 Bibs) was the 2025 selection. Each restaurant page read for its address (`michelin.json`).
  The **Bib Gourmand filter** applies (BIB-GOURMAND-FILTER.md). Good Hot Fish showed a Bib icon in one reading of the list, but it is
  not on the Bib filter page and the counts add up without it: Selected (recheck in a browser before launch).
- **James Beard** (`jbf.json`; Wikipedia's award lists and the places' own sites; jamesbeard.org's award search renders client-side):
  America's Classics Skylight Inn BBQ (Ayden) and Lexington Barbecue (both 2003); Crook's Corner (2011) **closed** June 2021, no
  reopening found (`closed.json`). Winners: Andrea Reusing, Lantern (Best Chef: Southeast 2011; its own site posts hours, undated);
  Ashley Christensen, Poole's (Best Chef: Southeast 2014, Outstanding Chef 2019); Chai Pani (Outstanding Restaurant 2022; moved in
  2024 to 32 Banks Ave; 2026 Outstanding Restaurateur finalist, WFAE); Cúrate (Outstanding Hospitality 2022); Ricky Moore, Saltbox
  Seafood Joint (Best Chef: Southeast 2022); Taylor Montgomery, Montgomery Sky Farm, Leicester (Best Chef: Southeast 2026: ticketed
  farm dinners, no daily service; its site answered 429, so not yet placed). 2026 semifinalist Matt Dawes, Bull and Beggar (WFAE).

## Press and tourism hosts (robots-checked 2026-10-26)

- **Usable:** ourstate.com, visitnc.com, ncbbqsociety.com (Historic Barbecue Trail), oldsalem.org, ncdcr.gov, wfae.org, whqr.org,
  publicradioeast.org, indyweek.com, chapelboro.com, salisburypost.com, hickoryrecord.com, cardinalpine.com, reflector.com,
  mcdowellnews.com, dailyadvance.com, reflector.com, wcnc.com, wsoctv.com, wfmynews2.com, charlottesgotalot.com, visitraleigh.com,
  wilmingtonandbeaches.com, outerbanks.org, thelocalpalate.com, tasteofthesouthmagazine.com, cardinalpine.com, en.wikipedia.org,
  jamesbeard.org, visitlexingtonnc.com, and the restaurants' own sites checked so far.
- **Blocked (never cited):** citizen-times.com, starnewsonline.com, fayobserver.com, gastongazette.com, shelbystar.com,
  southernliving.com, eater.com, seriouseats.com, nytimes.com, qcitymetro.com (robots disallow all three Claude agents); wral.com,
  mountainx.com, wlos.com, wunc.org, wbtv.com, wect.com, witn.com, ncpedia.org, the-dispatch.com, stateportpilot.com,
  washingtonpost.com (robots disallow ClaudeBot and/or anthropic-ai); gardenandgun.com, bonappetit.com (robots disallow ClaudeBot and
  Claude-User); exploreasheville.com, visitwinstonsalem.com, chaipani.com, businessnc.com, brunswickbeacon.com, atlasobscura.com (bot
  check); axios.com (answered Claude's fetcher 403); newsobserver.com, charlotteobserver.com, carolina.eater.com,
  charlottemagazine.com, ncfoodtrails.com (unreachable: treated as blocked); journalnow.com and greensboro.com (robots allow, but
  they redirect Claude's fetcher to a TollBit paywall: treated as blocked); project543.visitnc.com (robots disallow).
- **Taken over:** ncbbqsociety.com (the NC Barbecue Society, whose Historic Barbecue Trail other states' notes cite) now 301-redirects
  to an unrelated stem-cell site: never cited, and on the website blocklist.
- **Read by Claude's web fetcher only:** guide.michelin.com answers scripts with an empty 202 (AWS WAF), so its pages were read with
  the fetcher (`check_sources.READ_BY_FETCHER`), never by a script.

## Adult venues

`data/research/adult_venues.json` starts empty; the first build removed three clubs by name and Overture's adult category (Onyx,
Cheetah, Rick's Cabaret). A checked address list (Colorado's lesson: clubs under plain trade names) is still to do before the app ships.
