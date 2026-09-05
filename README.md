# Carte des toponymes de France

Colorer les communes de France selon les **préfixes et suffixes** de leur nom,
pour visualiser les grandes strates linguistiques et historiques du peuplement :
domaines gallo-romains (`-ac`, `-y`), villages francs (`-court`, `-ville`),
implantations germaniques (`-heim`, `-ange`), hagiotoponymes (`Saint-`)…

Le projet produit un fichier GeoJSON prêt à ouvrir dans **QGIS**, accompagné
d'un style `.qml` qui applique automatiquement les couleurs.

## Aperçu de la démarche

1. Télécharger les ~35 000 communes de France (contours + noms).
2. Classer chaque commune selon des règles toponymiques (regex de préfixes/suffixes).
3. Générer un style QGIS coloré, cohérent avec les règles.
4. Ouvrir dans QGIS et admirer la carte.

## Prérequis

- **Python 3** (bibliothèque standard uniquement, aucune installation).
- **QGIS 3.x** (testé pour le format de style 3.34, compatible 3.22+).

## Utilisation

Depuis le dossier du projet :

```bash
# 1. Télécharger les communes (~90 Mo, une seule fois)
python3 scripts/telecharger_communes.py

# 2. Classer les communes -> data/communes_classees.geojson
python3 scripts/classer_communes.py

# 3. (déjà généré) Régénérer le style si vous modifiez les couleurs
python3 scripts/generer_style_qgis.py
```

## Dans QGIS

1. **Couche ▸ Ajouter une couche ▸ Ajouter une couche vecteur…** et choisir
   `data/communes_classees.geojson`.
2. Clic droit sur la couche ▸ **Propriétés ▸ Symbologie ▸ Style (en bas) ▸
   Charger le style…** et sélectionner `styles/communes.qml`.
3. La carte se colore selon le champ `categorie`. La légende reprend les libellés.

Astuce : ajoutez un fond de carte clair (**OpenStreetMap** via le panneau
*Explorateur ▸ XYZ Tiles*) sous la couche pour situer les motifs régionaux.

## Personnaliser les catégories

Tout est piloté par un seul fichier : [`config/categories.json`](config/categories.json).

Chaque catégorie a :

- `nom` : libellé affiché dans la légende ;
- `couleur` : code hexadécimal ;
- `type` : `prefixe` (testé sur le nom entier), `suffixe` (testé sur le radical)
  ou `defaut` (fourre-tout) ;
- `motif` : une expression régulière Python (minuscules, accents conservés).

**L'ordre compte** : la première règle qui correspond l'emporte. Placez les cas
les plus spécifiques en haut.

Après modification, relancez `classer_communes.py` **et** `generer_style_qgis.py`.

## Comment se fait le classement

- Le **préfixe** est cherché sur le nom complet (ex. `Saint-Georges-sur-Loire`).
- Le **suffixe** est cherché sur le *radical* : le premier mot significatif du nom,
  en ignorant les mots de liaison (`sur`, `en`, `lès`, `le`, `de`…).
  Ainsi `Neuilly-sur-Seine` est analysé sur `Neuilly` → suffixe `-y`, et non `Seine`.

Quelques exemples réels :

| Commune                   | Catégorie                          |
|---------------------------|------------------------------------|
| Bergerac, Cognac          | `-ac` (gallo-romain, Sud)          |
| Neuilly-sur-Seine, Vitré  | `-y / -ay / -é` (gallo-romain, Nord)|
| Abbeville                 | `-ville`                           |
| Azincourt                 | `-court`                           |
| Molsheim, Guebwiller      | germanique `-heim / -willer`       |
| Hayange                   | germanique `-ange`                 |
| Strasbourg                | `-bourg`                           |
| Saint-Georges-sur-Loire   | hagiotoponyme `Saint-`             |

## Limites connues

- L'analyse est purement graphique (motif du nom), pas étymologique : quelques
  faux positifs sont inévitables (un nom peut finir en `-y` sans venir de `-acum`).
- Le radical retenu est le premier mot ; les toponymes composés rares peuvent
  être mal découpés.
- Ajustez librement les règles dans `config/categories.json` selon vos besoins.

## Sources des données

Contours communaux : dépôt
[france-geojson](https://github.com/gregoiredavid/france-geojson) (Grégoire David),
dérivé des données IGN Admin Express / INSEE (domaine public).

## Structure

```
france-toponymes-carte/
├── config/
│   └── categories.json          # règles + couleurs (source de vérité)
├── scripts/
│   ├── telecharger_communes.py  # récupère les communes
│   ├── classer_communes.py      # ajoute le champ 'categorie'
│   └── generer_style_qgis.py    # produit le .qml
├── styles/
│   └── communes.qml             # style QGIS catégorisé
└── data/                        # fichiers téléchargés/générés (git-ignorés)
```
