# Analyse de l'impact des feux de forêt sur l'albédo des glaciers de l'ouest canadien

## Description du projet

Ce projet de maîtrise vise à quantifier l'impact des dépôts de particules issues des feux de forêt sur l'albédo des glaciers de l'ouest canadien en utilisant :
- Le modèle RAQDPS (Regional Air Quality Deterministic Prediction System) d'Environnement Canada
- Les données satellites (MODIS, Sentinel-2)
- Le Randolph Glacier Inventory (RGI)

## Structure du projet

```
.
├── README.md                    # Ce fichier
├── requirements.txt             # Dépendances Python
├── setup.py                     # Configuration du package
├── data/                        # Données (non versionnées)
│   ├── raqdps/                  # Données RAQDPS
│   ├── rgi/                     # Randolph Glacier Inventory
│   ├── modis/                   # Données MODIS
│   └── sentinel2/               # Données Sentinel-2
├── src/                         # Code source principal
│   ├── __init__.py
│   ├── raqdps_glacier_coupling.py      # Couplage général RAQDPS-Glacier
│   ├── rgi_analysis.py                  # Analyse avec RGI
│   ├── athabasca_glacier.py             # Analyse spécifique Athabasca
│   └── utils/                           # Fonctions utilitaires
│       ├── __init__.py
│       ├── data_loaders.py
│       ├── visualization.py
│       └── statistics.py
├── notebooks/                   # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_raqdps_analysis.ipynb
│   └── 03_albedo_correlation.ipynb
├── scripts/                     # Scripts exécutables
│   ├── download_data.sh
│   ├── process_raqdps.py
│   └── generate_reports.py
├── config/                      # Fichiers de configuration
│   ├── config.yaml
│   └── glacier_locations.csv
├── results/                     # Résultats d'analyse
├── figures/                     # Figures générées
└── docs/                        # Documentation
    ├── methodology.md
    ├── data_sources.md
    └── api_reference.md
```

## Installation

1. Cloner le repository
```bash
git clone https://github.com/tofunori/glacier-wildfire-albedo-analysis.git
cd glacier-wildfire-albedo-analysis
```

2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

## Utilisation rapide

### Analyse du glacier Athabasca
```python
from src.athabasca_glacier import AthabascaGlacierAnalysis

# Initialiser l'analyse
analysis = AthabascaGlacierAnalysis(
    raqdps_path="/path/to/raqdps/data",
    output_dir="./results/athabasca"
)

# Analyser une période
df = analysis.analyze_period(
    start_date=datetime(2023, 7, 1),
    end_date=datetime(2023, 8, 31)
)
```

### Analyse régionale avec RGI
```python
from src.rgi_analysis import RGI_RAQDPS_Analysis

# Charger tous les glaciers de l'ouest canadien
analysis = RGI_RAQDPS_Analysis(
    rgi_shapefile="data/rgi/RGI60-02.shp",
    raqdps_path="data/raqdps/",
    region='02'
)

# Filtrer et analyser
analysis.filter_glaciers_by_criteria(min_area=5.0)
summary = analysis.batch_analysis_pipeline(
    start_date, end_date, output_dir="./results"
)
```

## Sources de données

### RAQDPS
- Résolution : 10 km
- Variables clés : BC_dep, PM2.5_dep, PM10_dep
- Fréquence : Horaire
- Accès : Via Datamart d'ECCC

### RGI (Randolph Glacier Inventory)
- Version : RGI 6.0
- Région : 02 (Western Canada and US)
- Download : [GLIMS RGI](https://www.glims.org/RGI/)

### Données satellites
- **MODIS** : MOD10A1 (albédo journalier, 500m)
- **Sentinel-2** : Bandes spectrales pour albédo haute résolution (10-20m)

## Méthodologie

1. **Extraction des dépôts** : Utilisation des champs de dépôt RAQDPS aux coordonnées des glaciers
2. **Calcul cumulatif** : Agrégation temporelle des dépôts (24h, 7j)
3. **Corrélation** : Analyse statistique entre dépôts et changements d'albédo
4. **Validation** : Comparaison avec mesures in-situ et littérature

## Publications et références

- Marshall, S. J. (2014). Glacier response to climate change: Modeling the effects of weather and debris cover. *Quaternary Science Reviews*.
- Ménégoz, M., et al. (2014). Snow cover sensitivity to black carbon deposition in the Himalayas. *Journal of Geophysical Research*.
- Painter, T. H., et al. (2013). End of the Little Ice Age in the Alps forced by industrial black carbon. *PNAS*.

## Contact

- Auteur : [Votre nom]
- Email : [votre.email@universite.ca]
- Superviseur : [Nom du superviseur]
- Institution : [Votre université]

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.