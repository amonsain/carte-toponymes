#!/usr/bin/env python3
"""Construit un projet QGIS (.qgz) avec fond de carte + rend un PNG (headless).

- Fond de carte XYZ (CARTO Positron) sous la couche des communes.
- Categorie 'Autre' rendue transparente pour faire ressortir les strates.
- Ecrit : france_toponymes.qgz  et  web/rendu_qgis.png

A lancer avec le Python embarque de QGIS (voir scripts/rendre.sh).
"""
import os
from qgis.core import (
    QgsApplication, QgsVectorLayer, QgsRasterLayer, QgsProject,
    QgsCoordinateReferenceSystem, QgsRectangle, QgsMapSettings,
    QgsMapRendererParallelJob, QgsCoordinateTransform,
)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor

PREFIX = "/Users/augustin/Applications/QGIS.app/Contents/MacOS"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEOJSON = os.path.join(BASE, "data", "communes_classees.geojson")
QML = os.path.join(BASE, "styles", "communes.qml")
QGZ = os.path.join(BASE, "france_toponymes.qgz")
PNG = os.path.join(BASE, "web", "rendu_qgis.png")

XYZ = ("type=xyz&url=https://tile.openstreetmap.org/"
       "{z}/{x}/{y}.png&zmax=19&zmin=0")


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
    ms.setBackgroundColor(QColor(245, 245, 245))
    ms.setOutputSize(QSize(1500, 1600))
    ms.setDestinationCrs(crs3857)
    ms.setExtent(extent)

    job = QgsMapRendererParallelJob(ms)
    job.start()
    job.waitForFinished()
    os.makedirs(os.path.dirname(PNG), exist_ok=True)
    job.renderedImage().save(PNG)
    print(f"Rendu PNG ecrit : {PNG}")

    qgs.exitQgis()


if __name__ == "__main__":
    main()
