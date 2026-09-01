# Bakkerijsysteem

Kostprijs, marge, voorraad en marktnoteringen voor een bakkerij. Draait op je eigen
computer, zonder installatie van pakketten. Alleen Python, dat staat op elke Mac al.

## Starten

```
python3 seed.py      # eenmalig: zet de voorbeelddata klaar
python3 markt.py     # haalt de actuele marktnoteringen op
python3 start.py     # start het systeem, je browser gaat vanzelf open
```

Daarna staat alles op `http://localhost:8777`. Stoppen doe je met ctrl-c.

## Wat het doet

**Vier schermen.**

| Scherm | Waarvoor |
| --- | --- |
| Marge per product | Kostprijs en marge per product, slechtste bovenaan, met schuiven om te zien wat een prijsbeweging doet |
| Voorraad en FIFO | Alle partijen op datum, hoelang je voorraad nog duurt, en het verschil tussen je voorraadprijs en vandaag bijkopen |
| Recepten | Receptuur op bakkerspercentage, deeggewicht, bakverlies en kostprijsopbouw |
| Marktnoteringen | De weeknoteringen die het systeem zelf ophaalt, met hun verloop over twee jaar |
| Je eigen cijfers | Je eigen bestanden erin zetten, en vier lijsten voor wie het liever in Excel doet |

**Twee kostprijzen, en het verschil is de kern.** De FIFO-kostprijs rekent met de partij
waar je nu echt uit bakt, oudste eerst. De vervangingswaarde rekent alsof je vandaag
alles opnieuw moet inkopen. Draai je op oude, goedkope voorraad, dan ziet je marge er
goed uit terwijl de markt allang is doorgelopen. De kolom "waar je nu uit bakt" laat
zien hoeveel weken dat nog goed gaat.

**Receptuur op bakkerspercentage.** Alles ten opzichte van het meel, zoals in de
bakkerij. Het systeem rekent zelf uit hoeveel deeg dat is, hoeveel stuks er uit een
batch komen en wat het bakverlies met het eindgewicht doet.

## De marktnoteringen

Negen noteringen, allemaal uit de open data van de Europese Commissie. Gratis en zonder
sleutel of abonnement:

| Notering | Bron |
| --- | --- |
| Baktarwe, rogge van bakkwaliteit, tarwezemelen | graanmarkt Duitsland |
| Durumtarwe | graanmarkt Frankrijk |
| Boter, magere melkpoeder, volle melkpoeder | zuivelmarkt Nederland |
| Witte suiker | suikermarkt, EU-gemiddelde |
| Ruwe zonnebloemolie | oliezaden Roemenie |

Voor eieren, zaden, noten, spijs en chocolade bestaat geen Europese notering. Die staan
zonder koppeling in het systeem en werk je bij met je eigen inkoopfactuur.

**Bloem is geen tarwe.** Tussen de tarwenotering en jouw zak bloem zitten maalloon,
transport en de marge van de molenaar, en er gaat ongeveer 130 kg tarwe in 100 kg bloem.
Daarom heeft elke grondstof een doorwerking in `data/grondstoffen.json`: welk deel van
een marktbeweging in jouw inkoopprijs terechtkomt. Voor bloem staat die op 0,55, voor
roomboter op 0,90. Pas ze aan als jouw leverancier zich anders gedraagt, dat is precies
het gesprek dat je met hem wil voeren.

**Waarom een servertje en geen los bestand.** Een pagina die je met dubbelklikken opent
mag van je browser geen gegevens van buiten halen. Draait dezelfde pagina op localhost,
dan mag het wel. Vandaar `start.py`.

## Je eigen cijfers erin

**De kortste weg: gooi je bestanden erin en vraag het aan Claude Code.** In het tabblad
Je eigen cijfers zet je je facturen, je receptenboek of je prijslijst neer. Pdf, Excel,
een foto van een papiertje, het maakt niet uit. Ze belanden in `data/aangeleverd/`. Daar
staat een kant en klare vraag bij die je in Claude Code plakt: hij leest de bestanden en
zet de cijfers op de juiste plek, met een kopie van je oude gegevens vooraf. Je hoeft
niets te weten over de vorm van de bestanden.

**Liever zelf in Excel.** Op hetzelfde tabblad download je vier lijsten die al
gevuld zijn met wat er nu in het systeem staat. Je opent ze in Excel, vervangt de regels
door die van jou, slaat op als csv en zet ze terug. Puntkomma of komma maakt niet uit, en
een prijs mag als 48,50 of als 48.50.

- **Inkoopprijzen van je leverancier**, de prijs per 100 kg zoals op de factuur
- **Recepten, verkoopprijzen en weekaantallen**, een regel per product
- **Samenstelling van je recepten**, de bakkerspercentages, garnering en verpakking
- **Je voorraadpartijen**, waarop de berekening oudste partij eerst draait

Elke regel die niet klopt komt terug in beeld met de reden erbij, in plaats van dat hij
stilletjes verdwijnt. En voordat er iets wordt overschreven gaat er een kopie met datum
naar `data/kopieen/`, dus je raakt nooit iets kwijt.

**De directe weg.** Alles staat ook gewoon in `data/`, JSON-bestanden die je met elke
teksteditor opent.

- `grondstoffen.json` — je grondstoffen, leveranciers, laatste inkoopprijs per 100 kg,
  en de koppeling naar een marktnotering
- `recepten.json` — je receptuur op bakkerspercentage, met deeggewicht, bakverlies,
  arbeid, oventijd, verkoopprijs en weekaantallen
- `inkoop.json` — je voorraadpartijen: datum, aantal, restant en prijs
- `noteringen.json` — de opgehaalde marktdata, dit bestand beheer je niet zelf

Leveringen en productie boek je in het scherm zelf. Een levering komt achteraan in de
rij, productie haalt de grondstoffen vooraan uit de oudste partij.

Wil je opnieuw beginnen met de voorbeelddata: `python3 seed.py`. Let op, dat overschrijft
wat je hebt ingevuld.

## Waar het aan grenst

Dit is geen boekhoudpakket en geen vervanging van je ERP. Het rekent kostprijs en marge
tot en met de directe productiekosten: grondstoffen, arbeid in de bakkerij, oven en
verpakking. Winkelkosten, bezorging, derving en overhead zitten er niet in. Het is
bedoeld om het gesprek over je prijskaart en je leverancier scherp te krijgen, met
cijfers erbij.

De ingevulde recepten en prijzen zijn voorbeelden. Ze zijn plausibel gekozen, maar het
zijn niet jouw cijfers tot je ze vervangt.
