# Guide de démarrage rapide

## 1. Installation

### Prérequis
- Python 3.8+
- Git
- Compte NASA Earthdata (pour MODIS)
- Compte Copernicus (pour Sentinel-2)

### Installation du projet

```bash
# Cloner le repository
git clone https://github.com/tofunori/glacier-wildfire-albedo-analysis.git
cd glacier-wildfire-albedo-analysis

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer le package en mode développement
pip install -e .
```

## 2. Configuration initiale

### Structure des données

Créez la structure de répertoires nécessaire :

```bash
mkdir -p data/{raqdps,rgi,modis,sentinel2,fires}
mkdir -p results/{raqdps_analysis,correlation_analysis,reports}
mkdir -p figures
```

### Télécharger les données RGI

```bash
# Exécuter le script de téléchargement
chmod +x scripts/download_data.sh
./scripts/download_data.sh
```

## 3. Première analyse

### Analyse du glacier Athabasca

```python
from src.athabasca_glacier import AthabascaGlacierAnalysis
from datetime import datetime

# Initialiser l'analyse
analysis = AthabascaGlacierAnalysis(
    raqdps_path="data/raqdps/",
    output_dir="results/athabasca"
)

# Analyser juillet 2023
start = datetime(2023, 7, 1)
end = datetime(2023, 7, 31)

df = analysis.analyze_period(start, end)
summary = analysis.create_summary_report(df)
print(summary)
```

### Utilisation du script de traitement

```bash
# Analyse d'un glacier spécifique
python scripts/process_raqdps.py \
    --start-date 2023-07-01 \
    --end-date 2023-08-31 \
    --glacier athabasca \
    --raqdps-path data/raqdps \
    --output-dir results

# Analyse régionale (tous les glaciers)
python scripts/process_raqdps.py \
    --start-date 2023-07-01 \
    --end-date 2023-08-31 \
    --glacier all \
    --raqdps-path data/raqdps \
    --rgi-path data/rgi/RGI60-02.shp \
    --output-dir results \
    --min-area 5.0
```

## 4. Exploration avec Jupyter

Lancez Jupyter pour explorer les notebooks :

```bash
jupyter notebook
```

Ouvrez les notebooks dans l'ordre :
1. `01_data_exploration.ipynb` - Explorer les données
2. `02_raqdps_analysis.ipynb` - Analyser les dépôts
3. `03_albedo_correlation.ipynb` - Étudier les corrélations

## 5. Génération de rapports

```bash
# Générer un rapport HTML
python scripts/generate_reports.py \
    --data-dir results \
    --output-dir reports \
    --format html

# Générer un rapport PDF (nécessite wkhtmltopdf)
python scripts/generate_reports.py \
    --data-dir results \
    --output-dir reports \
    --format pdf
```

## 6. Accès aux données RAQDPS

### Option 1: Téléchargement manuel

Téléchargez depuis le Datamart d'ECCC :
```bash
BASE_URL="https://dd.weather.gc.ca/model_raqdps/10km/grib2/"
DATE="20230715"
HOUR="12"
wget ${BASE_URL}/${HOUR}/000/${DATE}${HOUR}_000.grib2
```

### Option 2: Script automatisé

Créez un script `download_raqdps.py` :

```python
import requests
from datetime import datetime, timedelta
import os

def download_raqdps_period(start_date, end_date, output_dir):
    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y%m%d')
        for hour in range(0, 24, 6):  # Toutes les 6 heures
            hour_str = f"{hour:02d}"
            filename = f"{date_str}{hour_str}_000.grib2"
            url = f"https://dd.weather.gc.ca/model_raqdps/10km/grib2/{hour_str}/000/{filename}"
            
            output_path = os.path.join(output_dir, date_str, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if not os.path.exists(output_path):
                print(f"Téléchargement: {filename}")
                response = requests.get(url)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                else:
                    print(f"Erreur: {response.status_code}")
        
        current += timedelta(days=1)

# Utilisation
start = datetime(2023, 7, 1)
end = datetime(2023, 7, 7)
download_raqdps_period(start, end, "data/raqdps")
```

## 7. Dépannage

### Problème: Fichiers RAQDPS manquants

Les notebooks utilisent des données synthétiques si les vrais fichiers ne sont pas disponibles.

### Problème: Erreur d'importation

Assurez-vous d'avoir activé l'environnement virtuel et installé toutes les dépendances.

### Problème: Mémoire insuffisante

Pour les analyses régionales, filtrez les glaciers par surface minimale ou traitez par lots.

## 8. Prochaines étapes

1. **Obtenir les données réelles** :
   - Créer un compte NASA Earthdata
   - Télécharger les données MODIS MOD10A1
   - Obtenir l'accès complet aux archives RAQDPS

2. **Personnaliser l'analyse** :
   - Modifier `config/config.yaml`
   - Ajouter vos glaciers d'intérêt
   - Ajuster les fenêtres temporelles

3. **Étendre le code** :
   - Ajouter le support Sentinel-2
   - Intégrer les trajectoires HYSPLIT
   - Implémenter des modèles ML

## Support

Pour des questions ou problèmes :
- Ouvrir une issue sur GitHub
- Consulter la documentation dans `docs/`
- Voir les exemples dans les notebooks