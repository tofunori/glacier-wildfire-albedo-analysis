"""
Fonctions utilitaires pour charger différents types de données
"""

import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import rasterio
from datetime import datetime, timedelta
import geopandas as gpd

def load_raqdps_data(path, start_date, end_date, variables=None, bbox=None):
    """
    Charger les données RAQDPS pour une période donnée
    
    Args:
        path: Chemin vers les fichiers RAQDPS
        start_date: Date de début
        end_date: Date de fin
        variables: Liste des variables à extraire
        bbox: Boîte englobante (lon_min, lat_min, lon_max, lat_max)
    
    Returns:
        xarray.Dataset avec les données concaténées
    """
    if variables is None:
        variables = ['BC_dep', 'PM2.5_dep', 'PM10_dep']
    
    datasets = []
    current = start_date
    
    while current <= end_date:
        filename = Path(path) / f"{current.strftime('%Y%m%d%H')}_000.nc"
        
        if filename.exists():
            ds = xr.open_dataset(filename)
            
            # Sélectionner les variables
            if variables:
                ds = ds[variables]
            
            # Appliquer la boîte englobante si fournie
            if bbox:
                ds = ds.sel(
                    lon=slice(bbox[0], bbox[2]),
                    lat=slice(bbox[1], bbox[3])
                )
            
            datasets.append(ds)
        
        current += timedelta(hours=1)
    
    if datasets:
        return xr.concat(datasets, dim='time')
    else:
        raise ValueError("Aucune donnée trouvée pour la période spécifiée")

def load_modis_albedo(modis_path, date, tile='h11v03', product='MOD10A1'):
    """
    Charger les données d'albédo MODIS
    
    Args:
        modis_path: Chemin vers les fichiers MODIS
        date: Date des données
        tile: Tuile MODIS
        product: Produit MODIS (MOD10A1 par défaut)
    
    Returns:
        numpy.ndarray avec les valeurs d'albédo
    """
    # Construire le nom du fichier
    julian_day = date.timetuple().tm_yday
    filename = Path(modis_path) / f"{product}.A{date.year}{julian_day:03d}.{tile}.061.*.hdf"
    
    # Trouver le fichier correspondant
    matching_files = list(Path(modis_path).glob(filename.name))
    
    if not matching_files:
        raise FileNotFoundError(f"Aucun fichier MODIS trouvé pour {date}")
    
    # Utiliser rasterio pour lire le HDF
    with rasterio.open(matching_files[0]) as src:
        # MODIS stocke l'albédo dans le subdataset 'Snow_Albedo_Daily'
        albedo = src.read(1)
        
        # Appliquer les facteurs d'échelle MODIS
        albedo = albedo.astype(np.float32)
        albedo[albedo == 32767] = np.nan  # NoData
        albedo = albedo * 0.001  # Facteur d'échelle
        
        return albedo, src.transform, src.crs

def load_sentinel2_albedo(s2_path, date, bands=['B02', 'B03', 'B04', 'B08', 'B11']):
    """
    Charger et calculer l'albédo à partir de Sentinel-2
    
    Args:
        s2_path: Chemin vers les données Sentinel-2
        date: Date d'acquisition
        bands: Bandes à utiliser pour le calcul
    
    Returns:
        numpy.ndarray avec l'albédo calculé
    """
    # Coefficients pour narrow-to-broadband (Liang, 2001)
    coeffs = {
        'B02': 0.356,   # Blue
        'B03': 0.130,   # Green
        'B04': 0.373,   # Red
        'B08': 0.085,   # NIR
        'B11': 0.072    # SWIR1
    }
    
    albedo_sum = None
    
    for band in bands:
        if band in coeffs:
            band_path = Path(s2_path) / f"*_{band}_10m.jp2"
            matching_files = list(Path(s2_path).glob(band_path.name))
            
            if matching_files:
                with rasterio.open(matching_files[0]) as src:
                    data = src.read(1).astype(np.float32) / 10000  # Facteur Sentinel-2
                    
                    if albedo_sum is None:
                        albedo_sum = np.zeros_like(data)
                        transform = src.transform
                        crs = src.crs
                    
                    albedo_sum += data * coeffs[band]
    
    # Soustraire le terme constant
    albedo = albedo_sum - 0.0018
    albedo = np.clip(albedo, 0, 1)  # Limiter entre 0 et 1
    
    return albedo, transform, crs

def load_fire_data(fire_path, start_date, end_date, source='modis'):
    """
    Charger les données de feux actifs
    
    Args:
        fire_path: Chemin vers les données de feux
        start_date: Date de début
        end_date: Date de fin
        source: Source des données ('modis', 'viirs', 'cwfis')
    
    Returns:
        GeoDataFrame avec les points de feux
    """
    if source == 'modis':
        # Charger le CSV MODIS
        df = pd.read_csv(fire_path)
        
        # Convertir les dates
        df['datetime'] = pd.to_datetime(df['acq_date'] + ' ' + df['acq_time'].astype(str).str.zfill(4), 
                                       format='%Y-%m-%d %H%M')
        
        # Filtrer par date
        mask = (df['datetime'] >= start_date) & (df['datetime'] <= end_date)
        df = df[mask]
        
        # Créer le GeoDataFrame
        geometry = gpd.points_from_xy(df.longitude, df.latitude)
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
        
        # Garder les colonnes importantes
        columns_to_keep = ['datetime', 'latitude', 'longitude', 'brightness', 
                          'scan', 'track', 'frp', 'confidence', 'geometry']
        
        return gdf[columns_to_keep]
    
    elif source == 'viirs':
        # Implémentation similaire pour VIIRS
        pass
    
    elif source == 'cwfis':
        # Canadian Wildland Fire Information System
        pass
    
    else:
        raise ValueError(f"Source {source} non supportée")

def extract_glacier_values(data_array, glacier_geometry, method='mean'):
    """
    Extraire les valeurs d'un array pour un glacier donné
    
    Args:
        data_array: xarray.DataArray ou numpy.ndarray
        glacier_geometry: Shapely geometry du glacier
        method: Méthode d'agrégation ('mean', 'sum', 'max', 'min')
    
    Returns:
        Valeur agrégée
    """
    from rasterio.features import geometry_mask
    
    if isinstance(data_array, xr.DataArray):
        # Obtenir les coordonnées
        lons = data_array.lon.values
        lats = data_array.lat.values
        values = data_array.values
    else:
        # Supposer que c'est un numpy array
        values = data_array
    
    # Créer le masque
    mask = geometry_mask(
        [glacier_geometry],
        transform=rasterio.transform.from_bounds(
            glacier_geometry.bounds[0], 
            glacier_geometry.bounds[1],
            glacier_geometry.bounds[2], 
            glacier_geometry.bounds[3],
            values.shape[1], 
            values.shape[0]
        ),
        invert=True,
        out_shape=values.shape
    )
    
    # Appliquer le masque
    masked_values = np.ma.masked_array(values, ~mask)
    
    # Calculer l'agrégation
    if method == 'mean':
        return float(masked_values.mean())
    elif method == 'sum':
        return float(masked_values.sum())
    elif method == 'max':
        return float(masked_values.max())
    elif method == 'min':
        return float(masked_values.min())
    else:
        raise ValueError(f"Méthode {method} non supportée")