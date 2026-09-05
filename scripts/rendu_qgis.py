#!/usr/bin/env python3
"""Construit un projet QGIS (.qgz) avec fond de carte + rend un PNG (headless).

- Fond de carte XYZ (CARTO Positron) sous la couche des communes.
- Categorie 'Autre' rendue transparente pour faire ressortir les strates.
- Ecrit : france_toponymes.qgz  et  web/rendu_qgis.png

A lancer avec le Python embarque de QGIS (voir scripts/rendre.sh).
"""
import json
import os
from qgis.core import (
    QgsApplication, QgsVectorLayer, QgsRasterLayer, QgsProject,
    QgsCoordinateReferenceSystem, QgsRectangle, QgsMapSettings,
    QgsMapRendererParallelJob, QgsCoordinateTransform,
)
from qgis.PyQt.QtCore import QSize, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QPainter, QFont, QImage

PREFIX = "/Users/augustin/Applications/QGIS.app/Contents/MacOS"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(BASE, "config", "categories.json")
GEOJSON = os.path.join(BASE, "data", "communes_classees.geojson")
QML = os.path.join(BASE, "styles", "communes.qml")
QGZ = os.path.join(BASE, "france_toponymes.qgz")
PNG = os.path.join(BASE, "web", "rendu_qgis.png")

XYZ = ("type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/"
       "Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}&zmax=16&zmin=0")


def composer_avec_legende(carte, cats):
    """Ajoute une marge blanche a droite avec la legende (hors 'Autre').

    La legende ne recouvre ainsi aucune commune (Bretagne comprise).
    Renvoie une nouvelle image carte + legende.
    """
    entrees = [c for c in cats if c["type"] != "defaut"]
    marge, pad, sw, gap = 650, 30, 30, 14
    canvas = QImage(carte.width() + marge, carte.height(), QImage.Format_ARGB32)
    canvas.fill(QColor(255, 255, 255))
    p = QPainter(canvas)
    p.setRenderHint(QPainter.Antialiasing)
    p.drawImage(0, 0, carte)

    x = carte.width() + pad
    largeur = marge - pad * 2
    titre = QFont("Helvetica", 22)
    titre.setBold(True)
    p.setFont(titre)
    p.setPen(QColor(25, 25, 25))
    p.drawText(QRectF(x, pad, largeur, 56),
               Qt.AlignLeft | Qt.AlignVCenter, "Toponymes de France")
    sous = QFont("Helvetica", 15)
    sous.setItalic(True)
    p.setFont(sous)
    p.setPen(QColor(90, 90, 90))
    p.drawText(QRectF(x, pad + 46, largeur, 30),
               Qt.AlignLeft | Qt.AlignVCenter, "prefixes & suffixes des communes")

    # Hauteur de ligne calee sur l'espace disponible
    y0 = pad + 96
    lh = min(46, (carte.height() - y0 - pad) // len(entrees))
    p.setFont(QFont("Helvetica", 15))
    y = y0
    for c in entrees:
        p.setBrush(QColor(c["couleur"]))
        p.setPen(QColor(120, 120, 120))
        p.drawRoundedRect(QRectF(x, y + (lh - sw + 6) / 2, sw, sw - 6), 4, 4)
        p.setPen(QColor(25, 25, 25))
        p.drawText(QRectF(x + sw + gap, y, largeur - sw - gap, lh),
                   Qt.AlignLeft | Qt.AlignVCenter, c["nom"])
        y += lh
    p.end()
    return canvas


def main():
    QgsApplication.setPrefixPath(PREFIX, True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    # Couche communes + style
    communes = QgsVectorLayer(GEOJSON, "Communes", "ogr")
    if not communes.isValid():
        raise SystemExit("Couche communes invalide")
    communes.loadNamedStyle(QML)

    # Rendre 'Autre' transparent
    renderer = communes.renderer()
    if hasattr(renderer, "categories"):
        for cat in renderer.categories():
            if cat.value() == "autre" and cat.symbol():
                cat.symbol().setOpacity(0.0)
    communes.triggerRepaint()

    # Fond de carte
    fond = QgsRasterLayer(XYZ, "Fond CARTO", "wms")

    crs3857 = QgsCoordinateReferenceSystem("EPSG:3857")
    proj = QgsProject.instance()
    proj.setCrs(crs3857)
    proj.addMapLayer(fond)
    proj.addMapLayer(communes)
    proj.write(QGZ)
    print(f"Projet ecrit : {QGZ}")

    # Rendu PNG
    xform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"), crs3857, proj)
    extent = xform.transformBoundingBox(QgsRectangle(-5.2, 41.2, 9.8, 51.2))

    ms = QgsMapSettings()
    ms.setLayers([communes, fond])          # communes au-dessus du fond
    ms.setBackgroundColor(QColor(26, 26, 26))
    ms.setOutputSize(QSize(1500, 1600))
    ms.setDestinationCrs(crs3857)
    ms.setExtent(extent)

    job = QgsMapRendererParallelJob(ms)
    job.start()
    job.waitForFinished()
    image = job.renderedImage()

    with open(CONFIG, encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    image = composer_avec_legende(image, cats)

    os.makedirs(os.path.dirname(PNG), exist_ok=True)
    image.save(PNG)
    print(f"Rendu PNG ecrit : {PNG}")

    qgs.exitQgis()


if __name__ == "__main__":
    main()
