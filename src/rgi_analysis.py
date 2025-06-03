import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy import stats
import regionmask
from shapely.geometry import Point
import os

class RGI_RAQDPS_Analysis:
    """
    Analyse de l'impact des dépôts de particules sur l'albédo des glaciers
    en utilisant le Randolph Glacier Inventory (RGI) et RAQDPS
    """
    
    def __init__(self, rgi_shapefile, raqdps_path, region='02'):
        """
        Initialisation avec RGI
        
        Args:
            rgi_shapefile: Chemin vers le shapefile RGI (ex: RGI60-02.shp pour Western Canada)
            raqdps_path: Chemin vers les données RAQDPS
            region: Code région RGI ('02' pour Western Canada and US)
        """
        self.raqdps_path = raqdps_path
        self.region = region
        
        # Charger les glaciers RGI
        print(f"Chargement RGI région {region}...")
        self.glaciers = gpd.read_file(rgi_shapefile)
        
        # Filtrer pour l'ouest canadien si nécessaire
        if region == '02':
            # Garder seulement les glaciers canadiens (exclure US)
            self.glaciers = self.glaciers[
                self.glaciers['CenLon'] < -115  # Approximativement ouest canadien
            ]
        
        print(f"Nombre de glaciers chargés: {len(self.glaciers)}")
        
        # Créer des masques de glaciers pour l'analyse efficace
        self.glacier_masks = None
        
    def filter_glaciers_by_criteria(self, min_area=1.0, max_elevation=None):
        """
        Filtrer les glaciers selon des critères spécifiques
        
        Args:
            min_area: Surface minimale en km² (défaut: 1.0)
            max_elevation: Élévation maximale en mètres
        """
        initial_count = len(self.glaciers)
        
        # Filtrer par surface
        self.glaciers = self.glaciers[self.glaciers['Area'] >= min_area]
        
        # Filtrer par élévation si spécifié
        if max_elevation:
            self.glaciers = self.glaciers[self.glaciers['Zmed'] <= max_elevation]
        
        print(f"Glaciers filtrés: {initial_count} → {len(self.glaciers)}")
        
    def create_glacier_regions_mask(self, raqdps_grid):
        """
        Créer des masques efficaces pour tous les glaciers sur la grille RAQDPS
        """
        # Obtenir les coordonnées de la grille RAQDPS
        lons = raqdps_grid.lon.values
        lats = raqdps_grid.lat.values
        
        # Créer un masque régional avec regionmask
        self.glacier_masks = regionmask.Regions(
            name="RGI_Glaciers",
            numbers=list(range(len(self.glaciers))),
            names=self.glaciers['RGIId'].tolist(),
            abbrevs=self.glaciers['RGIId'].tolist(),
            outlines=self.glaciers.geometry.tolist()
        )
        
        # Créer le masque sur la grille RAQDPS
        self.mask_array = self.glacier_masks.mask(lons, lats)
        
    def extract_deposition_timeseries(self, start_date, end_date, 
                                    variables=['BC_dep', 'PM2.5_dep', 'PM10_dep']):
        """
        Extraire les séries temporelles de dépôt pour tous les glaciers
        """
        print(f"Extraction des dépôts de {start_date} à {end_date}")
        
        # Initialiser le stockage des résultats
        results = {glacier_id: [] for glacier_id in self.glaciers['RGIId']}
        
        # Parcourir les dates
        current_date = start_date
        while current_date <= end_date:
            # Charger les données RAQDPS pour cette heure
            filename = f"{self.raqdps_path}/{current_date.strftime('%Y%m%d%H')}_000.nc"
            
            try:
                with xr.open_dataset(filename) as ds:
                    # Si c'est la première fois, créer les masques
                    if self.glacier_masks is None:
                        self.create_glacier_regions_mask(ds)
                    
                    # Extraire les dépôts pour chaque variable
                    for var in variables:
                        if var in ds:
                            # Appliquer le masque pour obtenir les valeurs par glacier
                            for i, glacier_id in enumerate(self.glaciers['RGIId']):
                                mask = (self.mask_array == i)
                                
                                # Calculer la moyenne et la somme sur le glacier
                                dep_mean = float(ds[var].where(mask).mean())
                                dep_sum = float(ds[var].where(mask).sum())
                                
                                results[glacier_id].append({
                                    'time': current_date,
                                    f'{var}_mean': dep_mean,
                                    f'{var}_sum': dep_sum
                                })
                
            except FileNotFoundError:
                print(f"Fichier manquant: {filename}")
            
            # Passer à l'heure suivante
            current_date += timedelta(hours=1)
        
        # Convertir en DataFrames
        glacier_timeseries = {}
        for glacier_id, data in results.items():
            if data:
                df = pd.DataFrame(data)
                df.set_index('time', inplace=True)
                glacier_timeseries[glacier_id] = df
        
        return glacier_timeseries
    
    def analyze_fire_events(self, fire_data_path, buffer_km=200):
        """
        Analyser la proximité des feux aux glaciers
        
        Args:
            fire_data_path: Chemin vers les données de feux (MODIS, VIIRS, etc.)
            buffer_km: Rayon de recherche autour des glaciers en km
        """
        # Charger les données de feux
        fires = gpd.read_file(fire_data_path)
        
        # Projeter en coordonnées métriques pour les calculs de distance
        glaciers_proj = self.glaciers.to_crs('EPSG:3857')
        fires_proj = fires.to_crs('EPSG:3857')
        
        # Créer des buffers autour des glaciers
        glacier_buffers = glaciers_proj.buffer(buffer_km * 1000)  # Convertir km en m
        
        # Identifier les feux dans les zones d'influence
        fire_glacier_proximity = []
        
        for idx, glacier in glaciers_proj.iterrows():
            glacier_buffer = glacier.geometry.buffer(buffer_km * 1000)
            
            # Feux dans le buffer
            nearby_fires = fires_proj[fires_proj.geometry.within(glacier_buffer)]
            
            if len(nearby_fires) > 0:
                # Calculer les statistiques
                distances = nearby_fires.geometry.distance(glacier.geometry) / 1000  # en km
                
                fire_glacier_proximity.append({
                    'RGIId': self.glaciers.iloc[idx]['RGIId'],
                    'n_fires': len(nearby_fires),
                    'min_distance_km': distances.min(),
                    'mean_distance_km': distances.mean(),
                    'total_FRP': nearby_fires['FRP'].sum() if 'FRP' in nearby_fires else None,
                    'fire_dates': nearby_fires['date'].tolist() if 'date' in nearby_fires else None
                })
        
        return pd.DataFrame(fire_glacier_proximity)
    
    def calculate_transport_probability(self, glacier_id, wind_data):
        """
        Calculer la probabilité de transport des particules vers un glacier
        basé sur les données de vent RAQDPS
        """
        glacier = self.glaciers[self.glaciers['RGIId'] == glacier_id].iloc[0]
        glacier_loc = (glacier['CenLat'], glacier['CenLon'])
        
        # Analyser les trajectoires de vent
        # Simplification: utiliser les vents à 10m et 850 hPa
        transport_scores = []
        
        for time in wind_data.time:
            u10 = wind_data['u_10m'].sel(time=time)
            v10 = wind_data['v_10m'].sel(time=time)
            
            # Calculer la direction du vent et la probabilité de transport
            # (Code simplifié - en pratique, utiliser HYSPLIT ou similaire)
            wind_direction = np.arctan2(v10, u10) * 180 / np.pi
            
            # Score basé sur la direction du vent vers le glacier
            # À implémenter selon la localisation des sources de feux
            
        return transport_scores
    
    def batch_analysis_pipeline(self, start_date, end_date, output_dir):
        """
        Pipeline complet d'analyse pour tous les glaciers
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Extraire les dépôts
        print("1. Extraction des séries temporelles de dépôt...")
        deposition_series = self.extract_deposition_timeseries(start_date, end_date)
        
        # 2. Calculer les statistiques par glacier
        print("2. Calcul des statistiques...")
        glacier_stats = []
        
        for glacier_id, df in deposition_series.items():
            if len(df) > 0:
                glacier_info = self.glaciers[self.glaciers['RGIId'] == glacier_id].iloc[0]
                
                # Calculer les dépôts cumulatifs
                df['BC_cumul_7d'] = df['BC_dep_sum'].rolling('7D').sum()
                df['PM25_cumul_7d'] = df['PM2.5_dep_sum'].rolling('7D').sum()
                
                stats = {
                    'RGIId': glacier_id,
                    'Name': glacier_info['Name'] if 'Name' in glacier_info else 'Unknown',
                    'Area_km2': glacier_info['Area'],
                    'Elev_mean': glacier_info['Zmed'],
                    'BC_total': df['BC_dep_sum'].sum(),
                    'BC_max_7d': df['BC_cumul_7d'].max(),
                    'PM25_total': df['PM2.5_dep_sum'].sum(),
                    'PM25_max_7d': df['PM25_cumul_7d'].max(),
                    'n_hours_data': len(df)
                }
                
                glacier_stats.append(stats)
                
                # Sauvegarder les séries temporelles
                df.to_csv(f"{output_dir}/{glacier_id}_deposition.csv")
        
        # Créer un DataFrame de résumé
        summary_df = pd.DataFrame(glacier_stats)
        summary_df.to_csv(f"{output_dir}/glacier_deposition_summary.csv", index=False)
        
        return summary_df
    
    def plot_regional_deposition_map(self, summary_df, variable='BC_total'):
        """
        Créer une carte régionale des dépôts sur les glaciers
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Fusionner les données avec les géométries
        glaciers_with_data = self.glaciers.merge(
            summary_df[['RGIId', variable]], 
            on='RGIId'
        )
        
        # Créer la carte
        glaciers_with_data.plot(
            column=variable,
            ax=ax,
            legend=True,
            cmap='YlOrRd',
            legend_kwds={'label': f'{variable} (kg/m²)'}
        )
        
        # Ajouter le contexte géographique
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title(f'Dépôt total sur les glaciers RGI - Ouest Canadien')
        ax.grid(True, alpha=0.3)
        
        return fig

# Exemple d'utilisation
if __name__ == "__main__":
    # Chemins des données
    RGI_PATH = "/path/to/RGI60-02/RGI60-02.shp"  # Western Canada and US
    RAQDPS_PATH = "/path/to/raqdps/data"
    
    # Initialiser l'analyse
    analysis = RGI_RAQDPS_Analysis(
        rgi_shapefile=RGI_PATH,
        raqdps_path=RAQDPS_PATH,
        region='02'
    )
    
    # Filtrer les glaciers (optionnel)
    analysis.filter_glaciers_by_criteria(
        min_area=5.0,  # Garder seulement les glaciers > 5 km²
        max_elevation=4000  # Exclure les très hauts sommets
    )
    
    # Définir la période d'analyse (été 2023 - saison des feux)
    start_date = datetime(2023, 6, 1, 0)
    end_date = datetime(2023, 9, 30, 23)
    
    # Lancer l'analyse batch
    print("Lancement de l'analyse complète...")
    summary = analysis.batch_analysis_pipeline(
        start_date, 
        end_date,
        output_dir="/path/to/output"
    )
    
    # Afficher les glaciers les plus impactés
    print("\nTop 10 glaciers par dépôt de carbone noir:")
    top_glaciers = summary.nlargest(10, 'BC_total')
    print(top_glaciers[['RGIId', 'Name', 'Area_km2', 'BC_total', 'BC_max_7d']])
    
    # Créer la carte
    fig = analysis.plot_regional_deposition_map(summary, 'BC_total')
    plt.savefig('/path/to/output/deposition_map.png', dpi=300, bbox_inches='tight')