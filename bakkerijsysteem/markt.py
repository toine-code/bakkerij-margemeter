#!/usr/bin/env python3
"""
Haalt de marktnoteringen op bij de open data van de Europese Commissie.

Alles gratis, geen sleutel, geen abonnement. De reeksen worden opgeslagen in
data/noteringen.json, inclusief de historie, zodat het systeem kan uitrekenen
hoeveel de markt bewoog sinds de dag dat jij je laatste zak bloem kocht.

    python3 markt.py

Wat er niet is: een Europese notering voor eieren, zaden, noten, spijs of
chocolade. Die grondstoffen staan in het systeem zonder marktkoppeling, je vult
ze bij met je eigen inkoopfactuur.
"""

import datetime
import json
import pathlib
import urllib.error
import urllib.request

API = "https://ec.europa.eu/agrifood/api"
DATA = pathlib.Path(__file__).parent / "data"

# id, omschrijving, endpoint, filter, eenheid, bron
NOTERINGEN = [
    ("tarwe-bak", "Baktarwe", "cereal",
     {"land": "DE", "product": "Breadmaking common wheat"}, "ton",
     "Europese Commissie, graanmarkt Duitsland"),
    ("rogge-bak", "Rogge van bakkwaliteit", "cereal",
     {"land": "DE", "product": "Rye of breadmaking quality"}, "ton",
     "Europese Commissie, graanmarkt Duitsland"),
    ("durum", "Durumtarwe", "cereal",
     {"land": "FR", "product": "Durum wheat"}, "ton",
     "Europese Commissie, graanmarkt Frankrijk"),
    ("zemelen", "Tarwezemelen", "cereal",
     {"land": "DE", "product": "Wheat bran"}, "ton",
     "Europese Commissie, graanmarkt Duitsland"),
    ("boter", "Boter", "dairy",
     {"land": "NL", "product": "BUTTER"}, "100 kg",
     "Europese Commissie, zuivelmarkt Nederland"),
    ("magere-melkpoeder", "Magere melkpoeder", "dairy",
     {"land": "NL", "product": "SMP"}, "100 kg",
     "Europese Commissie, zuivelmarkt Nederland"),
    ("volle-melkpoeder", "Volle melkpoeder", "dairy",
     {"land": "NL", "product": "WMP"}, "100 kg",
     "Europese Commissie, zuivelmarkt Nederland"),
    ("suiker", "Witte suiker", "sugar",
     {"regio": "EU Average"}, "ton",
     "Europese Commissie, suikermarkt EU-gemiddelde"),
    ("zonnebloemolie", "Ruwe zonnebloemolie", "oilseeds",
     {"land": "RO", "product": "Crude sunflower oil"}, "ton",
     "Europese Commissie, oliezaden Roemenie"),
]


def _haal(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def _bedrag(tekst):
    """De endpoints wisselen tussen '400.00', '€248,50' en '501.4009'."""
    t = str(tekst).replace("€", "").strip()
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    return float(t)


def _datum(tekst):
    return datetime.datetime.strptime(tekst, "%d/%m/%Y").date()


def _reeks_granen(f):
    rijen = _haal("%s/cereal/prices?memberStateCodes=%s" % (API, f["land"]))
    return sorted(
        (_datum(r["endDate"]).isoformat(), _bedrag(r["price"]))
        for r in rijen if r.get("productName") == f["product"]
    )


def _reeks_zuivel(f):
    nu = datetime.date.today().year
    jaren = ",".join(str(j) for j in range(nu - 3, nu + 1))
    rijen = _haal("%s/dairy/prices?products=%s&memberStateCodes=%s&years=%s"
                  % (API, f["product"].lower(), f["land"], jaren))
    return sorted(
        (_datum(r["endDate"]).isoformat(), _bedrag(r["price"]))
        for r in rijen if r.get("product", "").upper() == f["product"]
    )


def _reeks_oliezaden(f):
    rijen = _haal("%s/oilseeds/prices?memberStateCodes=%s" % (API, f["land"]))
    return sorted(
        (_datum(r["endDate"]).isoformat(), _bedrag(r["price"]))
        for r in rijen if r.get("product") == f["product"]
    )


def _reeks_suiker(f):
    rijen = _haal("%s/sugar/prices" % API)
    punten = []
    for r in rijen:
        if r.get("sugarRegion") != f["regio"]:
            continue
        if r.get("contractType") != "Monthly data":
            continue
        jaar, maand = r["ym"].split("/")
        # de maandnotering zetten we op de laatste dag van die maand
        eerste_volgende = datetime.date(int(jaar) + (1 if maand == "12" else 0),
                                        1 if maand == "12" else int(maand) + 1, 1)
        punten.append(((eerste_volgende - datetime.timedelta(days=1)).isoformat(),
                       _bedrag(r["price"])))
    return sorted(punten)


OPHALERS = {
    "cereal": _reeks_granen,
    "dairy": _reeks_zuivel,
    "oilseeds": _reeks_oliezaden,
    "sugar": _reeks_suiker,
}


def waarde_op(reeks, datum):
    """De laatst bekende notering op of voor die datum."""
    gekozen = None
    for d, waarde in reeks:
        if d <= datum:
            gekozen = waarde
        else:
            break
    return gekozen if gekozen is not None else (reeks[0][1] if reeks else None)


def ophalen():
    resultaat = {"opgehaald": datetime.datetime.now().isoformat(timespec="seconds"),
                 "noteringen": {}}
    for nid, naam, endpoint, f, eenheid, bron in NOTERINGEN:
        try:
            reeks = OPHALERS[endpoint](f)
        except (urllib.error.URLError, ValueError, KeyError) as fout:
            print("  %-20s MISLUKT (%s)" % (nid, fout))
            continue
        if not reeks:
            print("  %-20s geen rijen gevonden" % nid)
            continue
        laatste_datum, laatste = reeks[-1]
        jaar_terug = (datetime.date.fromisoformat(laatste_datum)
                      - datetime.timedelta(days=364)).isoformat()
        vorig = waarde_op(reeks, jaar_terug)
        resultaat["noteringen"][nid] = {
            "id": nid, "naam": naam, "eenheid": eenheid, "bron": bron,
            "waarde": laatste, "datum": laatste_datum,
            "vorig_jaar": vorig,
            "verandering_jaar": round((laatste / vorig - 1) * 100, 1) if vorig else None,
            "reeks": reeks[-160:],
        }
        pijl = "%+.1f%%" % resultaat["noteringen"][nid]["verandering_jaar"]
        print("  %-20s %9.2f per %-7s %s   jaar op jaar %s"
              % (nid, laatste, eenheid, laatste_datum, pijl))
    return resultaat


def main():
    DATA.mkdir(exist_ok=True)
    print("Noteringen ophalen bij ec.europa.eu/agrifood ...")
    data = ophalen()
    if not data["noteringen"]:
        raise SystemExit("Niets opgehaald, bestaand bestand blijft staan.")
    (DATA / "noteringen.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print("\n%d noteringen opgeslagen in data/noteringen.json"
          % len(data["noteringen"]))


if __name__ == "__main__":
    main()
