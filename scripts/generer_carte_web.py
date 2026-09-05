#!/usr/bin/env python3
"""Genere une carte web interactive (Leaflet) a partir des communes classees.

- Simplifie les geometries (Douglas-Peucker) pour un poids raisonnable navigateur.
- Ecrit web/communes.js  (var COMMUNES = <geojson compact>)  -> chargeable en file://
- Ecrit web/index.html    (carte + legende + couleurs issues de config)

Ouvrir ensuite web/index.html dans un navigateur (double-clic).
Aucune dependance externe ; Leaflet est charge depuis un CDN a l'affichage.
"""
import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG = os.path.join(BASE, "config", "categories.json")
ENTREE = os.path.join(BASE, "data", "communes_classees.geojson")
WEB = os.path.join(BASE, "web")

TOLERANCE = 0.01   # degres (~1 km) : simplification adaptee a une vue nationale
DECIMALES = 4      # ~11 m de precision


def perp_dist2(p, a, b):
    """Distance perpendiculaire au carre de p au segment a-b (plan lon/lat)."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return (px - cx) ** 2 + (py - cy) ** 2


def douglas_peucker(points, tol):
    """Simplification iterative (evite les depassements de recursion)."""
    n = len(points)
    if n < 3:
        return points
    tol2 = tol * tol
    garder = [False] * n
    garder[0] = garder[-1] = True
    pile = [(0, n - 1)]
    while pile:
        i, j = pile.pop()
        dmax, idx = 0.0, -1
        for k in range(i + 1, j):
            d = perp_dist2(points[k], points[i], points[j])
            if d > dmax:
                dmax, idx = d, k
        if idx != -1 and dmax > tol2:
            garder[idx] = True
            pile.append((i, idx))
            pile.append((idx, j))
    return [p for p, g in zip(points, garder) if g]


def arrondir(points):
    return [[round(x, DECIMALES), round(y, DECIMALES)] for x, y in points]


def simplifier_anneau(anneau):
    s = douglas_peucker(anneau, TOLERANCE)
    if len(s) < 4:          # un polygone ferme a besoin d'au moins 4 sommets
        return None
    if s[0] != s[-1]:       # refermer si besoin
        s.append(s[0])
    return arrondir(s)


def simplifier_geometrie(geom):
    t = geom["type"]
    coords = geom["coordinates"]
    if t == "Polygon":
        anneaux = [a for a in (simplifier_anneau(r) for r in coords) if a]
        if not anneaux:
            return None
        return {"type": "Polygon", "coordinates": anneaux}
    if t == "MultiPolygon":
        polys = []
        for poly in coords:
            anneaux = [a for a in (simplifier_anneau(r) for r in poly) if a]
            if anneaux:
                polys.append(anneaux)
        if not polys:
            return None
        return {"type": "MultiPolygon", "coordinates": polys}
    return None


def main():
    if not os.path.exists(ENTREE):
        raise SystemExit(f"Fichier introuvable : {ENTREE}\nLance d'abord classer_communes.py")

    with open(CONFIG, encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    couleurs = {c["id"]: c["couleur"] for c in cats}

    print("Lecture + simplification ...")
    with open(ENTREE, encoding="utf-8") as f:
        geo = json.load(f)

    sortie_features = []
    for feat in geo["features"]:
        geom = simplifier_geometrie(feat["geometry"])
        if geom is None:
            continue
        p = feat.get("properties", {})
        sortie_features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "nom": p.get("nom", ""),
                "cat": p.get("categorie", "autre"),
                "cn": p.get("categorie_nom", ""),
            },
        })

    fc = {"type": "FeatureCollection", "features": sortie_features}

    os.makedirs(WEB, exist_ok=True)
    js_path = os.path.join(WEB, "communes.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("var COMMUNES = ")
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";")
    taille = os.path.getsize(js_path) // 1024
    print(f"  {len(sortie_features)} communes -> {js_path} ({taille} Ko)")

    # Legende (ordre du fichier de config)
    legende = "".join(
        f'<div class="l"><span class="s" style="background:{c["couleur"]}"></span>{c["nom"]}</div>'
        for c in cats
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toponymes de France</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html,body{{margin:0;height:100%;font-family:system-ui,sans-serif}}
  #map{{position:absolute;inset:0}}
  .panel{{position:absolute;z-index:1000;background:rgba(255,255,255,.95);
    border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.3);padding:10px 12px;font-size:13px}}
  #titre{{top:10px;left:50px;font-weight:600}}
  #legende{{bottom:20px;left:10px;max-height:70%;overflow:auto}}
  .l{{display:flex;align-items:center;margin:2px 0;line-height:1.2}}
  .s{{width:14px;height:14px;border-radius:3px;margin-right:7px;flex:0 0 auto;
    border:1px solid rgba(0,0,0,.2)}}
  .leaflet-popup-content{{font-size:13px}}
</style>
</head>
<body>
<div id="map"></div>
<div id="titre" class="panel">Toponymes de France&nbsp;— préfixes &amp; suffixes des communes</div>
<div id="legende" class="panel">{legende}</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="communes.js"></script>
<script>
  var COULEURS = {json.dumps(couleurs, ensure_ascii=False)};
  var map = L.map('map', {{preferCanvas:true}}).setView([46.6, 2.4], 6);
  L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'&copy; OpenStreetMap', maxZoom:19
  }}).addTo(map);

  function style(f){{
    var c = f.properties.cat;
    return {{
      fillColor: COULEURS[c] || '#e0e0e0',
      fillOpacity: c === 'autre' ? 0.25 : 0.85,
      color: '#ffffff', weight: 0.2
    }};
  }}
  L.geoJSON(COMMUNES, {{
    style: style,
    onEachFeature: function(f, layer){{
      var p = f.properties;
      layer.bindPopup('<b>'+p.nom+'</b><br>'+(p.cn||'—'));
    }}
  }}).addTo(map);
</script>
</body>
</html>"""

    html_path = os.path.join(WEB, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Carte -> {html_path}")
    print("\nOuvrir : open web/index.html")


if __name__ == "__main__":
    main()
