# Référence API

## Module principal : `src`

### `RAQDPSGlacierAnalysis`

Classe principale pour l'analyse des dépôts RAQDPS sur les glaciers.

#### Constructeur
```python
RAQDPSGlacierAnalysis(raqdps_path, glacier_shapefile, albedo_data_path)
```

**Paramètres:**
- `raqdps_path` (str): Chemin vers les fichiers RAQDPS NetCDF
- `glacier_shapefile` (str): Shapefile des contours des glaciers
- `albedo_data_path` (str): Chemin vers les données d'albédo

#### Méthodes principales

##### `load_raqdps_data(date_start, date_end, variables)`
Charge les données RAQDPS pour une période donnée.

**Paramètres:**
- `date_start` (datetime): Date de début
- `date_end` (datetime): Date de fin
- `variables` (list): Liste des variables à extraire

**Retourne:** xarray.Dataset

##### `calculate_cumulative_deposition(raqdps_data, glacier_id, window_days)`
Calcule le dépôt cumulatif sur une fenêtre temporelle.

**Paramètres:**
- `raqdps_data` (xarray.Dataset): Données RAQDPS
- `glacier_id` (str): Identifiant du glacier
- `window_days` (int): Nombre de jours pour la fenêtre cumulative

**Retourne:** pandas.DataFrame

### `RGI_RAQDPS_Analysis`

Analyse régionale utilisant le Randolph Glacier Inventory.

#### Constructeur
```python
RGI_RAQDPS_Analysis(rgi_shapefile, raqdps_path, region='02')
```

#### Méthodes principales

##### `filter_glaciers_by_criteria(min_area, max_elevation)`
Filtre les glaciers selon des critères spécifiques.

##### `batch_analysis_pipeline(start_date, end_date, output_dir)`
Pipeline complet d'analyse pour tous les glaciers.

### `AthabascaGlacierAnalysis`

Analyse spécifique pour le glacier Athabasca.

#### Constructeur
```python
AthabascaGlacierAnalysis(raqdps_path, output_dir)
```

#### Méthodes principales

##### `analyze_period(start_date, end_date, variables)`
Analyse une période complète.

##### `analyze_fire_events(df, fire_dates)`
Analyse l'impact d'événements de feux spécifiques.

## Module utilitaires : `src.utils`

### `data_loaders`

#### `load_raqdps_data(path, start_date, end_date, variables, bbox)`
Charge les données RAQDPS avec options de filtrage.

#### `load_modis_albedo(modis_path, date, tile, product)`
Charge les données d'albédo MODIS.

#### `load_fire_data(fire_path, start_date, end_date, source)`
Charge les données de feux actifs.

### `visualization`

#### `plot_time_series(df, variables, title, figsize)`
Crée un graphique de séries temporelles.

#### `create_deposition_map(glaciers_gdf, deposition_data, variable, figsize, cmap)`
Crée une carte des dépôts sur les glaciers.

#### `plot_correlation_matrix(df, variables, figsize)`
Crée une matrice de corrélation.

### `statistics`

#### `calculate_correlation(x, y, method)`
Calcule la corrélation entre deux variables.

**Paramètres:**
- `x`, `y` (array-like): Séries de données
- `method` (str): 'pearson', 'spearman', ou 'kendall'

**Retourne:** dict avec correlation, p_value, confidence_interval

#### `compute_lag_analysis(x, y, max_lag, method)`
Analyse la corrélation avec différents décalages temporels.

#### `perform_regression_analysis(X, y, include_interaction)`
Effectue une analyse de régression multiple.

## Scripts

### `process_raqdps.py`

Script principal pour traiter les données RAQDPS.

**Usage:**
```bash
python scripts/process_raqdps.py \
    --start-date 2023-07-01 \
    --end-date 2023-08-31 \
    --glacier all \
    --raqdps-path /path/to/raqdps \
    --rgi-path /path/to/rgi.shp \
    --output-dir ./results
```

### `generate_reports.py`

Génère des rapports automatiques.

**Usage:**
```bash
python scripts/generate_reports.py \
    --data-dir ./results \
    --output-dir ./reports \
    --format html
```

## Configuration

Le fichier `config/config.yaml` contient tous les paramètres configurables :

- Chemins des données
- Variables RAQDPS à analyser
- Paramètres RGI
- Fenêtres d'analyse temporelle
- Paramètres de visualisation

## Exemples d'utilisation

### Analyse simple d'un glacier

```python
from src.athabasca_glacier import AthabascaGlacierAnalysis
from datetime import datetime

# Initialiser
analysis = AthabascaGlacierAnalysis(
    raqdps_path="/path/to/raqdps",
    output_dir="./results"
)

# Analyser une période
df = analysis.analyze_period(
    datetime(2023, 7, 1),
    datetime(2023, 8, 31)
)

# Créer un rapport
summary = analysis.create_summary_report(df)
```

### Analyse régionale

```python
from src.rgi_analysis import RGI_RAQDPS_Analysis

# Charger tous les glaciers
analysis = RGI_RAQDPS_Analysis(
    rgi_shapefile="/path/to/RGI60-02.shp",
    raqdps_path="/path/to/raqdps"
)

# Filtrer les grands glaciers
analysis.filter_glaciers_by_criteria(min_area=10.0)

# Lancer l'analyse
summary = analysis.batch_analysis_pipeline(
    start_date, end_date, "./results"
)
```