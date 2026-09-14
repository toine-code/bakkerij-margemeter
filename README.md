# Het bakkerijsysteem

Wat je op 14 september in Vught zag, om zelf mee verder te gaan.

## Meteen bekijken

Open `webversie/index.html` in je browser, of ga naar
<https://toine-code.github.io/bakkerij-margemeter/webversie/index.html>.

Daar zit alles in: je marge per product, wat een grondstof met je hele assortiment doet,
je voorraad, je receptuur en de marktnoteringen. Op het tabblad **Claude Code** staat hoe
je zelf begint, en op het tabblad **Let op** wat je eerst moet uitzetten.

## Op je eigen computer

In `bakkerijsysteem/` staat de versie die echt rekent en die je met je eigen cijfers kunt
voeden. Start hem met:

```
python3 seed.py      # eenmalig, zet de voorbeeldgegevens klaar
python3 markt.py     # haalt de actuele marktnoteringen op
python3 start.py     # start het systeem in je browser
```

Of geef deze map gewoon aan Claude Code en vraag of hij hem start.

## Voordat je je eigen cijfers erin zet

Zet in Claude uit dat je gegevens gebruikt worden om het model te trainen. Hoe dat moet
staat op het tabblad **Let op**. Daar staat ook waar je zelf verantwoordelijk voor blijft.

## Vragen

Toine Boelens, YUTU, Den Bosch. toine@yutugrow.nl
