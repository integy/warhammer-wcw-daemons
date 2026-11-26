#!/usr/bin/env python3
"""Build the WCW 2026 Group 9 dossier: source/g9.json -> data.js

g9.json = one entry per Group 9 player, merged from BCP players + listhammer lists:
  {bcpId: {name, faction, disp, team, det, itc, units:[[name,pts],...], total, tags}}

Verdicts + notes come from the scouting pass (source/group9-scout.md):
  win = 你應該贏   even = 五五   hard = 難打
"""
import json, os, collections, re, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source", "g9.json")

# faction default: (verdict, note, kill priority)
FACTION = {
    "World Eaters": ("win", "純近戰 Berzerker Warband + Vessels of Wrath：Angron、Khârn、Eightbound、Jakhals，零遠程。",
                     "Exalted Eightbound → Khârn / MoE / Lord Invocatus（Karanak）"),
    "Space Marines (Astartes)": ("even", "Terminator Storm Force：Calgar + Guilliman + 10 隻 4++ Terminator，D2 量多。",
                                 "Guilliman > Calgar（Karanak），Terminator 留 Rendmaster 疊傷"),
    "Necrons": ("even", "Lokhust Heavy Destroyer 射擊海 + C'tan。C'tan 減傷令 Bloodthirster 傷害打折。",
                "Lokhust Heavy Destroyer → Lokhust Destroyer → Hexmark"),
    "Death Guard": ("even", "Mortarion + Knight Despoiler + 3× Myphitic Blight-hauler（6 支 melta 反大）。",
                    "Blight-hauler 必先清；Mortarion 用 Skarbrand（高 D）"),
    "Orks": ("even", "Green Tide 人海（6×20 Boyz）或機械化（Gunwagon + Wazbom）：數量追唔切。",
             "Weirdboy（psychic）／Wazbom（射擊）→ 其餘靠 mission"),
    "Adeptus Custodes": ("even", "Contemptor-Galatus + Telemon + Caladius：全場最抗打，高 T 高 save。",
                         "Caladius Grav-Tank（唯一穩定殺 Bloodthirster）→ 其餘搶 objective"),
    "Tyranids": ("even", "Exocrine / Maleceptor / Tyrannofex 射擊 + Hormagaunt 海。",
                 "Exocrine、Maleceptor → Hormagaunt 用 Bloodcrushers 磨"),
    "T'au Empire": ("hard", "純射擊 castle：Crisis Sunforge（melta）+ Hammerhead + Broadside，專殺你 Bloodthirster。",
                    "Crisis Sunforge → Breacher（scoring）→ Broadside"),
    "Chaos Space Marines": ("even", "Defiler / Venomcrawler / Vashtorr / Terminator 4++，大量 D3。",
                            "Defiler → Mutilator（D3 反大）"),
    "Space Wolves": ("even", "Assault Brethren / Stormlance：Thunderwolf + Eradicator melta + Eliminator（反 character）。",
                     "Eradicator（melta）→ Eliminator（小心 Karanak）"),
    "Grey Knights": ("even", "全部 deep strike + 4++，Purifier flamer overwatch 對大隻有災難性。",
                     "GMNDK → Razorback；Purifier 要 12\"+ 外 charge"),
    "Leagues of Votann": ("even", "Thunderkyn（D3 反大）/ Hekaton 或 Cthonian Beserks 近戰海。",
                          "Brôkhyr Thunderkyn 必殺"),
    "Aeldari": ("hard", "Fire Prism / Fire Dragon（melta 反大）+ 大量 character，射擊機動。",
                "Fire Prism / Fire Dragon → character（Karanak 大餐）"),
    "Dark Angels": ("even", "Land Speeder Vengeance / Thunderstrike speeder 型，或 Inner Circle + Deathwing 慢甲。",
                    "Land Speeder Vengeance 先拆"),
    "Imperial Knights": ("even", "5 隻 knight 或 Castellan 長程炮；冇 infantry scoring 係佢弱點。",
                         "Castellan（長程炮）→ 逐隻三打一"),
    "Thousand Sons": ("even", "Magnus + Scarab Occult，psychic 反大。",
                      "Magnus 必先殺 → Sorcerer（Karanak）"),
    "Chaos Daemons": ("even", "Daemons mirror：五神混合有 psychic，或全 Lord of Change 射擊。",
                      "Lord of Change → Skarbrand 對大魔"),
    "Deathwatch": ("even", "2× DW Terminator + Fortis + Indomitor，4++ 人海。",
                   "Indomitor / Fortis → 靠磨"),
    "Adepta Sororitas": ("even", "Vahl + Paragon（反大）+ Immolator / Dominion flamer。",
                         "Vahl、Paragon → flamer 要避 overwatch"),
    "Adeptus Mechanicus": ("even", "3× Skorpius Disintegrator + Onager + Kastelan 射擊。",
                           "Skorpius Disintegrator 先"),
}

# per-player specifics: name -> (verdict|None, note, killer)
PLAYER = {
    # World Eaters
    "Sam Dickinson": ("win", "4× Berzerkers + 2× Lord on Juggernaut，呢 8 張入面最平衡。", "Lord on Juggernaut（Karanak）"),
    "Peter Duff": ("win", "3× Lord on Juggernaut + 3× Berzerkers，最多 jugger 衝鋒。", "Lord on Juggernaut"),
    "Vidente Elthar": ("win", "3× MoE + 2× Slaughterbound，character 最多 —— Karanak 天堂。", "MoE / Slaughterbound"),
    "Gabriel Benický": ("win", "標準 Berzerker Warband，冇特別 anti-tank。", "Exalted Eightbound"),
    "Loukas Benard": ("win", "Berzerker Warband + Vessels of Wrath，近戰 mirror。", "Exalted Eightbound"),
    "Charles Primard": ("win", "Berzerker Warband，Jakhals 多、scoring 單位薄。", "Exalted Eightbound"),
    "Jack Harpster": ("win", "Berzerker Warband，單位數偏多但冇射擊。", "Exalted Eightbound"),
    "Rafal Skorupa": ("win", "新手池（ITC #31695），可以搶分。", "隨意"),
    # Astartes
    "Pedro Astrategas": ("hard", "Stormlance + 3 Impulsor + 2 Thunderstrike + 2 Eradicator melta —— 射擊型 speeder，Group 9 內你最差 matchup。", "Eradicator（melta）→ Thunderstrike"),
    "Anthony Maugé": (None, "標準 Terminator Storm Force：Calgar + Guilliman + DW Terminator 4++。", "Guilliman > Calgar"),
    "Martin Petriscak": (None, "Terminator Storm Force，D2 量多，唔好正面衝 blob。", "Guilliman > Calgar"),
    "moritz Klima": (None, "Terminator Storm Force，11 個 datasheet 偏精簡。", "Guilliman > Calgar"),
    "Debliquy Cameron (Celesx)": (None, "3 Scout + 2 DW Term，最少 anti-tank 嘅一張 Terminator 殼。", "Calgar → Terminator"),
    "Mike Hodges": (None, "Terminator Storm Force，14 個 datasheet。", "Guilliman > Calgar"),
    # Necrons
    "Steven Ross": (None, "Immortals + 2× Lokhust Lord + Scarab，5 張 Necron 入面最完整。", "Lokhust Lord → Heavy Destroyer"),
    "Clément Galland": ("hard", "2× C'tan + Flayed Ones —— 5 張入面最硬，Bloodthirster 打唔入。", "Flayed Ones → 靠 mission 偷分"),
    "Eetu Peltola": (None, "Awakened Dynasty + 3× Lokhust Lord + Wraiths。", "Lokhust Lord → Wraiths"),
    "Adrien Jerphagnon (Woyd)": (None, "Cursed Legion + Skyshroud，20 個 datasheet 最多 scoring。", "Heavy Destroyer → Hexmark"),
    "Francesco Di Bonaventura": ("hard", "2× C'tan + Silent King + Tesseract Vault —— 全部係你打唔死嘅嘢，純靠 mission 搶分。", "Hexmark → mission"),
    # Custodes
    "Riley Morris": (None, "3× Galatus + 2× Telemon + Allarus，4 張 Custodes 最厚。", "Caladius（如有）→ Allarus"),
    "Lucas McQueeney": (None, "Might of the Moritoi + Auric Champions 標準甲。", "Caladius → scoring unit"),
    "Samuel Young": (None, "Honoured Companions + Might of the Moritoi。", "Caladius → scoring unit"),
    "Jasper Lange": ("hard", "2× Caladius Grav-Tank —— 4 張 Custodes 最射擊型，唯一穩定殺你 Bloodthirster。", "Caladius ×2（Skarbrand + Thirster 一起 charge）"),
    # Death Guard
    "Igor Bourjac": (None, "Paragons of Putrescence + Shamblerot，標準 Mortarion + Despoiler + hauler。", "Blight-hauler → Mortarion（Skarbrand）"),
    "Alexandre Turco": (None, "Disruption，2 Helbrute 換走部分 hauler，近戰多咗。", "Helbrute / Blight-hauler"),
    "Jakub Ovecka": ("win", "Virulent Vectorium，冇 Knight Despoiler —— 4 張 DG 最易打。", "Blight-hauler（如有）→ 其餘逐 unit 食"),
    "Stephen Walker": (None, "4× Plague Marine，最多 scoring、最磨；listhammer 未收錄唔代表弱。", "Plague Marine 靠 mission 對衝"),
    # Orks
    "Will Paul": (None, "6× Boyz + 3× Weirdboy Green Tide：120 隻，靠 mission 唔好逐隻清。", "Weirdboy ×3"),
    "John Stavroulakis": (None, "War Horde + 2× Big Mek Dakkarig + Squighog，中間型。", "Big Mek Dakkarig"),
    "Alberto Nicolas \"The Carthaginian\"": (None, "機械化：3× Gunwagon + 2× Wazbom + Ghaz + Mozrog。", "Wazbom（射擊）→ Gunwagon"),
    "Mattias Levin": (None, "Green Tide 人海 + Bully Boyz。", "Weirdboy / 靠 mission"),
    # Tyranids
    "Marek Vlnka": (None, "Invasion Fleet + 2× Exocrine + 2× Maleceptor —— 你舊 army 嘅優化版。", "Exocrine、Maleceptor"),
    "Hugh Mc Cluskey": (None, "Subterranean Assault + 3 Zoanthrope + 2 Psychophage，射擊最密。", "Zoanthrope → Psychophage"),
    "Davey Liddle": (None, "Subterranean Assault + Raveners，全靠 deep strike 偷後場 —— 留一隻 Flesh Hounds 守 home。", "Ravener → 守 home objective"),
    "Xavo Melenero L'Escamarlà": (None, "Vanguard Onslaught + 2 Broodlord + Genestealer，快攻型。", "Broodlord → Genestealer"),
    # T'au
    "Brett Smith": ("hard", "全 Group ITC 最高 #31：3× Crisis Sunforge + 3 Breacher + 2 Coldstar，最強 T'au。", "Crisis Sunforge ×3（必殺）"),
    "Leo Pageon": ("hard", "Cadre + Kauyon，仲有 2× Hammerhead 長距離反大。", "Sunforge → Hammerhead"),
    "Josh Tyler": ("hard", "Mont'ka + 2 Ghostkeel + 2 Hammerhead + 2 Broadside，最射擊型、最難。", "Hammerhead / Broadside"),
    # CSM
    "Ed Watts": ("hard", "Soulforged Warpack：2 Defiler + 2 Venomcrawler + 2 Daemon Prince + Vashtorr，CSM 最硬。", "Defiler → Daemon Prince"),
    "Thomas Cowan": (None, "Warpstrike Champions：3× Chaos Terminator + 2× Sorcerer Termi + 2× Mutilator，Disruption。", "Mutilator（D3 反大）→ Terminator（Skarbrand）"),
    "Matt Chayba": (None, "Fellhammer + Cabal：2 Red Corsairs Raider + Vashtorr + Defiler，中間型。", "Defiler → Vashtorr"),
    # Knights
    "Luis Stiemerling": ("win", "Canis Rex + Atrapos + Lancer + Crusader + Destrier：5 隻 knight、冇 infantry scoring，三打一逐隻拆。", "逐隻拆（Skarbrand + 2 Thirster）"),
    "Giri {°_°}": ("hard", "2× Castellan + 2 Armiger + Canis Rex：Castellan 長程炮會喺你埋身之前殺 Bloodthirster。", "Castellan（靠 terrain + deep strike 埋身）"),
    # Grey Knights
    "Garrett Befera": (None, "Banishers：3× Brotherhood Terminator + 2× Paladin，全部 4++ 深打，Karanak 追唔到。", "Paladin（Bloodthirster 正面撞）"),
    "Matthew Wood": (None, "Warpbane：3× Purifier（flamer overwatch 災難）+ 2× GMNDK + 2× Razorback。", "GMNDK → Razorback；12\"+ 外 charge"),
    "J Sawlaw": (None, "Warpbane 同型：Purifier flamer 係最大陷阱。", "GMNDK → Razorback"),
    # Space Wolves
    "Aidan Brocklehurst": (None, "Assault Brethren + Phobos Shadow Force + 2 Bladeguard + 2 Eliminator（anti-character）。", "Eliminator（小心 Karanak）→ Bladeguard"),
    "Gil Dias": (None, "Stormlance + 2 Impulsor + 2 Eradicator melta + Thunderwolf。", "Eradicator（melta）"),
    "Petros Kazas": ("win", "Assault Brethren + 2 Wolf Guard Terminator + Logan + Bjorn，近戰 mirror，你贏。", "Logan → Bjorn"),
    # Votann
    "Mathieu Clerc": ("hard", "Needgaârd Oathband + Farseekers：3× Brôkhyr Thunderkyn（D3 反大）+ Hekaton。", "Thunderkyn ×3 必殺"),
    "Quentin Roché": ("win", "5× Cthonian Beserks + 2 Hearthguard，近戰型，你贏。", "Hearthguard"),
    # Aeldari
    "Thomas Faulkner": ("hard", "3× Warlock Conclave + 2× Fire Prism + 6 個 character，Take and Hold。", "Fire Prism → character（Karanak）"),
    "Roberto Gaiba": ("hard", "3× Windrider + 2× Fire Dragon（melta 反大）+ Avatar。", "Fire Dragon → Avatar 用 Skarbrand"),
    # Dark Angels
    "Juuso Sipiläinen": ("hard", "3× Land Speeder + 3× Land Speeder Vengeance + 2 Thunderstrike —— 同你打慣嘅 DA speeder 一樣，Recon。", "Vengeance ×3 先拆"),
    "Roger Borras": ("win", "2× Inner Circle + 2 Deathwing Knight + Lion：硬但慢，你快過佢。", "Inner Circle → Lion"),
    # Thousand Sons
    "Pavel Samsonov": (None, "Magnus + Scarab Occult，psychic 反大。", "Magnus 必先殺"),
    "Gasper Dular": (None, "Grand Coven + Magnus 型，14 個 datasheet。", "Magnus → Sorcerer"),
    # Daemons
    "Niklas Fritschen": ("win", "同 detachment（Daemonic Incursion）五神混合：Be'lakor + GUO + LoC + Shalaxi + Skarbrand。你純 Khorne 近戰贏，佢冇 Rendmaster 疊傷。", "Shalaxi → 大魔逐隻（Skarbrand 對衝）"),
    "Lara Silva": ("hard", "Warptide + Scintillating Legion：3× Lord of Change + 2 Flamer + 2 Screamer，全 psychic 射擊，同 T'au 一樣差 matchup。", "Lord of Change ×3（terrain + deep strike）"),
    # single-faction entries
    "Jeff Cope": (None, "Black Spear：2× DW Terminator + 2 Fortis + Indomitor，4++ 人海。", "Indomitor / Fortis 靠磨"),
    "Joel Gállego": (None, "Vahl + 2 Immolator + 2 Dominion（flamer）+ Paragon（反大）。", "Paragon → Vahl；避 flamer overwatch"),
    "Maxwell Lawrence": (None, "3× Skorpius Disintegrator + 2 Onager + Kastelan，射擊型。", "Skorpius Disintegrator"),
}

ME_NOTE = ("全場最「反 character + 反大隻」嘅 melee 機器：Karanak 專殺 character、3 隻 Rendmaster 疊傷、"
           "Skarbrand + 2 Bloodthirster 打硬目標、Flesh Hounds 搶位。")
ME_WEAK = "弱點：冇射擊、12 個 datasheet、模型數少；怕 D3+ 遠程、大範圍 overwatch 同爆擊。"


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def group_units(units):
    """[[name,pts],...] -> [{n,c,p}] grouped by datasheet"""
    c = collections.Counter(n for n, _ in units)
    pts = collections.defaultdict(int)
    for n, p in units:
        pts[n] = max(pts[n], p or 0)
    out = [{"n": n, "c": k, "p": pts[n]} for n, k in c.items()]
    out.sort(key=lambda u: (-u["c"], -u["p"], u["n"]))
    return out


raw = json.load(open(SRC))
players, me = [], None
for pid, v in raw.items():
    name = v["name"]
    if name == "Eric Leung":
        me = {"name": name, "faction": v["faction"], "det": v["det"], "fd": v["disp"],
              "total": v["total"], "units": group_units(v["units"]), "note": ME_NOTE, "weak": ME_WEAK}
        continue
    fac = v["faction"]
    fdef = FACTION.get(fac, ("even", "", ""))
    ov = PLAYER.get(name, (None, None, None))
    players.append({
        "id": slug(name) or pid, "bcp": pid, "name": name, "team": v.get("team") or "—",
        "faction": fac, "det": v.get("det") or "—", "fd": v.get("disp") or "—",
        "itc": v.get("itc"), "total": v.get("total"), "tags": v.get("tags") or [],
        "verdict": ov[0] or fdef[0],
        "note": ov[1] or fdef[1],
        "killer": ov[2] or fdef[2],
        "units": group_units(v.get("units") or []),
        "models": sum(k for k in (u["c"] for u in group_units(v.get("units") or []))),
    })

rank = {"hard": 0, "even": 1, "win": 2}
players.sort(key=lambda p: (rank[p["verdict"]], p["itc"] if p["itc"] else 999999))

fc = collections.Counter(p["faction"] for p in players)
fd = collections.Counter(p["fd"] for p in players)
det = collections.Counter()
for p in players:
    for d in (p["det"] or "").split("|"):
        d = d.strip()
        if d and d != "—":
            det[d] += 1

data = {
    "event": {
        "name": "Warhammer World Championships 2026", "place": "Barcelona · Fira Montjuïc",
        "dates": "2026-12-03 → 12-06", "bcp": "ej81ECrIXoRh", "group": 9,
        "groupSize": len(players) + 1, "opponents": len(players),
        "counts": {k: sum(1 for p in players if p["verdict"] == k) for k in ("win", "even", "hard")},
    },
    "me": me,
    "factions": [{"name": n, "count": c, "pct": round(c / len(players) * 100, 1)} for n, c in fc.most_common()],
    "dispositions": [{"name": n, "count": c} for n, c in fd.most_common()],
    "detachments": [{"name": n, "count": c} for n, c in det.most_common(12)],
    "players": players,
    "built": "2026-11-26",
}

with open(os.path.join(HERE, "data.js"), "w") as f:
    f.write("window.WCW_DATA = ")
    json.dump(data, f, ensure_ascii=False, indent=1)
    f.write(";\n")

missing = [p["name"] for p in players if p["name"] not in PLAYER]
print("players", len(players), "verdicts", data["event"]["counts"])
print("factions", len(fc), "dets", len(det), "| faction-default notes:", len(missing))