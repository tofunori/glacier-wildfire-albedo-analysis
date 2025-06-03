# Méthodologie détaillée

## 1. Extraction des données RAQDPS

### 1.1 Variables de dépôt

Le modèle RAQDPS fournit les flux de dépôt (kg/m²/s) pour plusieurs espèces chimiques :

- **BC_dep** : Carbone noir (Black Carbon)
  - Principal absorbeur de radiation solaire
  - Impact maximal sur l'albédo
  
- **PM2.5_dep** : Particules fines < 2.5 μm
  - Incluent le BC et autres composés
  - Pénétration profonde dans le manteau neigeux

- **PM10_dep** : Particules < 10 μm
  - Incluent les particules plus grossières
  - Dépôt principalement en surface

### 1.2 Processus de dépôt

**Dépôt sec** : Sédimentation gravitationnelle et diffusion turbulente
- Dépend de la vitesse du vent et de la stabilité atmosphérique
- Plus efficace pour les grosses particules

**Dépôt humide** : Lessivage par les précipitations
- In-cloud scavenging (nucléation)
- Below-cloud scavenging (collision)
- Plus efficace pour les particules fines

## 2. Traitement spatial

### 2.1 Projection et interpolation

```python
# Reprojection des données RAQDPS vers la projection des glaciers
from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:4326",  # WGS84
    "EPSG:3979",  # NAD83 Canada Atlas Lambert
    always_xy=True
)
```

### 2.2 Masquage des glaciers

- Utilisation des polygones RGI
- Buffer pour capturer les dépôts périphériques
- Pondération par l'altitude si disponible

## 3. Analyse temporelle

### 3.1 Fenêtres cumulatives

```
Dépôt instantané → Cumul 24h → Cumul 7j → Cumul saisonnier
```

### 3.2 Décalage temporel (lag)

L'impact sur l'albédo n'est pas instantané :
- Lag 0-1 jour : Dépôt en surface
- Lag 2-5 jours : Mélange avec la neige
- Lag 5-10 jours : Effet cumulatif

## 4. Corrélation avec l'albédo

### 4.1 Sources d'albédo

**MODIS (MOD10A1)** :
- Résolution : 500m
- Fréquence : Journalière
- Bandes : Albédo large bande (0.3-3.0 μm)

**Sentinel-2** :
- Résolution : 10-20m
- Fréquence : 5 jours
- Calcul : Albédo narrowband-to-broadband

### 4.2 Métriques de corrélation

1. **Corrélation de Pearson** : Relation linéaire
2. **Corrélation de Spearman** : Relation monotone
3. **Régression multiple** : Incluant les covariables météo

## 5. Facteurs de confusion

### 5.1 Variables météorologiques

- **Température** : Métamorphisme de la neige
- **Précipitations** : Renouvellement de la surface
- **Rayonnement solaire** : Vieillissement de la neige
- **Vent** : Redistribution des particules

### 5.2 Processus glaciologiques

- **Accumulation** : Enfouissement des particules
- **Ablation** : Concentration en surface
- **Regel** : Piégeage dans la glace

## 6. Validation

### 6.1 Comparaison avec la littérature

Valeurs typiques de réduction d'albédo :
- BC 50 ng/g : Δα = -0.01 à -0.02
- BC 500 ng/g : Δα = -0.05 à -0.10
- Poussière minérale : Effet moindre

### 6.2 Analyse de sensibilité

- Taille de la fenêtre cumulative
- Seuil de dépôt minimal
- Méthode d'interpolation spatiale

## 7. Incertitudes

### 7.1 Sources d'incertitude

1. **Modèle RAQDPS** : ±30-50% sur les dépôts
2. **Masques nuageux** : Données satellite manquantes
3. **Résolution spatiale** : Hétérogénéité sub-pixel
4. **Processus non linéaires** : Rétroactions complexes

### 7.2 Propagation d'erreur

```python
# Exemple de Monte Carlo pour l'incertitude
import numpy as np

n_simulations = 1000
bc_uncertainty = 0.3  # 30%
albedo_uncertainty = 0.05  # 5%

# Générer des réalisations
bc_samples = bc_dep * (1 + np.random.normal(0, bc_uncertainty, n_simulations))
albedo_samples = albedo * (1 + np.random.normal(0, albedo_uncertainty, n_simulations))
```