#!/usr/bin/env python3
"""Genere le style QGIS (.qml) categorise a partir de config/categories.json.

Le style colore la couche selon le champ 'categorie', avec les memes couleurs
que la classification. Une seule source de verite : le fichier JSON.

Resultat : styles/communes.qml
Dans QGIS : clic droit sur la couche > Proprietes > Symbologie > Charger le style.
"""
import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG = os.path.join(BASE, "config", "categories.json")
SORTIE = os.path.join(BASE, "styles", "communes.qml")


def hex_vers_rgba(hexa, alpha=255):
    hexa = hexa.lstrip("#")
    r, g, b = int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16)
    return f"{r},{g},{b},{alpha}"


def main():
    with open(CONFIG, encoding="utf-8") as f:
        cats = json.load(f)["categories"]

    categories_xml = []
    symbols_xml = []
    for i, c in enumerate(cats):
        val = c["id"]
        label = c["nom"].replace("&", "&amp;").replace('"', "&quot;")
        categories_xml.append(
            f'      <category value="{val}" symbol="{i}" label="{label}" render="true"/>'
        )
        couleur = hex_vers_rgba(c["couleur"])
        symbols_xml.append(f"""      <symbol type="fill" name="{i}" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <Option type="Map">
            <Option type="QString" name="color" value="{couleur}"/>
            <Option type="QString" name="style" value="solid"/>
            <Option type="QString" name="outline_style" value="solid"/>
            <Option type="QString" name="outline_color" value="255,255,255,60"/>
            <Option type="QString" name="outline_width" value="0.05"/>
            <Option type="QString" name="outline_width_unit" value="MM"/>
          </Option>
        </layer>
      </symbol>""")

    qml = f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34" styleCategories="Symbology">
  <renderer-v2 forceraster="0" type="categorizedSymbol" attr="categorie" symbollevels="0" enableorderby="0">
    <categories>
{chr(10).join(categories_xml)}
    </categories>
    <symbols>
{chr(10).join(symbols_xml)}
    </symbols>
  </renderer-v2>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
"""

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(qml)
    print(f"Style ecrit : {SORTIE}")
    print(f"{len(cats)} categories.")


if __name__ == "__main__":
    main()
