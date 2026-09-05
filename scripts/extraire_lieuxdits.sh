#!/bin/bash
# Extrait les lieux-dits nommes (points OSM place=*) de l'extrait France PBF.
# Utilise le GDAL de QGIS (driver OSM en lecture).
set -e
cd "$(dirname "$0")/.."
source scripts/lieuxdits_env.sh

PBF=data/osm/france-latest.osm.pbf
OUT=data/osm/lieuxdits_raw.geojson
[ -f "$PBF" ] || { echo "PBF manquant : $PBF"; exit 1; }

echo "Extraction des points place=* nommes depuis $PBF ..."
"$OGR2OGR" -f GeoJSON "$OUT" "$PBF" points \
  -where "place IN ('hamlet','isolated_dwelling','farm','locality','village','neighbourhood') AND name IS NOT NULL" \
  -select "name,place" \
  --config OSM_USE_CUSTOM_INDEXING YES \
  --config OGR_INTERLEAVED_READING YES \
  -lco RFC7946=YES -progress

echo "Ecrit : $OUT"
python3 -c "import json;d=json.load(open('$OUT'));print(len(d['features']),'lieux-dits extraits')"
