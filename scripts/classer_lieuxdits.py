#!/usr/bin/env python3
"""Classe les lieux-dits OSM avec les memes regles que les communes.

- Departement determine par jointure spatiale (point-in-polygon, departements.geojson)
  pour appliquer les regles regionales (breton, savoyard, flamand, bach).
- Sortie : data/osm/lieuxdits_classes.geojson (nom, cat, cn).
"""
import json
import os
import sys
from collections import Counter

from shapely.geometry import shape, Point
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classer_communes import charger_regles, classer, CONFIG  # noqa: E402

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEPTS = os.path.join(BASE, "data", "osm", "departements.geojson")
RAW = os.path.join(BASE, "data", "osm", "lieuxdits_raw.geojson")
OUT = os.path.join(BASE, "data", "osm", "lieuxdits_classes.geojson")
COMPTE = os.path.join(BASE, "data", "osm", "lieuxdits_compte.json")


def main():
    print("Chargement des departements ...")
    deps = json.load(open(DEPTS, encoding="utf-8"))
    polys, codes = [], []
    for f in deps["features"]:
        polys.append(shape(f["geometry"]))
        codes.append(f["properties"]["code"])
    tree = STRtree(polys)

    def dept_of(pt):
        for i in tree.query(pt):
            if polys[i].contains(pt):
                return codes[i]
        return None

    regles = charger_regles(CONFIG)
    lib = {i: n for i, n, _t, _m, _d in regles}

    print(f"Lecture {RAW} ...")
    raw = json.load(open(RAW, encoding="utf-8"))
    feats = raw["features"]
    print(f"{len(feats)} points a classer ...")

    out = []
    compte = Counter()
    for k, feat in enumerate(feats):
        g = feat.get("geometry")
        if not g or g.get("type") != "Point":
            continue
        lon, lat = g["coordinates"][0], g["coordinates"][1]
        nom = feat["properties"].get("name", "") or ""
        d = dept_of(Point(lon, lat))
        cat = classer(nom, regles, d)
        compte[cat] += 1
        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
            "properties": {"nom": nom, "cat": cat, "cn": lib[cat]},
        })
        if k % 100000 == 0 and k:
            print(f"  {k} ...")

    json.dump({"type": "FeatureCollection", "features": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(dict(compte), open(COMPTE, "w", encoding="utf-8"))
    total = sum(compte.values())
    print(f"\n{total} lieux-dits classes -> {OUT}\n")
    for id_, nom, _t, _m, _d in regles:
        n = compte.get(id_, 0)
        print(f"  {nom:<48} {n:>7}  ({n*100/total:4.1f} %)")


if __name__ == "__main__":
    main()
