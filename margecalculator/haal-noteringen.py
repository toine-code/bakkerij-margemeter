#!/usr/bin/env python3
"""
Haalt de actuele EU-marktnoteringen op en schrijft ze in index.html.

Twee bronnen, allebei openbaar en zonder sleutel:
  - boter, Nederlandse weeknotering, euro per 100 kg
  - baktarwe, Duitse weeknotering, euro per ton (voor Nederland publiceert de EU
    alleen voertarwe, Duitse baktarwe is de dichtstbijzijnde bruikbare notering)

Waarom in het bestand schrijven en niet live ophalen vanuit de pagina?
Een pagina die je opent met dubbelklik mag van je browser geen gegevens van
buiten ophalen. Door de cijfers hier in het bestand te zetten werkt de meter
ook zonder internet, bijvoorbeeld in een zaal met slechte wifi.

Gebruik:  python3 haal-noteringen.py
"""

import datetime
import json
import pathlib
import re
import urllib.request

API = "https://ec.europa.eu/agrifood/api"
HIER = pathlib.Path(__file__).parent


def haal(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def bedrag(tekst):
    """'€682,00' en '€682.00' worden allebei 682.0"""
    t = tekst.replace("€", "").strip()
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    return float(t)


def datum(tekst):
    return datetime.datetime.strptime(tekst, "%d/%m/%Y").date()


def boter():
    """Weeknotering boter Nederland, met dezelfde week vorig jaar ernaast."""
    nu = datetime.date.today().year
    rijen = haal(f"{API}/dairy/prices?products=butter&memberStateCodes=NL&years={nu - 1},{nu}")
    punten = sorted((datum(r["endDate"]), bedrag(r["price"])) for r in rijen)
    if not punten:
        return None
    laatst_datum, laatst_prijs = punten[-1]
    doel = laatst_datum - datetime.timedelta(days=364)
    vorig = min(punten, key=lambda p: abs((p[0] - doel).days))
    return {
        "naam": "Boter, Nederlandse notering",
        "eenheid": "per 100 kg",
        "prijs": laatst_prijs,
        "datum": laatst_datum.isoformat(),
        "vorig_jaar": vorig[1],
        "verandering": round((laatst_prijs / vorig[1] - 1) * 100, 1),
        "bron": "Europese Commissie, zuivelmarktnoteringen",
    }


def baktarwe():
    """Weeknotering baktarwe Duitsland, met dezelfde week vorig jaar ernaast."""
    rijen = haal(f"{API}/cereal/prices?memberStateCodes=DE")
    punten = sorted(
        (datum(r["endDate"]), bedrag(r["price"]))
        for r in rijen
        if r.get("productName") == "Breadmaking common wheat"
    )
    if not punten:
        return None
    laatst_datum, laatst_prijs = punten[-1]
    doel = laatst_datum - datetime.timedelta(days=364)
    vorig = min(punten, key=lambda p: abs((p[0] - doel).days))
    return {
        "naam": "Baktarwe, Duitse notering",
        "eenheid": "per ton",
        "prijs": laatst_prijs,
        "datum": laatst_datum.isoformat(),
        "vorig_jaar": vorig[1],
        "verandering": round((laatst_prijs / vorig[1] - 1) * 100, 1),
        "bron": "Europese Commissie, graanmarktnoteringen",
    }


def main():
    data = {
        "opgehaald": datetime.date.today().isoformat(),
        "zuivel": boter(),
        "bloem": baktarwe(),
    }
    if not data["zuivel"] or not data["bloem"]:
        raise SystemExit("Een van de twee noteringen kwam niet binnen, niets gewijzigd.")

    for sleutel in ("zuivel", "bloem"):
        n = data[sleutel]
        print(f"{n['naam']}: € {n['prijs']:.2f} {n['eenheid']} "
              f"({n['datum']}), een jaar eerder € {n['vorig_jaar']:.2f}, "
              f"dat is {n['verandering']:+.1f}%")

    pad = HIER / "index.html"
    html = pad.read_text()
    blok = "/*NOTERINGEN_START*/\nconst NOTERINGEN = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n/*NOTERINGEN_END*/"
    nieuw, n = re.subn(
        r"/\*NOTERINGEN_START\*/.*?/\*NOTERINGEN_END\*/",
        lambda _: blok,
        html,
        flags=re.S,
    )
    if not n:
        raise SystemExit("Kon het blok NOTERINGEN niet vinden in index.html.")
    pad.write_text(nieuw)
    print(f"\nGeschreven in {pad.name}. Ververs de pagina in je browser.")


if __name__ == "__main__":
    main()
