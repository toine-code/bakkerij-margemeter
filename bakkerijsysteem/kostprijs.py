#!/usr/bin/env python3
"""
De rekenkern: FIFO-voorraad, receptuur op bakkerspercentage, kostprijs en marge.

Twee kostprijzen per product, en het verschil ertussen is waar het om draait:

  FIFO             wat je product nu kost volgens je eigen voorraad, oudste
                   partij eerst. Dit is wat je boekhouder ziet.
  Vervangingswaarde wat het product kost als je alle grondstoffen vandaag zou
                   moeten bijkopen, geschat met de marktnoteringen.

Zolang je op oude, goedkope voorraad draait ziet je marge er goed uit terwijl de
markt allang is doorgestegen. Dit systeem laat zien wanneer die klap komt.

    python3 kostprijs.py        toont het overzicht in de terminal
"""

import datetime
import json
import pathlib

DATA = pathlib.Path(__file__).parent / "data"

GROEN, ORANJE = 65.0, 55.0   # margegrenzen in procenten, bruto na directe productiekosten


# ---------------------------------------------------------------------------
# Laden
# ---------------------------------------------------------------------------
def laad():
    def lees(naam, leeg):
        pad = DATA / naam
        return json.loads(pad.read_text()) if pad.exists() else leeg

    grond = lees("grondstoffen.json", {"grondstoffen": [], "vaste_kosten": {}})
    return {
        "vaste_kosten": grond.get("vaste_kosten", {}),
        "grondstoffen": {g["id"]: g for g in grond.get("grondstoffen", [])},
        "recepten": lees("recepten.json", {"recepten": []})["recepten"],
        "leveringen": lees("inkoop.json", {"leveringen": []})["leveringen"],
        "noteringen": lees("noteringen.json", {"noteringen": {}}),
    }


# ---------------------------------------------------------------------------
# FIFO
# ---------------------------------------------------------------------------
def lagen_van(db, gid):
    """Alle inkooplagen met restant, oudste eerst. Dat is de FIFO-volgorde."""
    lagen = [l for l in db["leveringen"] if l["grondstof"] == gid and l["restant"] > 0]
    return sorted(lagen, key=lambda l: l["datum"])


def voorraad(db, gid):
    return sum(l["restant"] for l in lagen_van(db, gid))


def fifo_kosten(db, gid, hoeveelheid):
    """
    Wat kost het om deze hoeveelheid uit de voorraad te halen, oudste partij
    eerst. Is de voorraad te klein, dan rekenen we de rest tegen de laatst
    bekende inkoopprijs en melden we het tekort.
    """
    rest = hoeveelheid
    kosten = 0.0
    gebruikt = []
    for laag in lagen_van(db, gid):
        if rest <= 1e-9:
            break
        pak = min(rest, laag["restant"])
        kosten += pak * laag["prijs_per_100"] / 100.0
        gebruikt.append({"laag": laag["id"], "datum": laag["datum"],
                         "hoeveelheid": round(pak, 4),
                         "prijs_per_100": laag["prijs_per_100"]})
        rest -= pak
    tekort = 0.0
    if rest > 1e-9:
        tekort = rest
        prijs = db["grondstoffen"].get(gid, {}).get("laatste_prijs_per_100", 0.0)
        kosten += rest * prijs / 100.0
    return kosten, gebruikt, tekort


def fifo_prijs_per_100(db, gid):
    """Gewogen prijs per 100 van wat er nu in het schap ligt."""
    lagen = lagen_van(db, gid)
    totaal = sum(l["restant"] for l in lagen)
    if not totaal:
        return db["grondstoffen"].get(gid, {}).get("laatste_prijs_per_100", 0.0)
    return sum(l["restant"] * l["prijs_per_100"] for l in lagen) / totaal


# ---------------------------------------------------------------------------
# Marktkoppeling
# ---------------------------------------------------------------------------
def _waarde_op(reeks, datum):
    gekozen = None
    for d, waarde in reeks:
        if d <= datum:
            gekozen = waarde
        else:
            break
    if gekozen is None and reeks:
        gekozen = reeks[0][1]
    return gekozen


def marktbeweging(db, gid):
    """
    Hoeveel de markt bewoog sinds jouw laatste levering van deze grondstof,
    al vermenigvuldigd met de doorwerking.

    Bloem is geen tarwe: er zit maalloon, transport en marge van de molenaar
    tussen. De doorwerking in grondstoffen.json zegt welk deel van een
    marktbeweging in jouw inkoopprijs terechtkomt.
    """
    g = db["grondstoffen"].get(gid)
    if not g or not g.get("notering"):
        return None
    notering = db["noteringen"].get("noteringen", {}).get(g["notering"])
    if not notering or not notering.get("reeks"):
        return None

    leveringen = [l for l in db["leveringen"] if l["grondstof"] == gid]
    if not leveringen:
        return None
    laatste = max(leveringen, key=lambda l: l["datum"])

    toen = _waarde_op(notering["reeks"], laatste["datum"])
    nu = notering["reeks"][-1][1]
    if not toen:
        return None
    ruw = (nu / toen - 1) * 100
    return {
        "notering": notering["naam"],
        "notering_id": notering["id"],
        "sinds": laatste["datum"],
        "waarde_toen": toen,
        "waarde_nu": nu,
        "eenheid": notering["eenheid"],
        "markt_pct": round(ruw, 1),
        "doorwerking": g["doorwerking"],
        "effect_pct": round(ruw * g["doorwerking"], 1),
        "verandering_jaar": notering.get("verandering_jaar"),
    }


def vervangingsprijs_per_100(db, gid):
    """Wat je vandaag betaalt als je moet bijkopen."""
    g = db["grondstoffen"].get(gid, {})
    basis = g.get("laatste_prijs_per_100", 0.0)
    beweging = marktbeweging(db, gid)
    if not beweging:
        return basis, None
    return basis * (1 + beweging["effect_pct"] / 100.0), beweging


# ---------------------------------------------------------------------------
# Recepten
# ---------------------------------------------------------------------------
def schuiffactor(db, gid, schuiven):
    groep = db["grondstoffen"].get(gid, {}).get("groep", "")
    return 1 + (schuiven or {}).get(groep, 0.0) / 100.0


def kosten_van(db, gid, hoeveelheid, prijsbron, schuiven):
    """
    Wat kost deze hoeveelheid volgens de gekozen bril.

    fifo       loopt de echte partijen af, oudste eerst
    scenario   doet hetzelfde en zet de schuif van die groep erbovenop, zodat
               het scenario zonder schuiven exact gelijk is aan vandaag
    vervanging rekent tegen de geschatte prijs van vandaag bijkopen
    """
    if prijsbron == "vervanging":
        prijs, _ = vervangingsprijs_per_100(db, gid)
        return hoeveelheid * prijs / 100.0, [], 0.0
    kosten, lagen, tekort = fifo_kosten(db, gid, hoeveelheid)
    if prijsbron == "scenario":
        kosten *= schuiffactor(db, gid, schuiven)
    return kosten, lagen, tekort


def bereken_recept(db, recept, prijsbron="fifo", schuiven=None):
    """
    prijsbron 'fifo'         rekent uit de voorraad, oudste partij eerst
    prijsbron 'vervanging'   rekent alsof je alles vandaag moet bijkopen
    prijsbron 'scenario'     rekent de FIFO-prijs met jouw schuiven erbovenop
    """
    vaste = db["vaste_kosten"]
    pct = recept["percentages"]
    totaal_pct = sum(pct.values())
    meel = recept["meelbasis_kg"]
    deeg_kg = meel * totaal_pct / 100.0
    stuks = int(deeg_kg * 1000 // recept["deeggewicht_g"])
    stuks = max(stuks, 1)

    regels = []
    grondstofkosten = 0.0
    tekorten = []
    for gid, percentage in sorted(pct.items(), key=lambda kv: -kv[1]):
        hoeveelheid = meel * percentage / 100.0
        kosten, gebruikt, tekort = kosten_van(db, gid, hoeveelheid, prijsbron, schuiven)
        if tekort > 0 and prijsbron == "fifo":
            tekorten.append({"grondstof": gid, "tekort": round(tekort, 2)})
        grondstofkosten += kosten
        g = db["grondstoffen"].get(gid, {})
        regels.append({
            "grondstof": gid, "naam": g.get("naam", gid), "groep": g.get("groep", ""),
            "percentage": percentage, "hoeveelheid": round(hoeveelheid, 3),
            "eenheid": g.get("eenheid", "kg"),
            "kosten": round(kosten, 4),
            "per_stuk": round(kosten / stuks, 4),
            "lagen": gebruikt,
        })

    garnering = 0.0
    for gid, per_stuk in recept.get("garnering", {}).items():
        hoeveelheid = per_stuk * stuks
        kosten, _, tekort = kosten_van(db, gid, hoeveelheid, prijsbron, schuiven)
        if tekort > 0 and prijsbron == "fifo":
            tekorten.append({"grondstof": gid, "tekort": round(tekort, 2)})
        garnering += kosten
        g = db["grondstoffen"].get(gid, {})
        regels.append({
            "grondstof": gid, "naam": g.get("naam", gid) + " (garnering)",
            "groep": g.get("groep", ""), "percentage": None,
            "hoeveelheid": round(hoeveelheid, 3), "eenheid": g.get("eenheid", "kg"),
            "kosten": round(kosten, 4), "per_stuk": round(kosten / stuks, 4), "lagen": [],
        })

    verpakking = 0.0
    for gid, per_stuk in recept.get("verpakking", {}).items():
        aantal = per_stuk * stuks
        kosten, _, _ = kosten_van(db, gid, aantal, prijsbron, schuiven)
        verpakking += kosten

    loonfactor = (1 + (schuiven or {}).get("Loon en energie", 0.0) / 100.0) if prijsbron == "scenario" else 1.0
    arbeid = recept["arbeid_min"] / 60.0 * vaste.get("uurloon_bakkerij", 0.0) * loonfactor
    oven = recept["oven_min"] / 60.0 * vaste.get("ovenuur", 0.0) * loonfactor

    batchkosten = grondstofkosten + garnering + verpakking + arbeid + oven
    kostprijs = batchkosten / stuks
    btw = vaste.get("btw_brood_banket", 0.09)
    verkoop_excl = recept["verkoop_incl"] / (1 + btw)
    marge = verkoop_excl - kostprijs

    return {
        "id": recept["id"], "naam": recept["naam"], "groep": recept["groep"],
        "prijsbron": prijsbron,
        "meelbasis_kg": meel, "totaal_percentage": round(totaal_pct, 1),
        "deeg_kg": round(deeg_kg, 2), "stuks_per_batch": stuks,
        "deeggewicht_g": recept["deeggewicht_g"],
        "bakverlies_pct": recept["bakverlies_pct"],
        "eindgewicht_g": round(recept["deeggewicht_g"] * (1 - recept["bakverlies_pct"] / 100.0)),
        "grondstoffen": round(grondstofkosten / stuks, 4),
        "garnering": round(garnering / stuks, 4),
        "verpakking": round(verpakking / stuks, 4),
        "arbeid": round(arbeid / stuks, 4),
        "oven": round(oven / stuks, 4),
        "arbeid_min": recept["arbeid_min"], "oven_min": recept["oven_min"],
        "kostprijs": round(kostprijs, 4),
        "verkoop_incl": recept["verkoop_incl"],
        "verkoop_excl": round(verkoop_excl, 4),
        "marge": round(marge, 4),
        "marge_pct": round(marge / verkoop_excl * 100, 1),
        "per_week": recept["per_week"],
        "week_marge": round(marge * recept["per_week"], 2),
        "week_omzet": round(verkoop_excl * recept["per_week"], 2),
        "regels": regels,
        "tekorten": tekorten,
    }


def kleur(pct):
    return "goed" if pct >= GROEN else ("let-op" if pct >= ORANJE else "verlies")


# ---------------------------------------------------------------------------
# Voorraad vooruitkijken
# ---------------------------------------------------------------------------
def weekverbruik(db):
    """Hoeveel van elke grondstof er per week doorheen gaat."""
    verbruik = {}
    for recept in db["recepten"]:
        berekend = bereken_recept(db, recept, "fifo")
        batches = recept["per_week"] / float(berekend["stuks_per_batch"])
        for gid, percentage in recept["percentages"].items():
            verbruik[gid] = verbruik.get(gid, 0.0) + batches * recept["meelbasis_kg"] * percentage / 100.0
        for gid, per_stuk in recept.get("garnering", {}).items():
            verbruik[gid] = verbruik.get(gid, 0.0) + per_stuk * recept["per_week"]
        for gid, per_stuk in recept.get("verpakking", {}).items():
            verbruik[gid] = verbruik.get(gid, 0.0) + per_stuk * recept["per_week"]
    return verbruik


def voorraadbeeld(db):
    """Per grondstof: voorraad, dekking in weken, en wat de prijs gaat doen."""
    verbruik = weekverbruik(db)
    uit = []
    for gid, g in db["grondstoffen"].items():
        lagen = lagen_van(db, gid)
        totaal = sum(l["restant"] for l in lagen)
        per_week = verbruik.get(gid, 0.0)
        fifo = fifo_prijs_per_100(db, gid)
        vervanging, beweging = vervangingsprijs_per_100(db, gid)
        oudste = lagen[0] if lagen else None
        weken_oudste = (oudste["restant"] / per_week) if (oudste and per_week > 0) else None
        uit.append({
            "id": gid, "naam": g["naam"], "groep": g["groep"], "eenheid": g["eenheid"],
            "leverancier": g.get("leverancier"),
            "voorraad": round(totaal, 2),
            "per_week": round(per_week, 2),
            "weken_dekking": round(totaal / per_week, 1) if per_week > 0 else None,
            "lagen": len(lagen),
            "fifo_per_100": round(fifo, 2),
            "laatste_prijs_per_100": g["laatste_prijs_per_100"],
            "vervanging_per_100": round(vervanging, 2),
            "verschil_pct": round((vervanging / fifo - 1) * 100, 1) if fifo else None,
            "oudste_laag": ({"datum": oudste["datum"], "restant": round(oudste["restant"], 1),
                             "prijs_per_100": oudste["prijs_per_100"],
                             "weken": round(weken_oudste, 1) if weken_oudste else None}
                            if oudste else None),
            "markt": beweging,
            "voorraadwaarde": round(totaal * fifo / 100.0, 2),
        })
    uit.sort(key=lambda r: (r["verschil_pct"] is None, -(r["verschil_pct"] or 0)))
    return uit


# ---------------------------------------------------------------------------
# Overzicht
# ---------------------------------------------------------------------------
def scenario_presets(db):
    """
    Wat de markt het afgelopen jaar deed, per grondstofgroep, gewogen naar hoeveel
    je van elke grondstof verbruikt. Grondstoffen zonder notering tellen als nul,
    want die bewegen niet mee met de beurs.
    """
    verbruik = weekverbruik(db)
    per_groep = {}
    for gid, g in db["grondstoffen"].items():
        waarde = verbruik.get(gid, 0.0) * fifo_prijs_per_100(db, gid) / 100.0
        if waarde <= 0:
            continue
        effect = 0.0
        if g.get("notering"):
            n = db["noteringen"].get("noteringen", {}).get(g["notering"])
            if n and n.get("verandering_jaar") is not None:
                effect = n["verandering_jaar"] * g["doorwerking"]
        bucket = per_groep.setdefault(g["groep"], {"waarde": 0.0, "effect": 0.0})
        bucket["waarde"] += waarde
        bucket["effect"] += waarde * effect
    presets = {}
    for groep, b in per_groep.items():
        waarde = round(b["effect"] / b["waarde"], 1) if b["waarde"] else 0.0
        # onder een half procent is het ruis, daar zet je geen schuif voor om
        presets[groep] = waarde if abs(waarde) >= 0.5 else 0.0
    return presets


def overzicht(db=None, schuiven=None):
    db = db or laad()
    schuiven = schuiven or {}
    btw = db["vaste_kosten"].get("btw_brood_banket", 0.09)
    producten = []
    for recept in db["recepten"]:
        nu = bereken_recept(db, recept, "fifo")
        vervanging = bereken_recept(db, recept, "vervanging")
        scenario = bereken_recept(db, recept, "scenario", schuiven)
        nu["kleur"] = kleur(nu["marge_pct"])

        def blok(b):
            nodig = b["kostprijs"] / (1 - nu["marge_pct"] / 100.0) * (1 + btw) if nu["marge_pct"] < 100 else None
            return {
                "kostprijs": b["kostprijs"], "marge": b["marge"],
                "marge_pct": b["marge_pct"], "kleur": kleur(b["marge_pct"]),
                "week_marge": b["week_marge"],
                "verschil_kostprijs": round(b["kostprijs"] - nu["kostprijs"], 4),
                "verschil_marge_pnt": round(b["marge_pct"] - nu["marge_pct"], 1),
                "nodige_verkoopprijs": round(nodig, 2) if nodig else None,
            }

        nu["vervanging"] = blok(vervanging)
        nu["scenario"] = blok(scenario)
        producten.append(nu)
    producten.sort(key=lambda p: p["marge_pct"])

    voorraad_regels = voorraadbeeld(db)
    week_nu = sum(p["week_marge"] for p in producten)
    week_scenario = sum(p["scenario"]["week_marge"] for p in producten)
    week_vervanging = sum(p["vervanging"]["week_marge"] for p in producten)

    return {
        "producten": producten,
        "voorraad": voorraad_regels,
        "noteringen": db["noteringen"],
        "vaste_kosten": db["vaste_kosten"],
        "schuiven": schuiven,
        "presets": scenario_presets(db),
        "groepen": sorted({g["groep"] for g in db["grondstoffen"].values()}) + ["Loon en energie"],
        "totalen": {
            "week_omzet": round(sum(p["week_omzet"] for p in producten), 2),
            "week_marge_nu": round(week_nu, 2),
            "week_marge_vervanging": round(week_vervanging, 2),
            "week_marge_scenario": round(week_scenario, 2),
            "week_verschil": round(week_scenario - week_nu, 2),
            "jaar_verschil": round((week_scenario - week_nu) * 52, 2),
            "voorraadwaarde": round(sum(v["voorraadwaarde"] for v in voorraad_regels), 2),
            "producten_rood_nu": sum(1 for p in producten if p["kleur"] == "verlies"),
            "producten_rood_scenario": sum(1 for p in producten if p["scenario"]["kleur"] == "verlies"),
        },
        "bijgewerkt": datetime.datetime.now().isoformat(timespec="seconds"),
    }


# ---------------------------------------------------------------------------
# Uitwisseling met Excel
#
# Nederlandse Excel gebruikt een puntkomma als scheidingsteken en een komma als
# decimaalteken. Daar schrijven we naartoe, en bij het inlezen accepteren we
# allebei de smaken, want een bakker weet niet welke hij heeft.
# ---------------------------------------------------------------------------
SJABLONEN = {
    "inkoopprijzen": {
        "titel": "Inkoopprijzen van je leverancier",
        "kolommen": ["grondstof", "naam", "groep", "eenheid", "prijs_per_100", "leverancier"],
        "uitleg": "De prijs per 100 kg of 100 liter, zoals hij op de factuur staat.",
    },
    "recepten": {
        "titel": "Recepten, verkoopprijzen en weekaantallen",
        "kolommen": ["recept", "naam", "groep", "meelbasis_kg", "deeggewicht_g",
                     "bakverlies_pct", "arbeid_min", "oven_min", "verkoop_incl", "per_week"],
        "uitleg": "Een regel per product. De verkoopprijs is inclusief btw.",
    },
    "receptregels": {
        "titel": "Samenstelling van je recepten",
        "kolommen": ["recept", "grondstof", "soort", "waarde"],
        "uitleg": ("Soort is deeg, garnering of verpakking. Bij deeg is de waarde het "
                   "bakkerspercentage ten opzichte van je meel, bij garnering en verpakking "
                   "is het de hoeveelheid per stuk."),
    },
    "leveringen": {
        "titel": "Je voorraadpartijen",
        "kolommen": ["grondstof", "datum", "aantal", "restant", "prijs_per_100", "partij"],
        "uitleg": "Een regel per levering. Hierop draait de berekening oudste partij eerst.",
    },
}


def _nl(waarde):
    if isinstance(waarde, float):
        return ("%.4f" % waarde).rstrip("0").rstrip(".").replace(".", ",")
    return "" if waarde is None else str(waarde)


def _getal(tekst, veld, regelnr):
    tekst = (tekst or "").strip().replace("\u00a0", "")
    if not tekst:
        raise ValueError("regel %d: %s is leeg" % (regelnr, veld))
    tekst = tekst.replace("€", "").strip()
    if "," in tekst and "." in tekst:
        tekst = tekst.replace(".", "").replace(",", ".")
    elif "," in tekst:
        tekst = tekst.replace(",", ".")
    try:
        return float(tekst)
    except ValueError:
        raise ValueError("regel %d: %s is geen getal (%r)" % (regelnr, veld, tekst))


def sjabloon_csv(soort, db=None):
    """Bouwt het sjabloon, alvast gevuld met wat er nu in het systeem staat."""
    import io, csv
    db = db or laad()
    vorm = SJABLONEN[soort]
    buffer = io.StringIO()
    schrijver = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    schrijver.writerow(vorm["kolommen"])

    if soort == "inkoopprijzen":
        for g in sorted(db["grondstoffen"].values(), key=lambda x: (x["groep"], x["naam"])):
            schrijver.writerow([g["id"], g["naam"], g["groep"], g["eenheid"],
                                _nl(g["laatste_prijs_per_100"]), g.get("leverancier", "")])
    elif soort == "recepten":
        for r in db["recepten"]:
            schrijver.writerow([r["id"], r["naam"], r["groep"], _nl(r["meelbasis_kg"]),
                                _nl(r["deeggewicht_g"]), _nl(r["bakverlies_pct"]),
                                _nl(r["arbeid_min"]), _nl(r["oven_min"]),
                                _nl(r["verkoop_incl"]), _nl(r["per_week"])])
    elif soort == "receptregels":
        for r in db["recepten"]:
            for gid, pct in r["percentages"].items():
                schrijver.writerow([r["id"], gid, "deeg", _nl(pct)])
            for gid, hoeveelheid in r.get("garnering", {}).items():
                schrijver.writerow([r["id"], gid, "garnering", _nl(hoeveelheid)])
            for gid, aantal in r.get("verpakking", {}).items():
                schrijver.writerow([r["id"], gid, "verpakking", _nl(aantal)])
    elif soort == "leveringen":
        for l in sorted(db["leveringen"], key=lambda x: (x["grondstof"], x["datum"])):
            schrijver.writerow([l["grondstof"], l["datum"], _nl(l["aantal"]),
                                _nl(l["restant"]), _nl(l["prijs_per_100"]), l.get("batch", "")])
    return buffer.getvalue()


def lees_csv(tekst):
    """Leest een csv die uit Excel komt, met puntkomma of komma als scheidingsteken."""
    import io, csv
    tekst = tekst.lstrip("\ufeff")
    eerste = tekst.splitlines()[0] if tekst.strip() else ""
    scheiding = ";" if eerste.count(";") >= eerste.count(",") else ","
    lezer = csv.DictReader(io.StringIO(tekst), delimiter=scheiding)
    kolommen = [k.strip().lower() for k in (lezer.fieldnames or [])]
    rijen = []
    for rij in lezer:
        rijen.append({(k or "").strip().lower(): (v or "").strip() for k, v in rij.items()})
    return kolommen, rijen


def main():
    db = laad()
    presets = scenario_presets(db)
    o = overzicht(db, presets)
    print("Marktbeweging afgelopen jaar, doorgerekend per groep:")
    for groep, pct in sorted(presets.items(), key=lambda kv: -abs(kv[1])):
        print("  %-18s %+6.1f%%" % (groep, pct))
    print()
    t = o["totalen"]
    print("Weekomzet          € %10.2f" % t["week_omzet"])
    print("Marge per week     € %10.2f  (FIFO, uit je eigen voorraad)" % t["week_marge_nu"])
    print("Marge per week     € %10.2f  (als je vandaag moet bijkopen)" % t["week_marge_vervanging"])
    print("Marge per week     € %10.2f  (scenario: markt jaar op jaar)" % t["week_marge_scenario"])
    print("Verschil per jaar  € %10.2f" % t["jaar_verschil"])
    print("Voorraadwaarde     € %10.2f" % t["voorraadwaarde"])
    print()
    print("%-34s %8s %8s %7s  %8s %7s  %s" %
          ("Product", "kostpr.", "verkoop", "marge", "straks", "marge", "per week"))
    for p in o["producten"]:
        print("%-34s %8.2f %8.2f %6.1f%%  %8.2f %6.1f%%  %8.0f  %s" % (
            p["naam"][:34], p["kostprijs"], p["verkoop_excl"], p["marge_pct"],
            p["scenario"]["kostprijs"], p["scenario"]["marge_pct"],
            p["week_marge"], p["kleur"]))
    print()
    print("Grootste gaten tussen voorraadprijs en vandaag bijkopen:")
    for v in o["voorraad"][:8]:
        if v["verschil_pct"] is None:
            continue
        print("  %-28s FIFO %8.2f   vandaag %8.2f   %+5.1f%%   dekking %s weken" % (
            v["naam"][:28], v["fifo_per_100"], v["vervanging_per_100"],
            v["verschil_pct"], v["weken_dekking"]))


if __name__ == "__main__":
    main()
