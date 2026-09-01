#!/usr/bin/env python3
"""
Start het bakkerijsysteem op je eigen computer.

    python3 start.py

Daarna opent je browser op http://localhost:8777. Alles draait lokaal: je
recepten, je inkoopprijzen en je voorraad blijven op deze computer staan. Het
enige verkeer naar buiten is het ophalen van de marktnoteringen bij de open data
van de Europese Commissie, en dat gebeurt alleen als je op de knop drukt.

Waarom een servertje en niet gewoon een bestand? Een pagina die je met
dubbelklikken opent mag van je browser geen gegevens van buiten halen. Draait
dezelfde pagina op localhost, dan mag het wel, en kan het systeem de noteringen
zelf ophalen.
"""

import http.server
import json
import re
import pathlib
import socketserver
import threading
import urllib.parse
import webbrowser

import kostprijs
import markt

HIER = pathlib.Path(__file__).parent
WEB = HIER / "web"
DATA = HIER / "data"
POORT = 8777


def schrijf(naam, inhoud):
    (DATA / naam).write_text(json.dumps(inhoud, ensure_ascii=False, indent=2))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB), **kw)

    def log_message(self, opmaak, *args):
        if "/api/" in (args[0] if args else ""):
            print("  %s" % (opmaak % args))

    # -- hulpjes ------------------------------------------------------------
    def stuur_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def lees_json(self):
        lengte = int(self.headers.get("Content-Length") or 0)
        if not lengte:
            return {}
        return json.loads(self.rfile.read(lengte).decode("utf-8"))

    # -- routes -------------------------------------------------------------
    def do_GET(self):
        pad = urllib.parse.urlparse(self.path)
        if not pad.path.startswith("/api/"):
            return super().do_GET()

        vraag = urllib.parse.parse_qs(pad.query)
        try:
            if pad.path == "/api/overzicht":
                schuiven = json.loads(vraag.get("schuiven", ["{}"])[0])
                return self.stuur_json(kostprijs.overzicht(schuiven=schuiven))

            if pad.path.startswith("/api/recept/"):
                rid = pad.path.rsplit("/", 1)[-1]
                db = kostprijs.laad()
                for recept in db["recepten"]:
                    if recept["id"] == rid:
                        detail = kostprijs.bereken_recept(db, recept, "fifo")
                        detail["bron"] = recept
                        return self.stuur_json(detail)
                return self.stuur_json({"fout": "recept niet gevonden"}, 404)

            if pad.path == "/api/voorraad":
                return self.stuur_json({"voorraad": kostprijs.voorraadbeeld(kostprijs.laad())})

            if pad.path == "/api/noteringen":
                db = kostprijs.laad()
                return self.stuur_json(db["noteringen"])

            if pad.path == "/api/aangeleverd":
                map_ = DATA / "aangeleverd"
                bestanden = []
                if map_.exists():
                    for f in sorted(map_.iterdir()):
                        if f.is_file() and not f.name.startswith("."):
                            bestanden.append({"naam": f.name, "bytes": f.stat().st_size})
                return self.stuur_json({"bestanden": bestanden,
                                        "map": str(map_.relative_to(HIER.parent))})

            if pad.path == "/api/sjablonen":
                return self.stuur_json({"sjablonen": [
                    dict(soort=soort, **{k: v for k, v in vorm.items() if k != "kolommen"},
                         kolommen=vorm["kolommen"])
                    for soort, vorm in kostprijs.SJABLONEN.items()]})

            if pad.path.startswith("/api/sjabloon/"):
                soort = pad.path.rsplit("/", 1)[-1]
                if soort not in kostprijs.SJABLONEN:
                    return self.stuur_json({"fout": "onbekend sjabloon"}, 404)
                body = kostprijs.sjabloon_csv(soort).encode("utf-8-sig")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition",
                                 'attachment; filename="%s.csv"' % soort)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return self.wfile.write(body)

        except Exception as fout:            # noqa: BLE001, een fout mag de server niet slopen
            return self.stuur_json({"fout": str(fout)}, 500)

        return self.stuur_json({"fout": "onbekend adres"}, 404)

    def do_POST(self):
        pad = urllib.parse.urlparse(self.path).path
        try:
            if pad == "/api/noteringen/ververs":
                data = markt.ophalen()
                if not data["noteringen"]:
                    return self.stuur_json({"fout": "geen enkele notering binnengekomen"}, 502)
                schrijf("noteringen.json", data)
                return self.stuur_json({"ok": True, "aantal": len(data["noteringen"]),
                                        "noteringen": data["noteringen"]})

            if pad == "/api/inkoop":
                body = self.lees_json()
                bestand = json.loads((DATA / "inkoop.json").read_text())
                nieuw = {
                    "id": "L%03d" % (len(bestand["leveringen"]) + 1),
                    "grondstof": body["grondstof"],
                    "datum": body["datum"],
                    "aantal": float(body["aantal"]),
                    "restant": float(body["aantal"]),
                    "prijs_per_100": float(body["prijs_per_100"]),
                    "batch": body.get("batch", ""),
                }
                bestand["leveringen"].append(nieuw)
                schrijf("inkoop.json", bestand)

                # de laatst bekende inkoopprijs meeschuiven
                grond = json.loads((DATA / "grondstoffen.json").read_text())
                for g in grond["grondstoffen"]:
                    if g["id"] == nieuw["grondstof"]:
                        g["laatste_prijs_per_100"] = nieuw["prijs_per_100"]
                schrijf("grondstoffen.json", grond)
                return self.stuur_json({"ok": True, "levering": nieuw})

            if pad == "/api/aangeleverd":
                body = self.lees_json()
                return self.stuur_json(bewaar_aangeleverd(body.get("naam", ""),
                                                          body.get("inhoud", "")))

            if pad == "/api/aangeleverd/wissen":
                map_ = DATA / "aangeleverd"
                weg = 0
                if map_.exists():
                    for f in list(map_.iterdir()):
                        if f.is_file() and not f.name.startswith("."):
                            f.unlink()
                            weg += 1
                return self.stuur_json({"ok": True, "verwijderd": weg})

            if pad.startswith("/api/import/"):
                soort = pad.rsplit("/", 1)[-1]
                body = self.lees_json()
                return self.stuur_json(importeer(soort, body.get("csv", "")))

            if pad == "/api/productie":
                body = self.lees_json()
                return self.stuur_json(boek_productie(body["recept"], float(body.get("batches", 1))))

        except Exception as fout:            # noqa: BLE001
            return self.stuur_json({"fout": str(fout)}, 500)

        return self.stuur_json({"fout": "onbekend adres"}, 404)


MAX_BESTAND = 25 * 1024 * 1024      # 25 MB, ruim genoeg voor een factuur of een spreadsheet


def bewaar_aangeleverd(naam, inhoud_base64):
    """
    Zet een bestand dat de bakker aanlevert in data/aangeleverd/.

    We lezen het niet uit en we snappen het niet. Dat is precies de bedoeling:
    Claude Code kijkt er straks naar. Wij zorgen alleen dat het bestand veilig
    op de juiste plek terechtkomt.
    """
    import base64
    schoon = pathlib.Path(naam or "").name          # geen paden, alleen de bestandsnaam
    schoon = re.sub(r"[^A-Za-z0-9._ ()-]", "_", schoon).strip() or "bestand"
    if schoon.startswith("."):
        schoon = "bestand" + schoon

    kop, _, data = inhoud_base64.partition(",")     # data:...;base64,AAAA
    ruw = data if data else kop
    try:
        bytes_ = base64.b64decode(ruw, validate=False)
    except Exception:
        return {"fout": "kon het bestand niet lezen"}
    if not bytes_:
        return {"fout": "het bestand is leeg"}
    if len(bytes_) > MAX_BESTAND:
        return {"fout": "dit bestand is groter dan 25 MB, dat is te groot"}

    map_ = DATA / "aangeleverd"
    map_.mkdir(exist_ok=True)
    doel = map_ / schoon
    teller = 2
    while doel.exists():                            # nooit stilletjes iets overschrijven
        doel = map_ / ("%s-%d%s" % (pathlib.Path(schoon).stem, teller, pathlib.Path(schoon).suffix))
        teller += 1
    doel.write_bytes(bytes_)
    return {"ok": True, "naam": doel.name, "bytes": len(bytes_)}


def bewaar_kopie(naam):
    """Zet een kopie weg voordat we iets overschrijven, met de datum erin."""
    import datetime
    bron = DATA / naam
    if not bron.exists():
        return None
    map_ = DATA / "kopieen"
    map_.mkdir(exist_ok=True)
    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    doel = map_ / ("%s-%s" % (stempel, naam))
    doel.write_text(bron.read_text())
    return doel.name


def importeer(soort, csv_tekst):
    """
    Leest een ingevuld sjabloon in en werkt de gegevens bij.

    Niets gaat stilletjes: elke regel die niet klopt komt terug in het verslag,
    met de reden erbij. En er gaat altijd eerst een kopie van het oude bestand
    naar data/kopieen/.
    """
    if soort not in kostprijs.SJABLONEN:
        return {"fout": "onbekend sjabloon"}
    if not csv_tekst.strip():
        return {"fout": "het bestand is leeg"}

    kolommen, rijen = kostprijs.lees_csv(csv_tekst)
    nodig = kostprijs.SJABLONEN[soort]["kolommen"]
    mist = [k for k in nodig if k not in kolommen]
    if mist:
        return {"fout": "deze kolommen missen: %s. Download het sjabloon opnieuw."
                        % ", ".join(mist)}

    db = kostprijs.laad()
    bekend = set(db["grondstoffen"])
    verslag = {"soort": soort, "gelezen": len(rijen), "verwerkt": 0,
               "nieuw": 0, "overgeslagen": [], "kopie": None}

    def fout(nr, reden):
        verslag["overgeslagen"].append({"regel": nr, "reden": reden})

    getal = kostprijs._getal

    if soort == "inkoopprijzen":
        verslag["kopie"] = bewaar_kopie("grondstoffen.json")
        bestand = json.loads((DATA / "grondstoffen.json").read_text())
        op_id = {g["id"]: g for g in bestand["grondstoffen"]}
        for nr, rij in enumerate(rijen, start=2):
            gid = rij.get("grondstof", "").strip()
            if not gid:
                fout(nr, "geen grondstof ingevuld")
                continue
            try:
                prijs = getal(rij.get("prijs_per_100"), "prijs_per_100", nr)
            except ValueError as e:
                fout(nr, str(e))
                continue
            if prijs < 0:
                fout(nr, "regel %d: een negatieve prijs kan niet" % nr)
                continue
            if gid in op_id:
                g = op_id[gid]
            else:
                g = {"id": gid, "naam": rij.get("naam") or gid,
                     "groep": rij.get("groep") or "Overig",
                     "eenheid": rij.get("eenheid") or "kg",
                     "handelseenheid": "100 " + (rij.get("eenheid") or "kg"),
                     "notering": None, "doorwerking": 0.0}
                bestand["grondstoffen"].append(g)
                op_id[gid] = g
                verslag["nieuw"] += 1
            g["laatste_prijs_per_100"] = prijs
            for veld in ("naam", "groep", "eenheid", "leverancier"):
                if rij.get(veld):
                    g[veld] = rij[veld]
            verslag["verwerkt"] += 1
        schrijf("grondstoffen.json", bestand)

    elif soort == "recepten":
        verslag["kopie"] = bewaar_kopie("recepten.json")
        bestand = json.loads((DATA / "recepten.json").read_text())
        op_id = {r["id"]: r for r in bestand["recepten"]}
        velden = [("meelbasis_kg", "meelbasis_kg"), ("deeggewicht_g", "deeggewicht_g"),
                  ("bakverlies_pct", "bakverlies_pct"), ("arbeid_min", "arbeid_min"),
                  ("oven_min", "oven_min"), ("verkoop_incl", "verkoop_incl"),
                  ("per_week", "per_week")]
        for nr, rij in enumerate(rijen, start=2):
            rid = rij.get("recept", "").strip()
            if not rid:
                fout(nr, "geen recept ingevuld")
                continue
            try:
                waarden = {sleutel: getal(rij.get(kolom), kolom, nr) for kolom, sleutel in velden}
            except ValueError as e:
                fout(nr, str(e))
                continue
            if rid in op_id:
                r = op_id[rid]
            else:
                r = {"id": rid, "percentages": {}, "garnering": {}, "verpakking": {}}
                bestand["recepten"].append(r)
                op_id[rid] = r
                verslag["nieuw"] += 1
            r["naam"] = rij.get("naam") or r.get("naam", rid)
            r["groep"] = rij.get("groep") or r.get("groep", "Overig")
            r.update(waarden)
            verslag["verwerkt"] += 1
        schrijf("recepten.json", bestand)

    elif soort == "receptregels":
        verslag["kopie"] = bewaar_kopie("recepten.json")
        bestand = json.loads((DATA / "recepten.json").read_text())
        op_id = {r["id"]: r for r in bestand["recepten"]}
        geraakt = set()
        onbekend = set()
        for nr, rij in enumerate(rijen, start=2):
            rid, gid = rij.get("recept", "").strip(), rij.get("grondstof", "").strip()
            soort_regel = (rij.get("soort") or "deeg").strip().lower()
            if rid not in op_id:
                fout(nr, "recept %s bestaat niet, zet hem eerst in het receptensjabloon" % rid)
                continue
            if gid not in bekend:
                onbekend.add(gid)
            try:
                waarde = getal(rij.get("waarde"), "waarde", nr)
            except ValueError as e:
                fout(nr, str(e))
                continue
            r = op_id[rid]
            if rid not in geraakt:
                r["percentages"], r["garnering"], r["verpakking"] = {}, {}, {}
                geraakt.add(rid)
            doel = {"deeg": "percentages", "garnering": "garnering",
                    "verpakking": "verpakking"}.get(soort_regel)
            if not doel:
                fout(nr, "soort moet deeg, garnering of verpakking zijn, niet %r" % soort_regel)
                continue
            r[doel][gid] = waarde
            verslag["verwerkt"] += 1
        if onbekend:
            verslag["waarschuwing"] = ("Deze grondstoffen kent het systeem nog niet: %s. "
                                       "Zet ze eerst in het sjabloon met inkoopprijzen."
                                       % ", ".join(sorted(onbekend)))
        schrijf("recepten.json", bestand)

    elif soort == "leveringen":
        verslag["kopie"] = bewaar_kopie("inkoop.json")
        nieuw = []
        onbekend = set()
        for nr, rij in enumerate(rijen, start=2):
            gid = rij.get("grondstof", "").strip()
            if not gid:
                fout(nr, "geen grondstof ingevuld")
                continue
            if gid not in bekend:
                onbekend.add(gid)
            datum = (rij.get("datum") or "").strip()
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", datum):
                fout(nr, "datum moet als 2026-08-31 geschreven worden, niet %r" % datum)
                continue
            try:
                aantal = getal(rij.get("aantal"), "aantal", nr)
                prijs = getal(rij.get("prijs_per_100"), "prijs_per_100", nr)
                restant = getal(rij.get("restant"), "restant", nr) if rij.get("restant") else aantal
            except ValueError as e:
                fout(nr, str(e))
                continue
            nieuw.append({"id": "L%03d" % (len(nieuw) + 1), "grondstof": gid,
                          "datum": datum, "aantal": aantal, "restant": restant,
                          "prijs_per_100": prijs, "batch": rij.get("partij", "")})
            verslag["verwerkt"] += 1
        if not nieuw:
            return {"fout": "geen enkele bruikbare regel gevonden, er is niets gewijzigd",
                    "overgeslagen": verslag["overgeslagen"]}
        if onbekend:
            verslag["waarschuwing"] = ("Deze grondstoffen kent het systeem nog niet: %s. "
                                       "Zet ze eerst in het sjabloon met inkoopprijzen."
                                       % ", ".join(sorted(onbekend)))
        schrijf("inkoop.json", {"leveringen": nieuw})

    return verslag


def boek_productie(recept_id, batches):
    """
    Boekt een productieronde af: haalt de grondstoffen uit de voorraad, oudste
    partij eerst, en schrijft de nieuwe restanten weg. Zo loopt de FIFO echt door.
    """
    db = kostprijs.laad()
    recept = next((r for r in db["recepten"] if r["id"] == recept_id), None)
    if not recept:
        return {"fout": "recept niet gevonden"}

    berekend = kostprijs.bereken_recept(db, recept, "fifo")
    nodig = {}
    for gid, percentage in recept["percentages"].items():
        nodig[gid] = nodig.get(gid, 0.0) + batches * recept["meelbasis_kg"] * percentage / 100.0
    for gid, per_stuk in recept.get("garnering", {}).items():
        nodig[gid] = nodig.get(gid, 0.0) + per_stuk * berekend["stuks_per_batch"] * batches
    for gid, per_stuk in recept.get("verpakking", {}).items():
        nodig[gid] = nodig.get(gid, 0.0) + per_stuk * berekend["stuks_per_batch"] * batches

    bestand = json.loads((DATA / "inkoop.json").read_text())
    per_grondstof = {}
    for laag in bestand["leveringen"]:
        per_grondstof.setdefault(laag["grondstof"], []).append(laag)

    kosten = 0.0
    tekorten = []
    for gid, hoeveelheid in nodig.items():
        rest = hoeveelheid
        for laag in sorted(per_grondstof.get(gid, []), key=lambda l: l["datum"]):
            if rest <= 1e-9:
                break
            pak = min(rest, laag["restant"])
            laag["restant"] = round(laag["restant"] - pak, 6)
            kosten += pak * laag["prijs_per_100"] / 100.0
            rest -= pak
        if rest > 1e-9:
            tekorten.append({"grondstof": gid, "tekort": round(rest, 2)})

    schrijf("inkoop.json", bestand)
    return {
        "ok": True, "recept": recept["naam"],
        "batches": batches,
        "stuks": int(berekend["stuks_per_batch"] * batches),
        "grondstofkosten": round(kosten, 2),
        "tekorten": tekorten,
    }


def main():
    if not (DATA / "grondstoffen.json").exists():
        raise SystemExit("Geen data gevonden. Draai eerst: python3 seed.py")

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    try:
        server = socketserver.ThreadingTCPServer(("127.0.0.1", POORT), Handler)
    except OSError:
        raise SystemExit(
            "Poort %d is al bezet. Draait het systeem al in een ander venster?\n"
            "Kijk in je browser op http://localhost:%d, of sluit dat andere venster af."
            % (POORT, POORT))

    with server:
        adres = "http://localhost:%d" % POORT
        print("Bakkerijsysteem draait op %s" % adres)
        print("Alles blijft op deze computer. Stoppen kan met ctrl-c.\n")
        threading.Timer(0.8, lambda: webbrowser.open(adres)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nGestopt.")


if __name__ == "__main__":
    main()
