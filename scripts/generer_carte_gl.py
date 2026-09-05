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
      "galloromain_ay", "galloromain_e", "galloromain_y", "galloromain_an",
      "villa_ville", "prefixe_ville"]),
    ("Germanique & franc", "#008300",
     ["germanique_heim", "germanique_ange", "germanique_dorf", "germanique_bach",
      "flamand", "franc_court"]),
    ("Celtique (breton, gaulois)", "#b76935", ["breton", "gaulois_euil"]),
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
            f'<div class="fam" data-fam="{fi}"><span class="caret">▾</span>'
            f'<input type="checkbox" class="famchk" data-fam="{fi}" checked title="Tout activer/désactiver">'
            f'<span class="s" style="background:{fcol}"></span><b>{fnom}</b>'
            f'<span class="n">{fr(ftot)}&nbsp;· {pct:.0f}%</span></div>'
            f'<div class="fam-body" data-body="{fi}">')
        for m in membres:
            c = par_id[m]
            n = counts.get(m, 0)
            blocs.append(
                f'<label class="l"><input type="checkbox" data-cat="{m}" data-family="{fi}" checked>'
                f'<span class="s sw" data-detail="{coul_detail[m]}" data-fam="{fcol}" '
                f'style="background:{coul_detail[m]}"></span>{c["nom"]}'
                f'<span class="n">{fr(n)}</span></label>')
        blocs.append('</div>')
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
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
  :root{{--bg:rgba(17,18,20,.72);--bd:rgba(255,255,255,.10);--tx:#eef0f2;--tx2:#9ba1a8;--tx3:#6a7077;--acc:#5b9dff}}
  *{{box-sizing:border-box}}
  html,body{{margin:0;height:100%;background:#0d0e10;color:var(--tx);font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
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
  #titre a{{display:inline-block;margin-top:10px;padding:4px 11px;background:rgba(91,157,255,.14);border:1px solid rgba(91,157,255,.32);border-radius:999px;font-size:11.5px}}
  #titre a:hover{{background:rgba(91,157,255,.24);text-decoration:none}}
  .caret{{font-size:9px;color:var(--tx3);width:11px;display:inline-block;transition:transform .2s;flex:0 0 auto}}
  .fam.collapsed .caret{{transform:rotate(-90deg)}}
  .fam-body.hidden{{display:none}}
  .famchk{{accent-color:var(--acc);margin:0 4px 0 0;width:12px;height:12px;flex:0 0 auto}}
  .panel{{animation:pin .5s cubic-bezier(.2,.75,.2,1) both}}
  #legende{{animation-delay:.06s}} #credit{{animation-delay:.12s}}
  @keyframes pin{{from{{opacity:0;transform:translateY(-8px)}}to{{opacity:1;transform:none}}}}
  #credit{{bottom:12px;left:14px;padding:7px 13px;font-size:11px;color:var(--tx3);max-width:360px}}
  #credit a{{color:var(--tx2);text-decoration:none}} #credit a:hover{{color:var(--tx)}}
</style>
</head>
<body>
<div id="map"></div>
<div id="titre" class="panel"><div class="t">Toponymes de France</div><small>préfixes &amp; suffixes des communes — {fr(total)} communes · <a href="lieux-dits.html">→ lieux-dits</a></small></div>
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
<div id="credit" class="panel">Données&nbsp;: <a href="https://www.openstreetmap.org" target="_blank" rel="noopener">OpenStreetMap</a> · IGN — cartographie des préfixes &amp; suffixes toponymiques</div>
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
    h.addEventListener('click',function(e){{
      if(e.target.classList.contains('famchk'))return;
      var fi=h.dataset.fam; h.classList.toggle('collapsed');
      document.querySelector('.fam-body[data-body="'+fi+'"]').classList.toggle('hidden');
    }});
  }});
  document.querySelectorAll('.famchk').forEach(function(c){{
    c.addEventListener('change',function(){{
      var fi=c.dataset.fam;
      document.querySelectorAll('.l input[data-family="'+fi+'"]').forEach(function(i){{i.checked=c.checked}});
      appliquer();
    }});
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
