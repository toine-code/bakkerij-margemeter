# De prompt die je weggeeft

Dit is de tekst die je in Claude Code plakt om de margemeter te bouwen. Letterlijk plakken werkt,
er zit geen truc in. Print hem op een kaartje, dan kunnen de bakkers het thuis overdoen.

---

## De bouwprompt

```
Maak een bestand margemeter.html dat ik gewoon in mijn browser kan openen,
zonder installatie, en dat alles in de pagina zelf uitrekent.

Het is een margemeter voor mijn bakkerij.

Bovenin vier schuiven: bloem en meel, roomboter en zuivel, overige
grondstoffen, en loon en energie. Elke schuif loopt van min 50 procent tot
plus 100 procent.

Vul het met voorbeeldrecepten van een Nederlandse bakkerij: wit brood,
desembrood, croissant, chocoladebroodje, worstenbroodje, amandelstaaf,
appeltaart en slagroomtaart. Zet per product neer: de grondstoffen in grammen
per stuk, hoeveel stuks er in een batch gaan, de minuten werk en de minuten
oven per batch, de verpakking per stuk, de verkoopprijs inclusief 9 procent
btw, en hoeveel ik er per week van verkoop.

Reken per product de kostprijs per stuk uit, dus grondstoffen plus arbeid plus
oven plus verpakking, en de marge ten opzichte van de verkoopprijs exclusief
btw. Zet de producten in een tabel met de slechtste marge bovenaan. Kleur de
marge groen vanaf 60 procent, oranje tussen 45 en 60 procent, en rood
daaronder. Laat per regel zien wat de schuiven met de kostprijs doen.

Bovenin wil ik in een oogopslag zien wat mijn marge per week nu is, en hoeveel
euro per week en per jaar dat scheelt met de basis.

De inkoopprijzen moeten in de pagina aanpasbaar zijn, zodat ik mijn eigen
facturen kan invullen zonder dat jij eraan te pas komt.

Zet er duidelijk bij dat de ingevulde cijfers voorbeelden zijn en dat ik mijn
eigen inkoop moet invullen.

Schrijf alles in het Nederlands, gebruik euro's met een komma, en houd het
uiterlijk rustig en zakelijk. Geen kleurenfestival.
```

---

## Drie vervolgprompts, voor als hij eenmaal draait

**1. Je eigen prijzen erin**

```
Hier zijn mijn echte inkoopprijzen van deze week: [plak je factuurregels].
Vervang de voorbeeldprijzen hiermee en laat de rest van het model staan.
```

**2. Een advies per product**

```
Zet achter elk product een advies voor als de boter 40 procent duurder wordt:
prijs verhogen, recept aanpassen, of laten staan. Reken erbij uit welke
verkoopprijs ik nodig heb om op mijn huidige marge te blijven.
```

**3. Onthouden en afdrukken**

```
Onthoud mijn ingevulde prijzen in de browser, zodat ze er de volgende keer
nog staan. En zet er een knop bij die de tabel netjes afdrukt met de datum
erboven, zodat ik hem mee kan nemen naar mijn boekhouder.
```

**4. De echte marktnoteringen erbij**

```
Schrijf een klein script dat de weeknoteringen voor boter en baktarwe ophaalt
bij de open data van de Europese Commissie, ec.europa.eu/agrifood/api, en die
percentages in mijn margemeter zet. Laat erbij zien hoeveel de prijs is
gestegen of gedaald ten opzichte van vorig jaar.
```

**5. Doorbouwen tot een echt systeem**

```
Bouw dit uit tot een systeem dat op mijn eigen computer draait, op localhost,
zodat het de marktnoteringen zelf kan ophalen.

Zet mijn grondstoffen erin met de inkoopprijs per 100 kg zoals hij op de
factuur van mijn leverancier staat. Werk met voorraadpartijen: per levering de
datum, het aantal, de prijs en wat er nog over is. Reken volgens first in
first out, dus uit de oudste partij eerst.

Zet mijn recepten op bakkerspercentage, dus alles ten opzichte van het meel,
met deeggewicht, bakverlies, minuten werk en oventijd per batch.

Laat per product twee kostprijzen zien: wat het kost uit mijn eigen voorraad,
en wat het kost als ik vandaag alles opnieuw moet inkopen. Laat per grondstof
zien hoeveel weken mijn huidige partij nog duurt.

Haal de noteringen voor tarwe, rogge, durum, boter, melkpoeder, suiker en
zonnebloemolie op bij ec.europa.eu/agrifood/api. Geef elke grondstof een
doorwerkingsfactor, want bloem is geen tarwe: daar zit maalloon en marge van de
molenaar tussen.

Ik wil er leveringen en gebakken batches in kunnen boeken.
```

---

## Wat je erbij zegt

- Het rekent wat jij invult. Zet je er onzin in, dan komt er nette onzin uit.
- Het draait op je eigen computer. Je eigen prijzen gaan nooit het internet op.
- Dit is geen boekhoudpakket en geen advies. Het is een rekenblad dat je in tien minuten zelf maakt.
