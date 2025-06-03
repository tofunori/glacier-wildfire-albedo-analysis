import pytest
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from src.utils.data_loaders import (
    load_raqdps_data,
    extract_glacier_values,
    load_fire_data
)

class TestDataLoaders:
    """Tests pour les fonctions de chargement de données"""
    
    def setup_method(self):
        """Créer des données de test"""
        # Créer un répertoire temporaire
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer des fichiers NetCDF de test
        times = pd.date_range('2023-07-01', periods=24, freq='H')
        lats = np.linspace(48, 60, 20)
        lons = np.linspace(-130, -110, 25)
        
        for time in times[:3]:  # Créer seulement 3 fichiers
            data = np.random.rand(len(lats), len(lons))
            ds = xr.Dataset(
                {
                    'BC_dep': (['lat', 'lon'], data),
                    'PM2.5_dep': (['lat', 'lon'], data * 2)
                },
                coords={
                    'lat': lats,
                    'lon': lons,
                    'time': time
                }
            )
            
            filename = f"{time.strftime('%Y%m%d%H')}_000.nc"
            filepath = Path(self.temp_dir) / filename
            ds.to_netcdf(filepath)
    
    def teardown_method(self):
        """Nettoyer les fichiers temporaires"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_raqdps_data(self):
        """Test du chargement des données RAQDPS"""
        start_date = datetime(2023, 7, 1, 0)
        end_date = datetime(2023, 7, 1, 2)
        
        # Charger les données
        ds = load_raqdps_data(
            self.temp_dir,
            start_date,
            end_date,
            variables=['BC_dep', 'PM2.5_dep']
        )
        
        # Vérifications
        assert isinstance(ds, xr.Dataset)
        assert 'BC_dep' in ds
        assert 'PM2.5_dep' in ds
        assert len(ds.time) == 3
    
    def test_load_raqdps_with_bbox(self):
        """Test du chargement avec boîte englobante"""
        start_date = datetime(2023, 7, 1, 0)
        end_date = datetime(2023, 7, 1, 0)
        
        bbox = (-120, 50, -115, 55)
        ds = load_raqdps_data(
            self.temp_dir,
            start_date,
            end_date,
            bbox=bbox
        )
        
        # Vérifier que les coordonnées sont dans la bbox
        assert ds.lon.min() >= bbox[0]
        assert ds.lat.min() >= bbox[1]
        assert ds.lon.max() <= bbox[2]
        assert ds.lat.max() <= bbox[3]
    
    def test_extract_glacier_values(self):
        """Test de l'extraction des valeurs pour un glacier"""
        # Créer des données de test
        data = np.ones((10, 10))
        data[4:7, 4:7] = 2  # Zone avec valeurs différentes
        
        da = xr.DataArray(
            data,
            coords={
                'lat': np.linspace(50, 51, 10),
                'lon': np.linspace(-120, -119, 10)
            },
            dims=['lat', 'lon']
        )
        
        # Créer une géométrie de test (carré)
        from shapely.geometry import box
        glacier_geom = box(-119.5, 50.4, -119.4, 50.6)
        
        # Extraire les valeurs
        mean_val = extract_glacier_values(da, glacier_geom, method='mean')
        
        # Vérifier
        assert isinstance(mean_val, float)
        assert mean_val > 1  # Devrait être proche de 2 si dans la bonne zone

pytest.main([__file__])