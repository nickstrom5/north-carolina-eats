"""Official North Carolina records -> data/raw/official/ (git-ignored). Every host was robots-checked first (check_sources.py).

- Wake County Environmental Health & Safety, through Wake County's Open Data hub (data.wake.gov, ArcGIS Hub, CC BY 4.0):
  "Restaurants in Wake County" (item 124c2187da8c41c59bde04fa67eb2872), "Food Inspections" (ebe3ae7f76954fad81411612d7c4fb17) and
  "Food Inspection Violations" (9b04d0c39abd4e049cbd4656a0a04ba3), each as the hub's own CSV download. The layers behind them live on
  maps.wake.gov, whose robots.txt disallows every agent, so we never call that server: only the hub's download links (data.wake.gov
  allows /api/), one request a minute (its Crawl-delay is 60).
"""
import json, os, sys, time
import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "official")
UA = {"User-Agent": "NorthCarolinaEatsBuild/1.0 (+nick@eatsranked.com)"}
HUB = "https://data.wake.gov/api"
WAKE = {"wake_restaurants": ("124c2187da8c41c59bde04fa67eb2872", 0),
        "wake_inspections": ("ebe3ae7f76954fad81411612d7c4fb17", 1),
        "wake_violations": ("9b04d0c39abd4e049cbd4656a0a04ba3", 2)}
DELAY = 61       # data.wake.gov robots.txt: Crawl-delay: 60
os.makedirs(OUT, exist_ok=True)
_last = [0.0]


def get(url, **kw):
    wait = _last[0] + DELAY - time.time()
    if wait > 0:
        time.sleep(wait)
    try:
        r = requests.get(url, headers=UA, timeout=900, **kw)
    finally:
        _last[0] = time.time()
    r.raise_for_status()
    return r


def wake():
    meta = {}
    for name, (item, layer) in WAKE.items():
        m = get(f"{HUB}/v3/datasets/{item}_{layer}").json()["data"]["attributes"]
        meta[name] = {k: m.get(k) for k in ("name", "license", "licenseInfo", "recordCount", "modified", "url")}
        meta[name]["fields"] = [f["name"] for f in m.get("fields") or []]
        # the hub serves a cached export unless asked for a fresh one (its first file stopped at 2026-09-14 while the layer had newer rows)
        r = get(f"{HUB}/download/v1/items/{item}/csv", params={"layers": layer, "redownload": "true"})
        open(f"{OUT}/{name}.csv", "wb").write(r.content)
        meta[name]["bytes"] = len(r.content)
        print(name, m.get("recordCount"), "rows;", len(r.content), "bytes", flush=True)
    meta["fetched"] = time.strftime("%Y-%m-%d")
    json.dump(meta, open(f"{OUT}/wake_meta.json", "w"), indent=1)


if __name__ == "__main__":
    for w in sys.argv[1:] or ["wake"]:
        globals()[w]()
