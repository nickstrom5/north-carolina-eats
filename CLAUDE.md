# North Carolina Eats (nc-eats) — notes for Claude Code sessions

Started 2026-10-26 from `../state-prompts/NORTH_CAROLINA_PROMPT.md` and `../STATE_EATS_PLAYBOOK.md` (read both). Pipeline ported from
`../tn-eats/` (inspection board after `../oh-eats/`); `tracking_params.py`, `injection.py` from co-eats; `check_websites.py` from oh-eats;
website blocklist = union of oh/co/pa/tn (879). Never modify another state's folder. Leaderboard artifact link in `LOCAL.md`.

- Brand (Nick, 2026-10-26, `playbook/05-naming.md`): "North Carolina Eats", subtitle "Restaurants, BBQ & Biscuits", Home Screen "NC Eats";
  icon = buttermilk biscuit on flag red #B31942 (`scripts/icon-concepts.swift` `biscuit()`, passes icon-style check); palette flag navy
  #13294B + red #B31942; header = mountains-to-sea horizon. Bib Gourmand filter applies (11 Bibs).
- Sources: `playbook/12-sources.md`. Statewide grade = rule .2662 letter of the county's published score. Only Wake County publishes
  (data.wake.gov hub CSVs, CC BY 4.0; maps.wake.gov robots-blocked, never called; hub export ends 2026-09-14). Other counties: state
  portal linked per county (`official.PORTAL` + `COUNTY_NO`), never copied. Nick chose: records request first
  (`playbook/records-requests.md`, drafts, Nick sends from his email; not sent yet).
- Rebuild: `cd pipeline && ../.venv/bin/python listings.py && ../.venv/bin/python geocode_official.py && ../.venv/bin/python calibrate.py &&
  ../.venv/bin/python northcarolina.py && NC_APP=1 ../.venv/bin/python northcarolina.py`, then `.venv/bin/python scripts/make-leaderboard.py`
  and republish site/index.html with northcarolina.json, nc_detail.json, nc_shapes.json.
- Link check: `cd pipeline && CHECK_WORKERS=4 ../.venv/bin/python check_websites.py [--retry-transient]`, started detached with
  `os.setsid()` (an app restart still killed the first run at 12,500/13,711; saves every 500, atomic). Check `data/check_websites*.log`;
  back up `data/nc/website_check.json` before stopping one; then re-export the app (`NC_APP=1`) and copy it into `NorthCarolinaEats/Resources`.
  All three passes done 2026-10-26 (11,296 links ok); app and leaderboard re-exported with them.
- Research: `pipeline/build_research.py` (evidence standard in its docstring) -> `data/research/app/*.json` + `LEADS.md`. Guides today:
  Eastern whole hog 9, Lexington 13, Carolina hot dogs 5, Calabash 3, biscuits/livermush 5; Moravian and oldest empty (leads).
  ncbbqsociety.com is taken over (blocklisted); journalnow/greensboro.com are TollBit-walled; guide.michelin.com is read only with
  Claude's web fetcher (`check_sources.READ_BY_FETCHER`).

## App (ported 2026-10-26 from tn-eats, inspections after oh-eats)
- `NorthCarolinaEats/` (bundle com.northcarolinaeats.ios, Home Screen "NC Eats"); `xcodegen generate`; build with
  `DEVELOPER_DIR="/Applications/Xcode 1.app/Contents/Developer"` (27.1, 27A9275 on 2026-10-26: check it's a public release before any
  archive), `-derivedDataPath DerivedData`. Own simulator in `.simulators`: "NC Eats 6.9" 66B43CFC-9809-4BBD-8F5B-FE19D1F2B870 (iOS 27.0).
- Wake inspections: core `in` = [jur, grade index, date, score], detail `in` = {n, h: [[date, grade, score, reinspection]], i: items};
  `GradeCard` draws the card (black on white); other counties link their portal page (`AppModel.portalURL`). Inspections guide sorts:
  latest, highest score, lowest score, nearest; rows show the street address, grade, score and month.
- Search: NC guide phrases; "barbecue" and "bbq" find the same places. OTA data updates (`Services/DataUpdates.swift`, shared copy) came
  with the port.
- Unit tests: 50 run 2026-10-26, all pass but the two ShareLinkTests that need `docs/data` (re-run after the site build). UI tests
  ported, not run.

## Website (ported 2026-10-26 from tn-eats, inspections after oh-eats)
- `scripts/make-site.py` -> `docs/` (BASE /north-carolina-eats until `NC_DOMAIN=northcarolina.eatsranked.com`); `scripts/explore.js` is the
  web app (keys `nceats-`); `scripts/qa-site.py [--static]` checks both (served under /north-carolina-eats/ on a free port).
- A hand-checked guide gets a page once it holds `MIN_GUIDE` (4) places; the web app and the app show a guide once it has one. Today:
  pages for Eastern, Lexington, hot dogs, biscuits; Calabash (3) only in the app and web app; Moravian and oldest nowhere yet.
- Grades: `north-carolina-restaurant-grades.html` explains rule .2662, counts Wake's latest grades and links all 100 counties' pages in
  the state's search (`portal` + `county_no` in the app data). No page lists places by score; the web app's Wake County Inspections
  guide opens on the latest inspections. qa-site.py fails if any published grade isn't the letter .2662 gives its score
  (mutation-checked 2026-10-26: a B on a 99.5 is caught).
- OTA: `python3 scripts/publish_app_data.py` after every export copied into `NorthCarolinaEats/Resources` (first copy 2026-10-26.1).
- Screens: `bash scripts/capture-screenshots.sh "NC Eats 6.9"`, then `scripts/site-images.sh` and make-site.py again.

## Still to do
1. Screenshots (`capture-screenshots.sh`, `site-images.sh`), UI tests, `make-listing.py`, review reply (playbook/13).
2. Research gaps (`data/research/app/LEADS.md`): Moravian bakeries, oldest places, fish camps, more hot dogs and Calabash; Montgomery Sky
   Farm's address; Lantern's dated source; Good Hot Fish's MICHELIN level in a browser; adult-venue address list.
3. Nick: send the DHHS records request (draft in `playbook/records-requests.md`); later repo/Pages, Cloudflare CNAME `northcarolina`,
   ASC record. Nothing pushed.
