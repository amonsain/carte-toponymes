#!/usr/bin/env python3
"""Genere une carte interactive performante (MapLibre GL, rendu GPU).

- Filtrage instantane par categorie (cases a cocher), rendu GPU.
- Legende groupee par FAMILLE (en-tetes cliquables) avec COMPTEURS (nb + %).
- Bascule couleur : Detail (24 suffixes) / Familles (8 couleurs, safe daltonisme).
- Fonds neutres (sombre / gris / OSM) selectionnables.
- FRONTIERE linguistique oil / oc activable.

Reutilise web/communes.js (var COMMUNES). Sortie : web/carte_gl.html.
"""
import json
import os
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG = os.path.join(BASE, "config", "categories.json")
CLASSEES = os.path.join(BASE, "data", "communes_classees.geojson")
WEB = os.path.join(BASE, "web")
SORTIE = os.path.join(WEB, "carte_gl.html")

ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas"
ATTR_ESRI = "&copy; Esri, HERE, Garmin"

# Familles (nom, couleur validee fond sombre, membres). Ordre = affichage.
FAMILLES = [
    ("Religieux", "#9085e9", ["religieux"]),
    ("Gallo-romain & latin", "#e66767",
     ["galloromain_gnac", "galloromain_ac", "occitan_argues", "galloromain_ieu",
      "galloromain_y", "galloromain_an", "villa_ville"]),
    ("Germanique & franc", "#008300",
     ["germanique_heim", "germanique_ange", "germanique_dorf", "franc_court"]),
    ("Normand (norrois)", "#199e70", ["norrois_eur", "suffixe_uit", "mesnil"]),
    ("Eau & locatifs", "#3987e5",
     ["cotier", "riverain", "complement_les", "complement_en"]),
    ("Savoyard (alpin)", "#d55181", ["savoyard_alpin"]),
    ("Paysage (relief, vallée, bourg)", "#c98500", ["mont", "val", "bourg"]),
    ("Divers", "#d95926", ["suffixe_ou"]),
    ("Autre", "#8a8a8a", ["autre"]),
]

# Ligne approximative de partage oil / oc (ouest -> est), lon/lat.
OILOC = [[-1.05, 45.55], [-0.2, 45.7], [0.6, 45.75], [1.3, 45.9], [2.0, 46.0],
         [2.6, 45.85], [3.2, 45.7], [3.8, 45.55], [4.4, 45.45], [5.2, 45.35],
         [6.0, 45.3], [6.9, 45.25]]


def fr(n):
    return format(n, ",").replace(",", " ")  # espace fine insecable


def main():
    cats = json.load(open(CONFIG, encoding="utf-8"))["categories"]
    par_id = {c["id"]: c for c in cats}
    coul_detail = {c["id"]: c["couleur"] for c in cats}

    counts = Counter(
        f["properties"].get("categorie", "autre")
        for f in json.load(open(CLASSEES, encoding="utf-8"))["features"])
    total = sum(counts.values())

    # Expressions de couleur MapLibre
    match_detail = ["match", ["get", "cat"]]
    match_fam = ["match", ["get", "cat"]]
    coul_fam = {}
    for _nom, fcol, membres in FAMILLES:
        for m in membres:
            coul_fam[m] = fcol
    for c in cats:
        if c["type"] == "defaut":
            continue
        match_detail += [c["id"], c["couleur"]]
        match_fam += [c["id"], coul_fam.get(c["id"], "#8a8a8a")]
    match_detail.append(coul_detail.get("autre", "#e0e0e0"))
    match_fam.append("#8a8a8a")

    # Legende groupee par famille
    blocs = []
    for fi, (fnom, fcol, membres) in enumerate(FAMILLES):
        ftot = sum(counts.get(m, 0) for m in membres)
        pct = ftot * 100 / total if total else 0
        blocs.append(
            f'<div class="fam" data-fam="{fi}" title="Tout activer/desactiver dans la famille">'
            f'<span class="s" style="background:{fcol}"></span><b>{fnom}</b>'
            f'<span class="n">{fr(ftot)}&nbsp;· {pct:.0f}%</span></div>')
        for m in membres:
            c = par_id[m]
            n = counts.get(m, 0)
            blocs.append(
                f'<label class="l"><input type="checkbox" data-cat="{m}" data-family="{fi}" checked>'
                f'<span class="s sw" data-detail="{coul_detail[m]}" data-fam="{fcol}" '
                f'style="background:{coul_detail[m]}"></span>{c["nom"]}'
                f'<span class="n">{fr(n)}</span></label>')
    legende = "".join(blocs)

    oiloc_geo = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {},
         "geometry": {"type": "LineString", "coordinates": OILOC}}]}

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toponymes de France — carte GL</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  html,body{{margin:0;height:100%;font-family:system-ui,sans-serif;background:#111}}
  #map{{position:absolute;inset:0}}
  .panel{{position:absolute;z-index:1;background:rgba(255,255,255,.96);
    border-radius:8px;box-shadow:0 1px 8px rgba(0,0,0,.4)}}
  #titre{{top:10px;left:10px;padding:8px 12px;font-weight:600}}
  #titre small{{display:block;font-weight:400;color:#666}}
  #legende{{top:10px;right:10px;max-height:calc(100% - 20px);overflow:auto;
    padding:8px 10px;width:355px;font-size:13px}}
  .bar{{display:flex;gap:6px;margin-bottom:6px}}
  .bar button{{flex:1;padding:4px;font-size:12px;cursor:pointer;
    border:1px solid #ccc;border-radius:5px;background:#f7f7f7}}
  .bar button.on{{background:#333;color:#fff;border-color:#333}}
  .titrebar{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;
    color:#888;margin:8px 0 3px}}
  .fam{{display:flex;align-items:center;margin:7px 0 2px;cursor:pointer;
    border-top:1px solid #eee;padding-top:5px}}
  .fam b{{flex:1}}
  .l{{display:flex;align-items:center;margin:1px 0 1px 6px;line-height:1.3;
    cursor:pointer;padding:1px 3px;border-radius:4px}}
  .l:hover{{background:#f0f0f0}}
  .l input{{margin-right:6px}}
  .n{{color:#999;font-variant-numeric:tabular-nums;font-size:12px;margin-left:auto;
    padding-left:8px}}
  .s{{width:14px;height:14px;border-radius:3px;margin-right:7px;flex:0 0 auto;
    border:1px solid rgba(0,0,0,.2)}}
  .chk{{display:flex;align-items:center;gap:6px;margin:4px 0;font-size:13px;cursor:pointer}}
  .maplibregl-popup-content{{font-size:13px}}
</style>
</head>
<body>
<div id="map"></div>
<div id="titre" class="panel">Toponymes de France<small>préfixes &amp; suffixes des communes — {fr(total)} communes</small></div>
<div id="legende" class="panel">
  <div class="titrebar">Fond de carte</div>
  <div class="bar" id="fonds">
    <button data-bg="sombre" class="on">Sombre</button>
    <button data-bg="gris">Gris</button>
    <button data-bg="osm">OSM</button>
  </div>
  <div class="titrebar">Couleur</div>
  <div class="bar" id="modes">
    <button data-mode="detail" class="on">24 suffixes</button>
    <button data-mode="fam">8 familles</button>
  </div>
  <label class="chk"><input type="checkbox" id="frontiere"> Frontière oïl / oc (approx.)</label>
  <div class="titrebar">Familles &amp; suffixes <span style="text-transform:none;color:#bbb">(clic sur une famille = tout cocher/décocher)</span></div>
  <div class="bar"><button id="tout">Tout</button><button id="rien">Aucun</button></div>
  {legende}
</div>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="communes.js"></script>
<script>
  var C_DETAIL = {json.dumps(match_detail, ensure_ascii=False)};
  var C_FAM = {json.dumps(match_fam, ensure_ascii=False)};
  var OILOC = {json.dumps(oiloc_geo, ensure_ascii=False)};
  var mode = 'detail';

  var map = new maplibregl.Map({{
    container: 'map', center: [2.4, 46.6], zoom: 5,
    style: {{
      version: 8,
      sources: {{
        sombre: {{ type:'raster', tileSize:256, attribution:'{ATTR_ESRI}',
          tiles:['{ESRI}/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}'] }},
        gris: {{ type:'raster', tileSize:256, attribution:'{ATTR_ESRI}',
          tiles:['{ESRI}/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}'] }},
        osm: {{ type:'raster', tileSize:256, attribution:'&copy; OpenStreetMap',
          tiles:['https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'] }},
        communes: {{ type:'geojson', data: COMMUNES }},
        oiloc: {{ type:'geojson', data: OILOC }}
      }},
      layers: [
        {{ id:'fond', type:'background', paint:{{'background-color':'#1a1a1a'}} }},
        {{ id:'bg-sombre', type:'raster', source:'sombre' }},
        {{ id:'bg-gris', type:'raster', source:'gris', layout:{{visibility:'none'}} }},
        {{ id:'bg-osm', type:'raster', source:'osm', layout:{{visibility:'none'}} }},
        {{ id:'communes-fill', type:'fill', source:'communes',
          paint: {{ 'fill-color': C_DETAIL,
            'fill-opacity': ['case', ['==', ['get','cat'], 'autre'], 0.10, 0.88] }} }},
        {{ id:'communes-line', type:'line', source:'communes',
          paint: {{ 'line-color':'#ffffff', 'line-width':0.12, 'line-opacity':0.35 }} }},
        {{ id:'oiloc', type:'line', source:'oiloc', layout:{{visibility:'none'}},
          paint: {{ 'line-color':'#ffe100', 'line-width':2.5, 'line-dasharray':[2,1.5],
            'line-opacity':0.9 }} }}
      ]
    }}
  }});
  map.addControl(new maplibregl.NavigationControl(), 'bottom-right');

  document.querySelectorAll('#fonds button').forEach(function(b){{
    b.onclick=function(){{
      document.querySelectorAll('#fonds button').forEach(function(x){{x.classList.remove('on')}});
      b.classList.add('on'); var k=b.dataset.bg;
      ['sombre','gris','osm'].forEach(function(x){{
        map.setLayoutProperty('bg-'+x,'visibility', x===k?'visible':'none'); }});
      document.body.style.background=(k==='sombre')?'#111':'#eee';
    }};
  }});

  // Bascule Detail / Familles
  document.querySelectorAll('#modes button').forEach(function(b){{
    b.onclick=function(){{
      document.querySelectorAll('#modes button').forEach(function(x){{x.classList.remove('on')}});
      b.classList.add('on'); mode=b.dataset.mode;
      map.setPaintProperty('communes-fill','fill-color', mode==='fam'?C_FAM:C_DETAIL);
      document.querySelectorAll('.sw').forEach(function(sw){{
        sw.style.background = mode==='fam'? sw.dataset.fam : sw.dataset.detail; }});
    }};
  }});

  // Frontiere
  document.getElementById('frontiere').onchange=function(){{
    map.setLayoutProperty('oiloc','visibility', this.checked?'visible':'none');
  }};

  // Filtrage
  function actives(){{
    return Array.from(document.querySelectorAll('.l input:checked')).map(function(i){{return i.dataset.cat}});
  }}
  function appliquer(){{
    var f=['in',['get','cat'],['literal',actives()]];
    map.setFilter('communes-fill',f); map.setFilter('communes-line',f);
  }}
  document.querySelectorAll('.l input').forEach(function(i){{ i.addEventListener('change',appliquer); }});
  document.querySelectorAll('.fam').forEach(function(h){{
    h.onclick=function(){{
      var fi=h.dataset.fam;
      var membres=Array.from(document.querySelectorAll('.l input[data-family="'+fi+'"]'));
      var cible=!membres.every(function(i){{return i.checked}});
      membres.forEach(function(i){{i.checked=cible}}); appliquer();
    }};
  }});
  document.getElementById('tout').onclick=function(){{
    document.querySelectorAll('.l input').forEach(function(i){{i.checked=true}}); appliquer(); }};
  document.getElementById('rien').onclick=function(){{
    document.querySelectorAll('.l input').forEach(function(i){{i.checked=false}}); appliquer(); }};

  map.on('click','communes-fill', function(e){{
    var p=e.features[0].properties;
    new maplibregl.Popup().setLngLat(e.lngLat).setHTML('<b>'+p.nom+'</b><br>'+(p.cn||'—')).addTo(map);
  }});
  map.on('mouseenter','communes-fill', function(){{ map.getCanvas().style.cursor='pointer'; }});
  map.on('mouseleave','communes-fill', function(){{ map.getCanvas().style.cursor=''; }});
  map.on('load', appliquer);
</script>
</body>
</html>"""

    os.makedirs(WEB, exist_ok=True)
    open(SORTIE, "w", encoding="utf-8").write(html)
    print(f"Carte GL ecrite : {SORTIE}  ({len(FAMILLES)} familles, {total} communes)")


if __name__ == "__main__":
    main()
