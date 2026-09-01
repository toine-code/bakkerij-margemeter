#!/bin/bash
# Dubbelklik dit bestand om het bakkerijsysteem te starten.
# Er opent een zwart venster, dat mag je laten staan. Sluit je het, dan stopt het systeem.
cd "$(dirname "$0")/bakkerijsysteem" || exit 1

echo ""
echo "  Bakkerijsysteem"
echo "  ---------------"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "  Python 3 staat niet op deze computer."
  echo "  Haal het op bij python.org, installeer het, en dubbelklik dit bestand opnieuw."
  echo ""
  read -r -p "  Druk op enter om te sluiten."
  exit 1
fi

if [ ! -f data/grondstoffen.json ]; then
  echo "  Eerste keer: de voorbeeldgegevens klaarzetten..."
  python3 seed.py
  echo ""
  echo "  Marktnoteringen ophalen..."
  python3 markt.py
  echo ""
fi

python3 start.py
echo ""
read -r -p "  Het systeem is gestopt. Druk op enter om dit venster te sluiten."
