#!/usr/bin/env python3
"""Telecharge le fichier GeoJSON des communes de France (avec geometrie).

Source : depot france-geojson de Gregoire David (donnees IGN/INSEE, domaine public).
Le fichier fait ~90 Mo. Il est enregistre dans data/communes.geojson.
"""
import os
import sys
import urllib.request

URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson"
DEST = os.path.join(os.path.dirname(__file__), "..", "data", "communes.geojson")


def _progress(block_num, block_size, total_size):
    telecharge = block_num * block_size
    if total_size > 0:
        pct = min(100, telecharge * 100 // total_size)
        sys.stdout.write(f"\r  {pct:3d} %  ({telecharge // (1024 * 1024)} Mo)")
        sys.stdout.flush()


def main():
    dest = os.path.abspath(DEST)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Telechargement des communes depuis :\n  {URL}")
    urllib.request.urlretrieve(URL, dest, _progress)
    print(f"\nEnregistre dans : {dest}")
    print(f"Taille : {os.path.getsize(dest) // (1024 * 1024)} Mo")


if __name__ == "__main__":
    main()
