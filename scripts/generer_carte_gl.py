#!/usr/bin/env python3
"""Genere une carte interactive performante (MapLibre GL, rendu GPU).

Filtrage instantane par categorie (cases a cochees), fond OpenStreetMap.
Reutilise web/communes.js (var COMMUNES = <geojson>) deja produit par
generer_carte_web.py.

Sortie : web/carte_gl.html  (double-clic, autonome ; MapLibre via CDN).
"""
import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG = os.path.join(BASE, "config", "categories.json")
WEB = os.path.join(BASE, "web")
SORTIE = os.path.join(WEB, "carte_gl.html")


def main():
    with open(CONFIG, encoding="utf-8") as f:
        cats = json.load(f)["categories"]

    couleurs = {c["id"]: c["couleur"] for c in cats}

    # Expression MapLibre 'match' pour la couleur de remplissage
    match = ["match", ["get", "cat"]]
    for c in cats:
        if c["type"] == "defaut":
            continue
        match += [c["id"], c["couleur"]]
    match.append(couleurs.get("autre", "#e0e0e0"))  # defaut

    # Legende (cases a cocher)
    lignes = "".join(
        f'<label class="l"><input type="checkbox" data-cat="{c["id"]}" checked>'
        f'<span class="s" style="background:{c["couleur"]}"></span>{c["nom"]}</label>'
        for c in cats
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toponymes de France — carte GL</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  html,body{{margin:0;height:100%;font-family:system-ui,sans-serif}}
  #map{{position:absolute;inset:0}}
  .panel{{position:absolute;z-index:1;background:rgba(255,255,255,.96);
    border-radius:8px;box-shadow:0 1px 8px rgba(0,0,0,.3)}}
  #titre{{top:10px;left:10px;padding:8px 12px;font-weight:600}}
  #titre small{{display:block;font-weight:400;color:#666}}
  #legende{{top:10px;right:10px;max-height:calc(100% - 20px);overflow:auto;
    padding:8px 10px;width:330px;font-size:13px}}
  #legende .bar{{display:flex;gap:6px;margin-bottom:6px}}
  #legende button{{flex:1;padding:4px;font-size:12px;cursor:pointer;
    border:1px solid #ccc;border-radius:5px;background:#f7f7f7}}
  .l{{display:flex;align-items:center;margin:1px 0;line-height:1.35;cursor:pointer;
    padding:2px 3px;border-radius:4px}}
  .l:hover{{background:#f0f0f0}}
  .l input{{margin-right:6px}}
  .s{{width:14px;height:14px;border-radius:3px;margin-right:7px;flex:0 0 auto;
    border:1px solid rgba(0,0,0,.2)}}
  .maplibregl-popup-content{{font-size:13px}}
</style>
</head>
<body>
<div id="map"></div>
<div id="titre" class="panel">Toponymes de France<small>préfixes &amp; suffixes des communes</small></div>
<div id="legende" class="panel">
  <div class="bar"><button id="tout">Tout</button><button id="rien">Aucun</button></div>
  {lignes}
</div>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="communes.js"></script>
<script>
  var COULEUR = {json.dumps(match, ensure_ascii=False)};
  var map = new maplibregl.Map({{
    container: 'map',
    center: [2.4, 46.6], zoom: 5,
    style: {{
      version: 8,
      sources: {{
        osm: {{ type:'raster', tileSize:256,
          tiles:['https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'],
          attribution:'&copy; OpenStreetMap' }},
        communes: {{ type:'geojson', data: COMMUNES }}
      }},
      layers: [
        {{ id:'osm', type:'raster', source:'osm' }},
        {{ id:'communes-fill', type:'fill', source:'communes',
          paint: {{
            'fill-color': COULEUR,
            'fill-opacity': ['case', ['==', ['get','cat'], 'autre'], 0.12, 0.82]
          }} }},
        {{ id:'communes-line', type:'line', source:'communes',
          paint: {{ 'line-color':'#ffffff', 'line-width':0.15 }} }}
      ]
    }}
  }});
  map.addControl(new maplibregl.NavigationControl(), 'bottom-right');

  // Filtrage instantane (GPU) selon les cases cochees
  function actives(){{
    return Array.from(document.querySelectorAll('#legende input:checked'))
      .map(function(i){{return i.dataset.cat}});
  }}
  function appliquer(){{
    var f = ['in', ['get','cat'], ['literal', actives()]];
    map.setFilter('communes-fill', f);
    map.setFilter('communes-line', f);
  }}
  document.querySelectorAll('#legende input').forEach(function(i){{
    i.addEventListener('change', appliquer);
  }});
  document.getElementById('tout').onclick = function(){{
    document.querySelectorAll('#legende input').forEach(function(i){{i.checked=true}});
    appliquer();
  }};
  document.getElementById('rien').onclick = function(){{
    document.querySelectorAll('#legende input').forEach(function(i){{i.checked=false}});
    appliquer();
  }};

  // Popup au clic
  map.on('click','communes-fill', function(e){{
    var p = e.features[0].properties;
    new maplibregl.Popup().setLngLat(e.lngLat)
      .setHTML('<b>'+p.nom+'</b><br>'+(p.cn||'—')).addTo(map);
  }});
  map.on('mouseenter','communes-fill', function(){{ map.getCanvas().style.cursor='pointer'; }});
  map.on('mouseleave','communes-fill', function(){{ map.getCanvas().style.cursor=''; }});
  map.on('load', appliquer);
</script>
</body>
</html>"""

    os.makedirs(WEB, exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Carte GL ecrite : {SORTIE}")
    if not os.path.exists(os.path.join(WEB, "communes.js")):
        print("ATTENTION : web/communes.js manquant -> lance generer_carte_web.py")


if __name__ == "__main__":
    main()
