#!/usr/bin/env python3
"""Genere la carte web des LIEUX-DITS (points), tuiles vectorielles PMTiles.

Carte separee de celle des communes. Reutilise les couleurs/familles/regles.
Sortie : docs/lieux-dits.html  (charge docs/lieuxdits.pmtiles).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generer_carte_gl import FAMILLES, fr, ESRI, ATTR_ESRI, OILOC  # noqa: E402

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG = os.path.join(BASE, "config", "categories.json")
COMPTE = os.path.join(BASE, "data", "osm", "lieuxdits_compte.json")
SORTIE = os.path.join(BASE, "docs", "lieux-dits.html")


def main():
    cats = json.load(open(CONFIG, encoding="utf-8"))["categories"]
    par_id = {c["id"]: c for c in cats}
    coul_detail = {c["id"]: c["couleur"] for c in cats}
    counts = json.load(open(COMPTE, encoding="utf-8")) if os.path.exists(COMPTE) else {}
    counts = {k: int(v) for k, v in counts.items()}
    total = sum(counts.values()) or 1
    affiche = total - counts.get("autre", 0)  # 'Autre' n'est pas dans les tuiles

    coul_fam = {m: fcol for _n, fcol, membres in FAMILLES for m in membres}
    match_detail = ["match", ["get", "cat"]]
    match_fam = ["match", ["get", "cat"]]
    for c in cats:
        if c["type"] == "defaut":
            continue
        match_detail += [c["id"], c["couleur"]]
        match_fam += [c["id"], coul_fam.get(c["id"], "#8a8a8a")]
    match_detail.append(coul_detail.get("autre", "#e0e0e0"))
    match_fam.append("#8a8a8a")

    blocs = []
    for fi, (fnom, fcol, membres) in enumerate(FAMILLES):
        if fnom == "Autre":
            continue  # non affiche sur la carte des lieux-dits
        ftot = sum(counts.get(m, 0) for m in membres)
        blocs.append(
            f'<div class="fam" data-fam="{fi}" title="Tout activer/desactiver">'
            f'<span class="s" style="background:{fcol}"></span><b>{fnom}</b>'
            f'<span class="n">{fr(ftot)}&nbsp;· {ftot*100/total:.0f}%</span></div>')
        for m in membres:
            c = par_id[m]
            blocs.append(
                f'<label class="l"><input type="checkbox" data-cat="{m}" data-family="{fi}" checked>'
                f'<span class="s sw" data-detail="{coul_detail[m]}" data-fam="{fcol}" '
                f'style="background:{coul_detail[m]}"></span>{c["nom"]}'
                f'<span class="n">{fr(counts.get(m,0))}</span></label>')
    legende = "".join(blocs)

    oiloc_geo = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {},
         "geometry": {"type": "LineString", "coordinates": OILOC}}]}

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lieux-dits de France — toponymes</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  html,body{{margin:0;height:100%;font-family:system-ui,sans-serif;background:#111}}
  #map{{position:absolute;inset:0}}
  .panel{{position:absolute;z-index:1;background:rgba(255,255,255,.96);border-radius:8px;
    box-shadow:0 1px 8px rgba(0,0,0,.4)}}
  #titre{{top:10px;left:10px;padding:8px 12px;font-weight:600}}
  #titre small{{display:block;font-weight:400;color:#666}}
  #titre a{{color:#2171b5;text-decoration:none;font-size:12px}}
  #legende{{top:10px;right:10px;max-height:calc(100% - 20px);overflow:auto;padding:8px 10px;
    width:355px;font-size:13px}}
  .bar{{display:flex;gap:6px;margin-bottom:6px}}
  .bar button{{flex:1;padding:4px;font-size:12px;cursor:pointer;border:1px solid #ccc;
    border-radius:5px;background:#f7f7f7}}
  .bar button.on{{background:#333;color:#fff;border-color:#333}}
  .titrebar{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#888;margin:8px 0 3px}}
  .fam{{display:flex;align-items:center;margin:7px 0 2px;cursor:pointer;border-top:1px solid #eee;padding-top:5px}}
  .fam b{{flex:1}}
  .l{{display:flex;align-items:center;margin:1px 0 1px 6px;line-height:1.3;cursor:pointer;padding:1px 3px;border-radius:4px}}
  .l:hover{{background:#f0f0f0}} .l input{{margin-right:6px}}
  .n{{color:#999;font-variant-numeric:tabular-nums;font-size:12px;margin-left:auto;padding-left:8px}}
  .s{{width:14px;height:14px;border-radius:3px;margin-right:7px;flex:0 0 auto;border:1px solid rgba(0,0,0,.2)}}
  .chk{{display:flex;align-items:center;gap:6px;margin:4px 0;font-size:13px;cursor:pointer}}
  .maplibregl-popup-content{{font-size:13px}}
</style>
</head>
<body>
<div id="map"></div>
<div id="titre" class="panel">Lieux-dits de France<small>{fr(affiche)} lieux-dits typés / {fr(total)} au total — <a href="index.html">↩ carte des communes</a></small></div>
<div id="legende" class="panel">
  <div class="titrebar">Fond de carte</div>
  <div class="bar" id="fonds">
    <button data-bg="sombre" class="on">Sombre</button><button data-bg="gris">Gris</button><button data-bg="osm">OSM</button>
  </div>
  <div class="titrebar">Couleur</div>
  <div class="bar" id="modes"><button data-mode="detail" class="on">Détail</button><button data-mode="fam">Familles</button></div>
  <label class="chk"><input type="checkbox" id="frontiere"> Frontière oïl / oc (approx.)</label>
  <div class="titrebar">Familles &amp; suffixes <span style="text-transform:none;color:#bbb">(clic famille = tout)</span></div>
  <div class="bar"><button id="tout">Tout</button><button id="rien">Aucun</button></div>
  {legende}
</div>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/pmtiles@3.0.6/dist/pmtiles.js"></script>
<script>
  var C_DETAIL = {json.dumps(match_detail, ensure_ascii=False)};
  var C_FAM = {json.dumps(match_fam, ensure_ascii=False)};
  var OILOC = {json.dumps(oiloc_geo, ensure_ascii=False)};
  var proto = new pmtiles.Protocol();
  maplibregl.addProtocol('pmtiles', proto.tile);

  var map = new maplibregl.Map({{
    container:'map', center:[2.4,46.6], zoom:5,
    style:{{ version:8,
      sources:{{
        sombre:{{type:'raster',tileSize:256,attribution:'{ATTR_ESRI}',tiles:['{ESRI}/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}']}},
        gris:{{type:'raster',tileSize:256,attribution:'{ATTR_ESRI}',tiles:['{ESRI}/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}']}},
        osm:{{type:'raster',tileSize:256,attribution:'&copy; OpenStreetMap',tiles:['https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png']}},
        lieuxdits:{{type:'vector',url:'pmtiles://lieuxdits.pmtiles'}},
        oiloc:{{type:'geojson',data:OILOC}}
      }},
      layers:[
        {{id:'fond',type:'background',paint:{{'background-color':'#1a1a1a'}}}},
        {{id:'bg-sombre',type:'raster',source:'sombre'}},
        {{id:'bg-gris',type:'raster',source:'gris',layout:{{visibility:'none'}}}},
        {{id:'bg-osm',type:'raster',source:'osm',layout:{{visibility:'none'}}}},
        {{id:'ld',type:'circle',source:'lieuxdits','source-layer':'lieuxdits',
          paint:{{'circle-color':C_DETAIL,
            'circle-radius':['interpolate',['linear'],['zoom'],4,1,7,2.4,10,4.4,13,8],
            'circle-opacity':0.85,'circle-stroke-width':0}}}},
        {{id:'oiloc',type:'line',source:'oiloc',layout:{{visibility:'none'}},
          paint:{{'line-color':'#ffe100','line-width':2.5,'line-dasharray':[2,1.5],'line-opacity':0.9}}}}
      ]
    }}
  }});
  map.addControl(new maplibregl.NavigationControl(),'bottom-right');

  document.querySelectorAll('#fonds button').forEach(function(b){{b.onclick=function(){{
    document.querySelectorAll('#fonds button').forEach(function(x){{x.classList.remove('on')}});b.classList.add('on');
    var k=b.dataset.bg;['sombre','gris','osm'].forEach(function(x){{map.setLayoutProperty('bg-'+x,'visibility',x===k?'visible':'none')}});
    document.body.style.background=(k==='sombre')?'#111':'#eee';}};}});

  var mode='detail';
  document.querySelectorAll('#modes button').forEach(function(b){{b.onclick=function(){{
    document.querySelectorAll('#modes button').forEach(function(x){{x.classList.remove('on')}});b.classList.add('on');mode=b.dataset.mode;
    map.setPaintProperty('ld','circle-color',mode==='fam'?C_FAM:C_DETAIL);
    document.querySelectorAll('.sw').forEach(function(sw){{sw.style.background=mode==='fam'?sw.dataset.fam:sw.dataset.detail}});}};}});

  document.getElementById('frontiere').onchange=function(){{map.setLayoutProperty('oiloc','visibility',this.checked?'visible':'none')}};

  function actives(){{return Array.from(document.querySelectorAll('.l input:checked')).map(function(i){{return i.dataset.cat}})}}
  function appliquer(){{map.setFilter('ld',['in',['get','cat'],['literal',actives()]])}}
  document.querySelectorAll('.l input').forEach(function(i){{i.addEventListener('change',appliquer)}});
  document.querySelectorAll('.fam').forEach(function(h){{h.onclick=function(){{
    var fi=h.dataset.fam;var m=Array.from(document.querySelectorAll('.l input[data-family="'+fi+'"]'));
    var t=!m.every(function(i){{return i.checked}});m.forEach(function(i){{i.checked=t}});appliquer();}};}});
  document.getElementById('tout').onclick=function(){{document.querySelectorAll('.l input').forEach(function(i){{i.checked=true}});appliquer()}};
  document.getElementById('rien').onclick=function(){{document.querySelectorAll('.l input').forEach(function(i){{i.checked=false}});appliquer()}};

  map.on('click','ld',function(e){{var p=e.features[0].properties;
    new maplibregl.Popup().setLngLat(e.lngLat).setHTML('<b>'+p.nom+'</b><br>'+(p.cn||'—')).addTo(map);}});
  map.on('mouseenter','ld',function(){{map.getCanvas().style.cursor='pointer'}});
  map.on('mouseleave','ld',function(){{map.getCanvas().style.cursor=''}});
  map.on('load',appliquer);
</script>
</body>
</html>"""

    open(SORTIE, "w", encoding="utf-8").write(html)
    print(f"Ecrit : {SORTIE}  ({fr(total)} lieux-dits)")


if __name__ == "__main__":
    main()
