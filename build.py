#!/usr/bin/env python3
"""Build the WCW 2026 Chaos Daemons dossier: data.js + index.html + card.html."""
import json, glob, collections, os, re, unicodedata

WS = os.path.expanduser("~/.hermes/workspace/wcw-daemons")
os.makedirs(WS, exist_ok=True)

bcp_all = json.load(open("/tmp/wcw_all.json"))["active"]
dae_bcp = [p for p in bcp_all if (p.get("faction") or {}).get("name") == "Chaos Daemons"]

# ---- faction table ----
fc = collections.Counter((p.get("faction") or {}).get("name", "?") for p in bcp_all)
factions = [{"name": n, "count": c, "pct": round(c / len(bcp_all) * 100, 1)} for n, c in fc.most_common()]

# ---- hutber data ----
hut = {}
for f in sorted(glob.glob("/tmp/wcw_hutber/*.json")):
    d = json.load(open(f))
    if "error" in d:
        continue
    hut[d["player"]["name"]] = d
# alias Matej
if "MATEJ" in hut:
    hut["Matej \"Amon\" Rek"] = hut.pop("MATEJ")


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def elo_pick(elo, prefix, min_games=5):
    best = None
    for k, v in elo.items():
        if not k.startswith(prefix):
            continue
        g = int(v.get("games") or 0)
        if g < min_games:
            continue
        r = float(v["rating"])
        if best is None or r > best["rating"]:
            best = {"rating": round(r), "games": g, "scope": k, "rank": v.get("rank"), "last": v.get("last")}
    return best


ANALYSIS = json.load(open(os.path.join(os.path.dirname(__file__), "analysis.json")))

players = []
for p in dae_bcp:
    u = p.get("user") or {}
    name = f"{u.get('firstName','')} {u.get('lastName','')}".strip()
    h = hut.get(name, {})
    elo = h.get("elo", {})
    ev = h.get("events", []) or []
    dae_ev = [e for e in ev if "Daemon" in (e.get("faction") or "")]
    det = collections.Counter(e.get("detachment") for e in dae_ev if e.get("detachment"))
    rec = collections.Counter(g.get("result") for g in (h.get("recent_games") or []))
    teams = elo_pick(elo, "all_time_teams")
    small = elo_pick(elo, "all_time_small")
    glob_ = elo_pick(elo, "all_time/")
    dsv = [x for x in (elo_pick(elo, "dataslate_small") , elo_pick(elo, "dataslate/")) if x]
    ds = max(dsv, key=lambda x: x["rating"]) if dsv else None
    a = ANALYSIS.get(name, {})
    players.append({
        "id": slug(name), "name": name, "team": (p.get("team") or {}).get("name") or "—",
        "group": p.get("groupName") or "—", "fd": (p.get("subFaction") or {}).get("name") or "—",
        "bcpId": p.get("userId"),
        "teams": teams, "small": small, "global": glob_, "dataslate": ds,
        "events": [{"date": e.get("date"), "event": e.get("event"), "standing": e.get("standing"),
                    "record": e.get("record"), "faction": e.get("faction"), "detachment": e.get("detachment")}
                   for e in ev[:6]],
        "daemonsEvents": len(dae_ev), "totalEvents": len(ev),
        "detachments": [{"name": n, "count": c} for n, c in det.most_common(3)],
        "recent": {"w": rec.get("W", 0), "l": rec.get("L", 0), "d": rec.get("D", 0)},
        "usual": [{"name": n, "count": c} for n, c in (h.get("factions") or [])[:4]],
        "tier": a.get("tier", "?"), "style": a.get("style", ""), "note": a.get("note", ""),
        "watch": a.get("watch", ""),
    })

players.sort(key=lambda x: -((x["teams"] or x["small"] or {"rating": 0})["rating"]))

# detachment meta across the 20 (latest daemons event each)
latest_det = collections.Counter(x["detachments"][0]["name"] for x in players if x["detachments"])
det_meta = [{"name": n, "count": c} for n, c in latest_det.most_common()]

data = {
    "event": {"name": "WCW 2026 (World Team Championship)", "bcp": "ej81ECrIXoRh", "place": "Barcelona",
              "dates": "2026-12-03 → 12-06", "players": len(bcp_all), "faction": "Chaos Daemons",
              "count": len(dae_bcp), "pct": round(len(dae_bcp) / len(bcp_all) * 100, 1),
              "rank": next(i + 1 for i, f in enumerate(factions) if f["name"] == "Chaos Daemons"),
              "factionCount": len(factions)},
    "factions": factions, "detachments": det_meta, "players": players,
    "built": "2026-11-26",
}
open(os.path.join(WS, "data.js"), "w").write("window.WCW_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
print("players", len(players), "factions", len(factions), "detachments", det_meta)