# Sources de données détaillées

## RAQDPS (Regional Air Quality Deterministic Prediction System)

### Accès aux données

**Datamart ECCC** :
```bash
# URL de base
BASE_URL="https://dd.weather.gc.ca/model_raqdps/10km/grib2/"

# Format des fichiers
# {YYYYMMDDHH}_000.grib2
# Exemple : 2023071512_000.grib2

# Téléchargement avec wget
wget ${BASE_URL}/${HH}/${FORECAST}/${YYYYMMDDHH}_000.grib2
```

### Variables disponibles

| Variable | Description | Unité | Niveau |
|----------|-------------|-------|--------|
| BC_dep | Dépôt de carbone noir | kg/m²/s | Surface |
| PM2.5_dep | Dépôt PM2.5 | kg/m²/s | Surface |
| PM10_dep | Dépôt PM10 | kg/m²/s | Surface |
| OC_dep | Dépôt carbone organique | kg/m²/s | Surface |
| SO4_dep | Dépôt sulfates | kg/m²/s | Surface |
| NO3_dep | Dépôt nitrates | kg/m²/s | Surface |
| dust_dep | Dépôt poussière | kg/m²/s | Surface |
| BC | Concentration BC | μg/m³ | Multiple |
| PM2.5 | Concentration PM2.5 | μg/m³ | Surface |

### Conversion GRIB2 vers NetCDF

```bash
# Utiliser wgrib2
wgrib2 input.grib2 -netcdf output.nc

# Ou avec CDO
cdo -f nc copy input.grib2 output.nc
```

## Randolph Glacier Inventory (RGI 6.0)

### Téléchargement

```bash
# Région 02 - Western Canada and US
wget https://www.glims.org/RGI/rgi60_files/02_rgi60_WesternCanadaUS.zip

# Toutes les régions
wget https://www.glims.org/RGI/rgi60_files/00_rgi60_attribs.zip
```

### Structure des attributs

```python
# Colonnes principales
rgi_columns = [
    'RGIId',          # Identifiant unique
    'GLIMSId',        # ID GLIMS si disponible  
    'BgnDate',        # Date image source
    'EndDate',        # Date fin si composite
    'CenLon',         # Longitude centroïde
    'CenLat',         # Latitude centroïde
    'O1Region',       # Région niveau 1
    'O2Region',       # Région niveau 2
    'Area',           # Surface (km²)
    'Zmin',           # Altitude min (m)
    'Zmax',           # Altitude max (m)
    'Zmed',           # Altitude médiane (m)
    'Slope',          # Pente moyenne (°)
    'Aspect',         # Orientation (°)
    'Lmax',           # Longueur max (m)
    'Status',         # Statut (0=Land-terminating)
    'Connect',        # Connectivité
    'Form',           # Forme
    'TermType',       # Type terminus
    'Surging',        # Surge (0=No)
    'Linkages',       # Liens hydriques
    'Name'            # Nom si connu
]
```

## MODIS Snow Products

### MOD10A1 - Snow Cover Daily

**Téléchargement via Earthdata** :
```python
import requests
from datetime import datetime

# Configuration
product = "MOD10A1.061"  # Collection 6.1
tile = "h11v03"          # Tile pour l'ouest canadien
date = datetime(2023, 7, 15)

# URL de base
base_url = f"https://n5eil01u.ecs.nsidc.org/MOST/{product}/"
file_url = f"{base_url}{date.strftime('%Y.%m.%d')}/"
```

### Variables MOD10A1

- **NDSI_Snow_Cover** : Indice de neige
- **Snow_Albedo_Daily** : Albédo de la neige
- **orbit_info** : Information sur l'orbite
- **granule_pnt** : Points de la granule

## Sentinel-2

### Accès via sentinelsat

```python
from sentinelsat import SentinelAPI

# Connexion
api = SentinelAPI('username', 'password', 
                  'https://scihub.copernicus.eu/dhus')

# Recherche pour le glacier Athabasca
footprint = "POLYGON((-117.27 52.17, -117.24 52.17, 
                      -117.24 52.20, -117.27 52.20, 
                      -117.27 52.17))"

products = api.query(footprint,
                     date=('20230701', '20230831'),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 30),
                     producttype='S2MSI2A')  # Niveau 2A
```

### Calcul de l'albédo Sentinel-2

```python
# Coefficients pour narrow-to-broadband
# Liang (2001) pour Sentinel-2
coeffs = {
    'B2': 0.356,   # Blue
    'B3': 0.130,   # Green  
    'B4': 0.373,   # Red
    'B8': 0.085,   # NIR
    'B11': 0.072   # SWIR1
}

# Albédo = Σ(coeff * bande) - 0.0018
```

## Données de feux

### MODIS Active Fire (MCD14ML)

```bash
# Téléchargement depuis FIRMS
wget https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Canada_24h.csv
```

### Canadian Wildland Fire Information System

```python
# API CWFIS
import requests

# Points chauds
hotspots_url = "https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/"

# Périmètres de feux
perimeters_url = "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/"
```

## Données météorologiques complémentaires

### ERA5 (pour validation)

```python
import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': [
            '2m_temperature',
            'total_precipitation',
            '10m_u_component_of_wind',
            '10m_v_component_of_wind',
        ],
        'year': '2023',
        'month': ['07', '08'],
        'day': [str(d).zfill(2) for d in range(1, 32)],
        'time': [str(h).zfill(2) + ':00' for h in range(24)],
        'area': [53, -120, 49, -114],  # Ouest canadien
    },
    'era5_glacier_region.nc'
)
```