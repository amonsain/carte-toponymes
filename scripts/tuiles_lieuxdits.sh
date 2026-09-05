#!/bin/bash
# Genere les tuiles vectorielles PMTiles des lieux-dits (via GDAL de QGIS + pmtiles).
set -e
cd "$(dirname "$0")/.."
source scripts/lieuxdits_env.sh

IN=data/osm/lieuxdits_classes.geojson
MBT=data/osm/lieuxdits.mbtiles
PM=docs/lieuxdits.pmtiles

[ -f "$IN" ] || { echo "manque $IN"; exit 1; }
rm -f "$MBT" "$PM"

echo "1/2 GeoJSON -> MBTiles (MVT, z4-13 ; 'Autre' exclu) ..."
"$OGR2OGR" -f MBTiles "$MBT" "$IN" \
  -where "cat <> 'autre'" \
  -dsco MINZOOM=4 -dsco MAXZOOM=13 -dsco MAX_SIZE=3000000 \
  -nln lieuxdits

echo "2/2 MBTiles -> PMTiles ..."
python3 -c "from pmtiles.convert import mbtiles_to_pmtiles; mbtiles_to_pmtiles('$MBT','$PM',13)"

echo "OK : $PM ($(ls -lh "$PM" | awk '{print $5}'))"
