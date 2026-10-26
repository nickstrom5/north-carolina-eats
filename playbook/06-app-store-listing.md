# App Store listing (ASO)

Written by `scripts/make-listing.py` from `site-numbers.json` (2026-10-26); re-run it after every data refresh, never hand-edit.
The machine copy is `app-store/listing.json` (read by `../scripts/asc_listing.py` once Nick creates the App Store Connect record and
adds `"com.northcarolinaeats.ios": "nc-eats"` to its FOLDERS). The URLs assume northcarolina.eatsranked.com is live; until Nick's
CNAME resolves, use https://nickstrom5.github.io/north-carolina-eats/.

## Name (30 max)
`North Carolina Eats` (19)

## Subtitle (30 max)
`Restaurants, BBQ & Biscuits` (27)

Together they index: north, carolina, eats, restaurants, bbq, biscuits. Home Screen name: NC Eats.

## Keywords (100 max)
`raleigh,charlotte,asheville,durham,greensboro,wilmington,barbecue,whole hog,lexington,hot dog,grades` (100)

- No word repeats the name or subtitle; no trademarks (no Skylight Inn, Biltmore, Cook Out, Bojangles), no "best", "top" or "#1".
- Towns are the biggest win; Winston-Salem, Chapel Hill, Cary, Greenville, Boone and the Outer Banks didn't fit, nor did livermush.
  Rotate them in after a month of App Store Connect search-term data. Apple's public search can't be used for this research (itunes.apple.com's robots.txt blocks Claude).

## Promotional text (170 max, editable any time without review)
`9 Eastern whole hog pits, 13 Lexington barbecue joints and Carolina hot dogs, checked by hand, plus Wake County's grades and 22,000+ restaurants near you.` (154)

## Description (3229 of 4,000)
```
North Carolina's restaurants, from a tray of Eastern whole hog to a Lexington plate with red slaw.

North Carolina Eats is a free guide to eating in North Carolina: 9 Eastern whole hog pits, 13 Lexington barbecue joints, 5 Carolina hot dog stands, 3 Calabash seafood houses and 5 biscuit and livermush places we checked by hand, 64 MICHELIN and James Beard honorees, Wake County's official inspection scores and grades for 2,097 places, and 22,903 restaurants, cafés, bars and bakeries in 594 towns, from Murphy to Manteo. No account, no ads.

NORTH CAROLINA GUIDES
• Eastern Whole Hog: 9 pits that cook the whole hog the eastern way, chopped and dressed with vinegar and pepper.
• Lexington Barbecue: 13 Piedmont pits for pork shoulder, red dip and red slaw.
• Carolina Hot Dogs: 5 stands serving them all the way, with chili, slaw, onions and mustard.
• Calabash Seafood: 3 places for lightly breaded, quickly fried seafood.
• Biscuits & Livermush: 5 places for scratch biscuits and the western Piedmont's livermush.
• MICHELIN & James Beard: the MICHELIN Guide's one-star restaurant, 11 Bib Gourmands and Recommended places, and James Beard winners, nominees, semifinalists and America's Classics (64 places).
• Wake County Inspections: the county's own latest score for 2,097 places, with the grade it earns (A at 90 or more), the date and the items cited.

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

An independent app, not affiliated with any restaurant, chain or government agency (including the State of North Carolina, the NC Department of Health and Human Services and Wake County), or with the MICHELIN Guide or the James Beard Foundation. MICHELIN and the MICHELIN Guide are trademarks of Michelin. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. Place data from Overture Maps Foundation (CDLA Permissive 2.0), Wake County Open Data (CC BY 4.0) and others; sources and licenses are on the About tab.
```

## What's New (1.0)
`First release: Eastern and Lexington barbecue, Carolina hot dogs, biscuits and livermush, Wake County's inspection grades and 22,000+ North Carolina restaurants.`

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
