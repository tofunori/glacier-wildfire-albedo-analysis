#!/bin/bash
# Script pour télécharger les données nécessaires

# Configuration
DATA_DIR="./data"
START_DATE="2023-07-01"
END_DATE="2023-08-31"

# Créer les répertoires
mkdir -p ${DATA_DIR}/{raqdps,rgi,modis,sentinel2,fires}

echo "=== Téléchargement des données ==="

# 1. RGI pour l'ouest canadien
echo "\n1. Téléchargement RGI..."
cd ${DATA_DIR}/rgi
if [ ! -f "02_rgi60_WesternCanadaUS.shp" ]; then
    wget https://www.glims.org/RGI/rgi60_files/02_rgi60_WesternCanadaUS.zip
    unzip 02_rgi60_WesternCanadaUS.zip
    rm 02_rgi60_WesternCanadaUS.zip
else
    echo "RGI déjà téléchargé"
fi
cd ../..

# 2. RAQDPS - Exemple pour une journée
echo "\n2. Téléchargement RAQDPS (exemple)..."
RAQDPS_URL="https://dd.weather.gc.ca/model_raqdps/10km/grib2"
TEST_DATE="2023/07/15"
TEST_HOUR="12"

mkdir -p ${DATA_DIR}/raqdps/${TEST_DATE//-/}
cd ${DATA_DIR}/raqdps/${TEST_DATE//-/}

if [ ! -f "${TEST_DATE//-/}${TEST_HOUR}_000.grib2" ]; then
    wget "${RAQDPS_URL}/${TEST_HOUR}/000/${TEST_DATE//-/}${TEST_HOUR}_000.grib2"
    # Convertir en NetCDF
    if command -v wgrib2 &> /dev/null; then
        wgrib2 "${TEST_DATE//-/}${TEST_HOUR}_000.grib2" -netcdf "${TEST_DATE//-/}${TEST_HOUR}_000.nc"
    fi
else
    echo "Exemple RAQDPS déjà téléchargé"
fi
cd ../../..

# 3. Données de feux MODIS
echo "\n3. Téléchargement données de feux..."
cd ${DATA_DIR}/fires
if [ ! -f "MODIS_fires_Canada_2023.csv" ]; then
    # FIRMS API nécessite une clé - utiliser l'archive
    wget "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Canada_2023.csv" \
         -O MODIS_fires_Canada_2023.csv
else
    echo "Données de feux déjà téléchargées"
fi
cd ../..

# 4. Script Python pour télécharger MODIS albédo
echo "\n4. Configuration pour MODIS albédo..."
cat > download_modis_albedo.py << 'EOF'
#!/usr/bin/env python
"""
Script pour télécharger les données MODIS MOD10A1
Nécessite un compte NASA Earthdata
"""

import os
import requests
from datetime import datetime, timedelta
from getpass import getpass

def download_modis_albedo(date, tile="h11v03", output_dir="data/modis"):
    """
    Télécharge MOD10A1 pour une date et tuile spécifiques
    """
    # Configuration
    product = "MOD10A1.061"
    base_url = f"https://n5eil01u.ecs.nsidc.org/MOST/{product}/"
    
    # Format de la date
    date_str = date.strftime("%Y.%m.%d")
    
    # URL du fichier
    filename = f"{product}.A{date.strftime('%Y%j')}.{tile}.061.*.hdf"
    
    print(f"Configuration pour télécharger {filename}")
    print("Créer un compte sur: https://urs.earthdata.nasa.gov/")
    print("Puis utiliser un outil comme wget avec authentification")
    
    return filename

if __name__ == "__main__":
    # Exemple pour une date
    test_date = datetime(2023, 7, 15)
    download_modis_albedo(test_date)
EOF

echo "\n=== Configuration terminée ==="
echo "Structure des données créée dans ${DATA_DIR}/"
echo "\nPour MODIS et Sentinel-2 :"
echo "1. Créer un compte NASA Earthdata : https://urs.earthdata.nasa.gov/"
echo "2. Créer un compte Copernicus : https://scihub.copernicus.eu/dhus/"
echo "3. Utiliser les notebooks Jupyter pour télécharger les données"
echo "\nPour RAQDPS complet :"
echo "Utiliser le script process_raqdps.py avec les dates souhaitées"