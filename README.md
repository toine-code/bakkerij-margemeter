# Margemeter voor de bakkerij

Wat je zag tijdens de presentatie, om zelf mee verder te gaan. Twee dingen zitten
erin, van klein naar groot.

## 1. De margemeter

`margecalculator/index.html` is één bestand. Dubbelklik het en het opent in je
browser. Schuif aan de grondstofprijzen en je ziet meteen welk product je marge
opvreet en wat dat je per jaar kost.

Dit is precies het bestand dat in de zaal in tien minuten gebouwd is. De opdracht
waarmee dat gebeurde staat in `prompt-margemeter.md`, woord voor woord. Plak hem in
Claude Code en je hebt hem opnieuw, en dan kun je hem verder aanpassen aan je eigen
zaak.

## 2. Het bakkerijsysteem

Groter, en dichter bij hoe het echt werkt in je bakkerij.

- Je grondstoffen met de inkoopprijs per 100 kg zoals hij op de factuur staat
- Je recepten op bakkerspercentage, met deeggewicht, bakverlies, werk en oventijd
- Je voorraad in partijen, en het rekent uit de oudste partij eerst
- De marktnoteringen voor tarwe, rogge, boter, suiker en zonnebloem, die het zelf
  ophaalt bij de Europese Commissie

**Starten.** Dubbelklik `Start bakkerijsysteem.command` op een Mac, of
`Start bakkerijsysteem.bat` op Windows. De eerste keer duurt het een halve minuut,
daarna opent je browser vanzelf. Er blijft een zwart venster openstaan, dat hoort zo.
Sluit je dat venster, dan stopt het systeem.

Er is Python 3 voor nodig. Op een Mac staat dat er al. Op Windows haal je het
eenmalig op bij python.org, en vink je bij het installeren "Add Python to PATH" aan.

## Je eigen cijfers erin, via Excel

In het systeem zit een tabblad **Je eigen cijfers**. Daar staan vier lijsten klaar,
alvast gevuld met de voorbeeldgegevens:

- je inkoopprijzen, per 100 kg, zoals ze op de factuur van je leverancier staan
- je recepten, met je verkoopprijzen en hoeveel je er per week van verkoopt
- de samenstelling van je recepten, op bakkerspercentage
- je voorraadpartijen, waarop het rekenen met de oudste partij eerst draait

Download er een, open hem in Excel, vervang de regels door die van jou, sla op als csv
en zet hem terug. Puntkomma of komma maakt niet uit, en een prijs mag je schrijven als
48,50 of als 48.50. Klopt een regel niet, dan zie je meteen welke en waarom, in plaats
van dat hij stilletjes verdwijnt. Voordat er iets wordt overschreven gaat er een kopie
met datum naar `bakkerijsysteem/data/kopieen/`, dus je raakt nooit iets kwijt.

Leveringen en gebakken batches boek je gewoon in het scherm zelf.

## Wat je moet weten

- **De cijfers die er nu in staan zijn voorbeelden.** Ze zijn plausibel gekozen, maar
  het zijn niet jouw cijfers tot je ze vervangt.
- **Het rekent wat jij invult.** Zet je er een verkeerde boterprijs in, dan komt er
  een keurige verkeerde uitkomst uit. Controleer de eerste tabel een keer met de hand.
- **Alles blijft op je eigen computer.** Je recepten en prijzen gaan nergens heen. Het
  enige verkeer naar buiten is het ophalen van de marktnoteringen, en dat gebeurt
  alleen als je op die knop drukt.
- **Het is geen boekhouding.** Het rekent tot en met je directe productiekosten:
  grondstoffen, werk in de bakkerij, oven en verpakking. Winkelkosten, bezorging,
  derving en overhead zitten er niet in. Overleg met je accountant voor je je
  prijskaart omgooit.
- **Claude Code kost geld.** Ongeveer 20 dollar per maand voor het instapabonnement.
  Het gebruiken van wat hier staat kost niets, dat draait gewoon op je eigen computer.

## Vragen

Toine Boelens, YUTU, Den Bosch. toine@yutugrow.nl. Loop je vast, mail gerust.
