#!/usr/bin/env python3
"""
Zet de voorbeelddata klaar: grondstoffen, recepten en inkooplagen.

Draai dit een keer om met schone voorbeeldcijfers te beginnen, of nadat je iets
grondig hebt verbouwd. Let op: dit overschrijft alles in data/.

    python3 seed.py
"""

import datetime
import json
import pathlib

DATA = pathlib.Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Grondstoffen
#
# prijs_per_100 is de laatst bekende inkoopprijs per handelseenheid (100 kg of
# 100 liter), zoals hij op de factuur van je leverancier staat.
#
# notering + doorwerking koppelen de grondstof aan een marktnotering. De
# doorwerking zegt hoeveel van een marktbeweging in jouw inkoopprijs terechtkomt.
# Bloem is geen tarwe: er zit maalloon, transport en marge van de molenaar
# tussen, en je hebt ongeveer 130 kg tarwe nodig voor 100 kg bloem. Vandaar 0,55.
# ---------------------------------------------------------------------------
GRONDSTOFFEN = [
    # id, naam, groep, eenheid, prijs per 100, leverancier, notering, doorwerking
    ("bloem-patent",     "Tarwebloem patent",          "Meel en bloem", "kg",  48.50, "Meneba",        "tarwe-bak", 0.55),
    ("bloem-brood",      "Broodbloem type 550",        "Meel en bloem", "kg",  46.80, "Meneba",        "tarwe-bak", 0.55),
    ("meel-volkoren",    "Tarwemeel volkoren",         "Meel en bloem", "kg",  45.20, "Meneba",        "tarwe-bak", 0.62),
    ("meel-spelt",       "Speltmeel",                  "Meel en bloem", "kg",  92.00, "Zeelandia",     "tarwe-bak", 0.35),
    ("meel-rogge",       "Roggemeel",                  "Meel en bloem", "kg",  54.00, "Meneba",        "rogge-bak", 0.58),
    ("gries-durum",      "Durumgries",                 "Meel en bloem", "kg",  86.00, "Meneba",        "durum",     0.55),
    ("zemelen",          "Tarwezemelen",               "Meel en bloem", "kg",  32.00, "Meneba",        "zemelen",   0.70),

    ("roomboter",        "Roomboter ongezouten",       "Zuivel en vet", "kg", 780.00, "Zijerveld",     "boter",     0.90),
    ("plaatboter",       "Croissantboter in plaat",    "Zuivel en vet", "kg", 845.00, "Zijerveld",     "boter",     0.85),
    ("margarine",        "Bakkersmargarine",           "Zuivel en vet", "kg", 225.00, "Zeelandia",     "zonnebloemolie", 0.45),
    ("melk-vol",         "Volle melk",                 "Zuivel en vet", "l",   95.00, "Zijerveld",     "volle-melkpoeder", 0.30),
    ("slagroom",         "Slagroom 35%",               "Zuivel en vet", "l",  420.00, "Zijerveld",     "boter",     0.55),
    ("karnemelk",        "Karnemelk",                  "Zuivel en vet", "l",   80.00, "Zijerveld",     "magere-melkpoeder", 0.25),
    ("ei-vloeibaar",     "Heel ei vloeibaar",          "Zuivel en vet", "kg", 330.00, "Interovo",      None,        0.0),

    ("maanzaad",         "Maanzaad blauw",             "Zaden en noten", "kg", 480.00, "Bakkersgrondstof", None,     0.0),
    ("zonnebloempit",    "Zonnebloempitten",           "Zaden en noten", "kg", 195.00, "Bakkersgrondstof", "zonnebloemolie", 0.35),
    ("sesamzaad",        "Sesamzaad",                  "Zaden en noten", "kg", 280.00, "Bakkersgrondstof", None,     0.0),
    ("lijnzaad",         "Lijnzaad bruin",             "Zaden en noten", "kg", 165.00, "Bakkersgrondstof", None,     0.0),
    ("pompoenpit",       "Pompoenpitten",              "Zaden en noten", "kg", 520.00, "Bakkersgrondstof", None,     0.0),
    ("amandelschaaf",    "Amandelschaafsel",           "Zaden en noten", "kg", 1180.00, "Bakkersgrondstof", None,    0.0),
    ("hazelnoot",        "Hazelnoten gebrand",         "Zaden en noten", "kg", 1450.00, "Bakkersgrondstof", None,    0.0),

    ("suiker",           "Kristalsuiker",              "Zoet en smaak", "kg", 135.00, "Zeelandia",     "suiker",    0.80),
    ("basterdsuiker",    "Witte basterdsuiker",        "Zoet en smaak", "kg", 155.00, "Zeelandia",     "suiker",    0.70),
    ("spijs",            "Amandelspijs",               "Zoet en smaak", "kg", 680.00, "Zeelandia",     None,        0.0),
    ("chocolade",        "Chocolade couverture puur",  "Zoet en smaak", "kg", 850.00, "Callebaut",     None,        0.0),
    ("rozijn",           "Rozijnen",                   "Zoet en smaak", "kg", 340.00, "Bakkersgrondstof", None,     0.0),
    ("kaneel",           "Kaneel gemalen",             "Zoet en smaak", "kg", 1100.00, "Zeelandia",    None,        0.0),
    ("appel",            "Appels schijf",              "Zoet en smaak", "kg", 165.00, "Hollander",     None,        0.0),

    ("gist",             "Verse gist",                 "Hulpstoffen",   "kg", 280.00, "Zeelandia",     None,        0.0),
    ("zout",             "Bakkerszout",                "Hulpstoffen",   "kg",  65.00, "Zeelandia",     None,        0.0),
    ("verbeteraar",      "Broodverbetermiddel",        "Hulpstoffen",   "kg", 390.00, "Zeelandia",     "tarwe-bak", 0.20),
    ("desem",            "Roggedesem vloeibaar",       "Hulpstoffen",   "kg", 210.00, "Zeelandia",     "rogge-bak", 0.30),
    ("water",            "Water",                      "Hulpstoffen",   "l",    0.15, "Brabant Water", None,       0.0),

    ("gehakt",           "Gehakt half om half",        "Hartig",        "kg", 780.00, "Slagerij Vermeer", None,     0.0),
    ("kaas-belegen",     "Belegen kaas geraspt",       "Hartig",        "kg", 920.00, "Zijerveld",     None,        0.0),

    ("zak-brood",        "Broodzak papier",            "Verpakking",    "st",   5.00, "Bunzl",         None,        0.0),
    ("zak-klein",        "Papieren zak klein",         "Verpakking",    "st",   2.20, "Bunzl",         None,        0.0),
    ("doos-taart",       "Taartdoos 26 cm",            "Verpakking",    "st",  45.00, "Bunzl",         None,        0.0),
    ("doos-gebak",       "Gebaksdoos klein",           "Verpakking",    "st",   9.50, "Bunzl",         None,        0.0),
]

# ---------------------------------------------------------------------------
# Recepten, op bakkerspercentage
#
# Alle percentages zijn ten opzichte van het meel in het recept, zoals in de
# bakkerij gebruikelijk. Het meel telt dus altijd samen op tot 100.
# ---------------------------------------------------------------------------
RECEPTEN = [
    {
        "id": "wit-800", "naam": "Wit tarwebrood 800 g", "groep": "Brood",
        "meelbasis_kg": 25,
        "percentages": {"bloem-patent": 100, "water": 60, "gist": 2.2, "zout": 1.9,
                        "margarine": 2.5, "verbeteraar": 0.5},
        "garnering": {},
        "deeggewicht_g": 920, "bakverlies_pct": 12.0,
        "arbeid_min": 45, "oven_min": 55, "verpakking": {"zak-brood": 1},
        "verkoop_incl": 3.25, "per_week": 900,
    },
    {
        "id": "volkoren-800", "naam": "Volkorenbrood 800 g", "groep": "Brood",
        "meelbasis_kg": 25,
        "percentages": {"meel-volkoren": 100, "water": 66, "gist": 2.4, "zout": 1.9,
                        "margarine": 2.5, "verbeteraar": 0.8},
        "garnering": {},
        "deeggewicht_g": 935, "bakverlies_pct": 13.0,
        "arbeid_min": 48, "oven_min": 58, "verpakking": {"zak-brood": 1},
        "verkoop_incl": 3.55, "per_week": 620,
    },
    {
        "id": "meergranen-800", "naam": "Meergranenbrood met zaden 800 g", "groep": "Brood",
        "meelbasis_kg": 20,
        "percentages": {"meel-volkoren": 60, "bloem-brood": 30, "meel-rogge": 10,
                        "water": 68, "gist": 2.4, "zout": 1.9, "margarine": 3.0,
                        "zonnebloempit": 8, "lijnzaad": 5, "sesamzaad": 3, "pompoenpit": 4,
                        "zemelen": 6, "verbeteraar": 0.8},
        "garnering": {"zonnebloempit": 0.006, "maanzaad": 0.003},
        "deeggewicht_g": 950, "bakverlies_pct": 13.5,
        "arbeid_min": 58, "oven_min": 58, "verpakking": {"zak-brood": 1},
        "verkoop_incl": 4.25, "per_week": 430,
    },
    {
        "id": "desem-spelt", "naam": "Speltdesem vloerbrood", "groep": "Brood",
        "meelbasis_kg": 15,
        "percentages": {"meel-spelt": 80, "bloem-patent": 20, "water": 72,
                        "desem": 22, "gist": 0.4, "zout": 2.0},
        "garnering": {},
        "deeggewicht_g": 880, "bakverlies_pct": 14.0,
        "arbeid_min": 70, "oven_min": 62, "verpakking": {"zak-brood": 1},
        "verkoop_incl": 4.95, "per_week": 240,
    },
    {
        "id": "rogge-vol", "naam": "Fries roggebrood", "groep": "Brood",
        "meelbasis_kg": 30,
        "percentages": {"meel-rogge": 100, "water": 78, "zout": 1.6, "desem": 10},
        "garnering": {},
        "deeggewicht_g": 1050, "bakverlies_pct": 8.0,
        "arbeid_min": 40, "oven_min": 240, "verpakking": {"zak-brood": 1},
        "verkoop_incl": 3.10, "per_week": 180,
    },
    {
        "id": "kadet-maanzaad", "naam": "Kadetje met maanzaad", "groep": "Klein brood",
        "meelbasis_kg": 12,
        "percentages": {"bloem-patent": 100, "water": 58, "gist": 3.0, "zout": 1.8,
                        "margarine": 4.0, "suiker": 2.0, "verbeteraar": 0.6},
        "garnering": {"maanzaad": 0.0025},
        "deeggewicht_g": 62, "bakverlies_pct": 14.0,
        "arbeid_min": 90, "oven_min": 22, "verpakking": {"zak-klein": 1},
        "verkoop_incl": 0.65, "per_week": 1450,
    },
    {
        "id": "croissant", "naam": "Roomboter croissant", "groep": "Viennoiserie",
        "meelbasis_kg": 10,
        "percentages": {"bloem-patent": 100, "water": 26, "melk-vol": 24, "gist": 4.0,
                        "zout": 1.9, "suiker": 10, "plaatboter": 50, "ei-vloeibaar": 4},
        "garnering": {},
        "deeggewicht_g": 72, "bakverlies_pct": 16.0,
        "arbeid_min": 240, "oven_min": 35, "verpakking": {"zak-klein": 1},
        "verkoop_incl": 1.60, "per_week": 600,
    },
    {
        "id": "chocobroodje", "naam": "Chocoladebroodje", "groep": "Viennoiserie",
        "meelbasis_kg": 10,
        "percentages": {"bloem-patent": 100, "water": 26, "melk-vol": 24, "gist": 4.0,
                        "zout": 1.9, "suiker": 10, "plaatboter": 50, "ei-vloeibaar": 4,
                        "chocolade": 14},
        "garnering": {},
        "deeggewicht_g": 80, "bakverlies_pct": 15.0,
        "arbeid_min": 250, "oven_min": 35, "verpakking": {"zak-klein": 1},
        "verkoop_incl": 1.85, "per_week": 350,
    },
    {
        "id": "italiaans-durum", "naam": "Italiaans landbrood met durum", "groep": "Brood",
        "meelbasis_kg": 14,
        "percentages": {"bloem-patent": 65, "gries-durum": 35, "water": 66,
                        "gist": 1.6, "zout": 2.0, "desem": 12},
        "garnering": {"sesamzaad": 0.004},
        "deeggewicht_g": 640, "bakverlies_pct": 13.0,
        "arbeid_min": 62, "oven_min": 48, "verpakking": {"zak-brood": 1},
        "verkoop_incl": 3.75, "per_week": 210,
    },
    {
        "id": "kaasbroodje", "naam": "Kaasbroodje", "groep": "Hartig",
        "meelbasis_kg": 6,
        "percentages": {"bloem-patent": 100, "water": 50, "gist": 4.0, "zout": 1.6,
                        "margarine": 10, "melk-vol": 10, "ei-vloeibaar": 6,
                        "kaas-belegen": 55},
        "garnering": {"kaas-belegen": 0.012},
        "deeggewicht_g": 95, "bakverlies_pct": 12.0,
        "arbeid_min": 105, "oven_min": 28, "verpakking": {"zak-klein": 1},
        "verkoop_incl": 2.15, "per_week": 380,
    },
    {
        "id": "worstenbroodje", "naam": "Worstenbroodje", "groep": "Hartig",
        "meelbasis_kg": 8,
        "percentages": {"bloem-patent": 100, "water": 52, "gist": 4.0, "zout": 1.6,
                        "margarine": 12, "melk-vol": 8, "ei-vloeibaar": 5,
                        "gehakt": 95},
        "garnering": {},
        "deeggewicht_g": 105, "bakverlies_pct": 11.0,
        "arbeid_min": 150, "oven_min": 30, "verpakking": {"zak-klein": 1},
        "verkoop_incl": 2.35, "per_week": 500,
    },
    {
        "id": "amandelstaaf", "naam": "Roomboter amandelstaaf", "groep": "Banket",
        "meelbasis_kg": 6,
        "percentages": {"bloem-patent": 100, "water": 42, "zout": 1.5,
                        "roomboter": 85, "spijs": 175, "ei-vloeibaar": 14,
                        "amandelschaaf": 8},
        "garnering": {},
        "deeggewicht_g": 340, "bakverlies_pct": 9.0,
        "arbeid_min": 110, "oven_min": 32, "verpakking": {"doos-gebak": 1},
        "verkoop_incl": 5.25, "per_week": 120,
    },
    {
        "id": "appeltaart", "naam": "Hollandse appeltaart", "groep": "Banket",
        "meelbasis_kg": 4,
        "percentages": {"bloem-patent": 100, "roomboter": 62, "basterdsuiker": 45,
                        "ei-vloeibaar": 12, "zout": 1.0,
                        "appel": 300, "rozijn": 20, "kaneel": 1.2, "suiker": 22},
        "garnering": {},
        "deeggewicht_g": 1580, "bakverlies_pct": 7.0,
        "arbeid_min": 150, "oven_min": 65, "verpakking": {"doos-taart": 1},
        "verkoop_incl": 18.95, "per_week": 60,
    },
    {
        "id": "slagroomtaart", "naam": "Slagroomtaart 8 personen", "groep": "Banket",
        "meelbasis_kg": 2.4,
        "percentages": {"bloem-patent": 100, "ei-vloeibaar": 175, "suiker": 110,
                        "slagroom": 320, "appel": 90},
        "garnering": {"amandelschaaf": 0.020},
        "deeggewicht_g": 1650, "bakverlies_pct": 6.0,
        "arbeid_min": 165, "oven_min": 30, "verpakking": {"doos-taart": 1},
        "verkoop_incl": 22.50, "per_week": 45,
    },
]

# ---------------------------------------------------------------------------
# Inkooplagen, oudste eerst. Dit is de FIFO-voorraad.
# (grondstof, dagen geleden, aantal, prijs per 100, restant)
# ---------------------------------------------------------------------------
LEVERINGEN = [
    ("bloem-patent",  96, 2000, 44.10, 0),
    ("bloem-patent",  61, 2000, 45.80, 780),
    ("bloem-patent",  26, 2000, 48.50, 2000),
    ("bloem-brood",   54, 1000, 44.90, 320),
    ("bloem-brood",   19, 1000, 46.80, 1000),
    ("meel-volkoren", 68, 1500, 42.30, 410),
    ("meel-volkoren", 25, 1500, 45.20, 1500),
    ("meel-spelt",    72,  400, 88.00, 95),
    ("meel-spelt",    23,  400, 92.00, 400),
    ("meel-rogge",    58,  600, 51.50, 180),
    ("meel-rogge",    21,  600, 54.00, 600),
    ("gries-durum",   80,  200, 84.00, 140),
    ("zemelen",       45,  150, 32.00, 92),

    ("roomboter",     84,  200, 1020.00, 0),
    ("roomboter",     49,  200, 880.00, 46),
    ("roomboter",     14,  250, 780.00, 250),
    ("plaatboter",    52,  150, 940.00, 38),
    ("plaatboter",    17,  150, 845.00, 150),
    ("margarine",     40,  300, 218.00, 165),
    ("margarine",     12,  300, 225.00, 300),
    ("melk-vol",      10,  400,  95.00, 315),
    ("slagroom",       8,  120, 420.00, 88),
    ("karnemelk",     10,  150,  80.00, 96),
    ("ei-vloeibaar",   9,  250, 330.00, 172),

    ("maanzaad",      75,   80, 455.00, 26),
    ("maanzaad",      18,   80, 480.00, 80),
    ("zonnebloempit", 66,  200, 182.00, 54),
    ("zonnebloempit", 20,  200, 195.00, 200),
    ("sesamzaad",     70,  100, 268.00, 61),
    ("lijnzaad",      70,  120, 158.00, 78),
    ("pompoenpit",    88,   50, 505.00, 31),
    ("amandelschaaf", 62,   60, 1140.00, 22),
    ("amandelschaaf", 15,   60, 1180.00, 60),
    ("hazelnoot",     90,   30, 1450.00, 21),

    ("suiker",        56,  500, 128.00, 140),
    ("suiker",        22,  500, 135.00, 500),
    ("basterdsuiker", 44,  200, 149.00, 118),
    ("spijs",         33,  300, 655.00, 96),
    ("spijs",         11,  300, 680.00, 300),
    ("chocolade",     37,  120, 812.00, 44),
    ("chocolade",     13,  120, 850.00, 120),
    ("rozijn",        64,  100, 325.00, 58),
    ("kaneel",        95,   10, 1100.00, 7),
    ("appel",          6,  400, 165.00, 268),

    ("gist",           7,  120, 280.00, 78),
    ("zout",          78,  300,  62.00, 164),
    ("verbeteraar",   35,  150, 378.00, 71),
    ("verbeteraar",   10,  150, 390.00, 150),
    ("desem",         16,  200, 210.00, 142),
    ("water",          1, 50000,  0.15, 50000),

    ("gehakt",         4,  300, 780.00, 214),
    ("kaas-belegen",   9,   60, 920.00, 38),

    ("zak-brood",     30, 20000, 5.00, 12400),
    ("zak-klein",     30, 30000, 2.20, 19800),
    ("doos-taart",    47,  1500, 45.00, 860),
    ("doos-gebak",    47,  2000,  9.50, 1240),
]

VASTE_KOSTEN = {
    "uurloon_bakkerij": 26.40,
    "uurloon_toelichting": "bruto plus werkgeverslasten, cao Bakkersbedrijf, voorbeeld",
    "ovenuur": 7.20,
    "ovenuur_toelichting": "gas plus elektra plus afschrijving per ovenuur, voorbeeld",
    "btw_brood_banket": 0.09,
}


def main():
    vandaag = datetime.date.today()

    grondstoffen = []
    for gid, naam, groep, eenheid, prijs, lev, notering, doorwerking in GRONDSTOFFEN:
        grondstoffen.append({
            "id": gid,
            "naam": naam,
            "groep": groep,
            "eenheid": eenheid,
            "handelseenheid": "100 " + eenheid,
            "laatste_prijs_per_100": prijs,
            "leverancier": lev,
            "notering": notering,
            "doorwerking": doorwerking,
        })

    leveringen = []
    for i, (gid, dagen, aantal, prijs, restant) in enumerate(LEVERINGEN, start=1):
        datum = vandaag - datetime.timedelta(days=dagen)
        leveringen.append({
            "id": "L%03d" % i,
            "grondstof": gid,
            "datum": datum.isoformat(),
            "aantal": float(aantal),
            "restant": float(restant),
            "prijs_per_100": prijs,
            "batch": "%s-%s" % (gid[:3].upper(), datum.strftime("%y%m%d")),
        })

    (DATA / "grondstoffen.json").write_text(
        json.dumps({"vaste_kosten": VASTE_KOSTEN, "grondstoffen": grondstoffen},
                   ensure_ascii=False, indent=2))
    (DATA / "recepten.json").write_text(
        json.dumps({"recepten": RECEPTEN}, ensure_ascii=False, indent=2))
    (DATA / "inkoop.json").write_text(
        json.dumps({"leveringen": leveringen}, ensure_ascii=False, indent=2))

    print("Klaargezet in %s" % DATA)
    print("  %d grondstoffen" % len(grondstoffen))
    print("  %d recepten" % len(RECEPTEN))
    print("  %d inkooplagen" % len(leveringen))


if __name__ == "__main__":
    main()
