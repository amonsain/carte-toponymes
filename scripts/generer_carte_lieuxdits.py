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
  :root{{--bg:rgba(17,18,20,.72);--bd:rgba(255,255,255,.10);--tx:#eef0f2;--tx2:#9ba1a8;--tx3:#6a7077;--acc:#5b9dff}}
  *{{box-sizing:border-box}}
  html,body{{margin:0;height:100%;background:#0d0e10;color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
  #map{{position:absolute;inset:0}}
  .panel{{position:absolute;z-index:1;background:var(--bg);color:var(--tx);-webkit-backdrop-filter:blur(18px) saturate(1.4);backdrop-filter:blur(18px) saturate(1.4);border:1px solid var(--bd);border-radius:16px;box-shadow:0 12px 44px rgba(0,0,0,.55)}}
  #titre{{top:14px;left:14px;padding:13px 17px;max-width:290px}}
  #titre .t{{font-size:16.5px;font-weight:650;letter-spacing:-.015em}}
  #titre small{{display:block;margin-top:4px;font-size:12px;color:var(--tx2);line-height:1.5}}
  #titre a{{color:var(--acc);text-decoration:none;font-weight:500}}
  #titre a:hover{{text-decoration:underline}}
  #legende{{top:14px;right:14px;max-height:calc(100% - 28px);overflow-y:auto;padding:12px 7px 14px 15px;width:322px;font-size:13px}}
  #legende::-webkit-scrollbar{{width:9px}}
  #legende::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.13);border-radius:9px;border:2px solid transparent;background-clip:padding-box}}
  .titrebar{{font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:var(--tx3);font-weight:600;margin:15px 8px 7px}}
  .titrebar:first-child{{margin-top:2px}}
  .bar{{display:flex;gap:5px;margin:0 8px 4px}}
  .bar button{{flex:1;padding:6px 4px;font-size:12px;font-weight:500;cursor:pointer;color:var(--tx2);border:1px solid var(--bd);border-radius:9px;background:rgba(255,255,255,.03);transition:.15s}}
  .bar button:hover{{background:rgba(255,255,255,.08);color:var(--tx)}}
  .bar button.on{{background:var(--acc);color:#fff;border-color:transparent;box-shadow:0 2px 10px rgba(91,157,255,.4)}}
  .fam{{display:flex;align-items:center;gap:9px;margin:9px 4px 1px;padding:6px 5px;cursor:pointer;border-radius:8px;border-top:1px solid var(--bd);font-weight:600;font-size:12.5px}}
  .fam:hover{{background:rgba(255,255,255,.05)}}
  .fam b{{flex:1;font-weight:600}}
  .l{{display:flex;align-items:center;margin:1px 0 1px 8px;line-height:1.35;cursor:pointer;padding:3px 6px 3px 5px;border-radius:8px;color:var(--tx)}}
  .l:hover{{background:rgba(255,255,255,.06)}}
  .l input,.chk input{{accent-color:var(--acc);margin-right:9px;width:13px;height:13px}}
  .n{{color:var(--tx3);font-variant-numeric:tabular-nums;font-size:11.5px;margin-left:auto;padding-left:10px}}
  .s{{width:12px;height:12px;border-radius:50%;margin-right:10px;flex:0 0 auto;box-shadow:0 0 0 1px rgba(255,255,255,.28)}}
  .fam .s{{width:13px;height:13px;border-radius:4px}}
  .chk{{display:flex;align-items:center;margin:7px 8px;font-size:12.5px;cursor:pointer;color:var(--tx2)}}
  .maplibregl-popup-content{{font-size:13px;background:#191a1d;color:#eef0f2;border-radius:11px;padding:10px 14px;box-shadow:0 10px 34px rgba(0,0,0,.55)}}
  .maplibregl-popup-content b{{color:#fff}}
  .maplibregl-popup-tip{{border-top-color:#191a1d!important;border-bottom-color:#191a1d!important}}
  .maplibregl-ctrl-group{{background:var(--bg)!important;border:1px solid var(--bd)!important;box-shadow:0 6px 20px rgba(0,0,0,.5)!important}}
  .maplibregl-ctrl-group button{{filter:invert(1) hue-rotate(180deg)}}
</style>
</head>
<body>
<div id="map"></div>
<div id="titre" class="panel"><div class="t">Lieux-dits de France</div><small>{fr(affiche)} lieux-dits typés / {fr(total)} au total — <a href="index.html">↩ carte des communes</a></small></div>
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
            'circle-radius':['interpolate',['linear'],['zoom'],4,0.75,7,1.8,10,3.3,13,6],
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
