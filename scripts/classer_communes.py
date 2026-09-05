#!/usr/bin/env python3
"""Classe chaque commune selon les regles toponymiques de config/categories.json.

Lit data/communes.geojson, ajoute a chaque entite une propriete 'categorie'
(l'id de la categorie) et 'categorie_nom' (le libelle lisible), puis ecrit
data/communes_classees.geojson (utilisable directement dans QGIS).

Aucune dependance externe : uniquement la bibliotheque standard Python.
"""
import json
import os
import re
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG = os.path.join(BASE, "config", "categories.json")
ENTREE = os.path.join(BASE, "data", "communes.geojson")
SORTIE = os.path.join(BASE, "data", "communes_classees.geojson")

# Mots de liaison a ignorer pour trouver le radical du toponyme.
# Ex : "Aix-en-Provence" -> radical "aix" ; "Neuilly-sur-Seine" -> "neuilly".
LIAISONS = {
    "sur", "sous", "les", "lès", "lez", "la", "le", "l", "en", "au", "aux",
    "de", "du", "des", "d", "et", "devant", "sainte", "saint", "st", "ste",
}


def charger_regles(chemin):
    with open(chemin, encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    regles = []
    for c in cats:
        motif = re.compile(c["motif"]) if c["motif"] else None
        regles.append((c["id"], c["nom"], c["type"], motif))
    return regles


def radical(nom):
    """Renvoie le premier mot significatif du nom (en minuscules)."""
    jetons = re.split(r"[-\s']", nom.lower())
    for jeton in jetons:
        if jeton and jeton not in LIAISONS:
            return jeton
    return nom.lower()


def classer(nom, regles):
    nom_min = nom.lower()
    rad = radical(nom)
    for id_, _nom_cat, type_, motif in regles:
        if type_ == "defaut":
            return id_
        if type_ in ("prefixe", "complement") and motif.search(nom_min):
            return id_
        if type_ == "suffixe" and motif.search(rad):
            return id_
    return "autre"


def main():
    if not os.path.exists(ENTREE):
        raise SystemExit(
            f"Fichier introuvable : {ENTREE}\n"
            "Lance d'abord : python scripts/telecharger_communes.py"
        )

    regles = charger_regles(CONFIG)
    libelles = {id_: nom for id_, nom, _t, _m in regles}

    print(f"Lecture de {ENTREE} ...")
    with open(ENTREE, encoding="utf-8") as f:
        geo = json.load(f)

    compte = Counter()
    for feature in geo.get("features", []):
        props = feature.setdefault("properties", {})
        nom = props.get("nom", "") or ""
        cat = classer(nom, regles)
        props["categorie"] = cat
        props["categorie_nom"] = libelles[cat]
        compte[cat] += 1

    print(f"Ecriture de {SORTIE} ...")
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(geo, f, ensure_ascii=False)

    total = sum(compte.values())
    print(f"\n{total} communes classees :\n")
    for id_, nom, _t, _m in regles:
        n = compte.get(id_, 0)
        pct = (n * 100 / total) if total else 0
        print(f"  {nom:<45} {n:>6}  ({pct:4.1f} %)")


if __name__ == "__main__":
    main()
