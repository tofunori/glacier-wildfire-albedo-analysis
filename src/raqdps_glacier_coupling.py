import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy import stats
import rasterio
from rasterio.warp import reproject, Resampling

class RAQDPSGlacierAnalysis:
    """
    Classe pour analyser l'impact des dépôts de particules sur l'albédo des glaciers
    en utilisant les données RAQDPS
    """
    
    def __init__(self, raqdps_path, glacier_shapefile, albedo_data_path):
        """
        Initialisation avec les chemins des données
        
        Args:
            raqdps_path: Chemin vers les fichiers RAQDPS NetCDF
            glacier_shapefile: Shapefile des contours des glaciers
            albedo_data_path: Chemin vers les données d'albédo (MODIS/Sentinel)
        """
        self.raqdps_path = raqdps_path
        self.glaciers = gpd.read_file(glacier_shapefile)
        self.albedo_path = albedo_data_path
        
    def load_raqdps_data(self, date_start, date_end, variables=['BC_dep', 'PM2.5_dep']):
        """
        Charger les données RAQDPS pour une période donnée
        
        Args:
            date_start: Date de début (datetime)
            date_end: Date de fin (datetime)
            variables: Liste des variables à extraire
        """
        # Générer la liste des fichiers pour la période
        dates = pd.date_range(date_start, date_end, freq='H')
        datasets = []
        
        for date in dates:
            # Format typique des fichiers RAQDPS: YYYYMMDDHH_000.nc
            filename = f"{self.raqdps_path}/{date.strftime('%Y%m%d%H')}_000.nc"
            try:
                ds = xr.open_dataset(filename)
                # Extraire seulement les variables nécessaires
                ds_subset = ds[variables]
                datasets.append(ds_subset)
            except FileNotFoundError:
                print(f"Fichier manquant: {filename}")
                continue
        
        # Combiner tous les datasets
        return xr.concat(datasets, dim='time')
    
    def extract_glacier_deposition(self, raqdps_data, glacier_id):
        """
        Extraire les données de dépôt pour un glacier spécifique
        
        Args:
            raqdps_data: Dataset xarray RAQDPS
            glacier_id: Identifiant du glacier
        """
        # Obtenir les coordonnées du glacier
        glacier = self.glaciers[self.glaciers['ID'] == glacier_id].iloc[0]
        glacier_bounds = glacier.geometry.bounds
        
        # Extraire la région d'intérêt
        roi = raqdps_data.sel(
            lat=slice(glacier_bounds[1], glacier_bounds[3]),
            lon=slice(glacier_bounds[0], glacier_bounds[2])
        )
        
        # Masquer avec le contour exact du glacier
        glacier_mask = self.create_glacier_mask(roi, glacier.geometry)
        
        # Calculer les statistiques de dépôt
        deposition_stats = {
            'mean_BC_dep': float(roi['BC_dep'].where(glacier_mask).mean()),
            'total_BC_dep': float(roi['BC_dep'].where(glacier_mask).sum()),
            'mean_PM25_dep': float(roi['PM2.5_dep'].where(glacier_mask).mean()),
            'total_PM25_dep': float(roi['PM2.5_dep'].where(glacier_mask).sum()),
            'area_km2': glacier.geometry.area / 1e6
        }
        
        return deposition_stats
    
    def calculate_cumulative_deposition(self, raqdps_data, glacier_id, window_days=7):
        """
        Calculer le dépôt cumulatif sur une fenêtre temporelle
        
        Args:
            raqdps_data: Dataset xarray RAQDPS
            glacier_id: ID du glacier
            window_days: Nombre de jours pour la fenêtre cumulative
        """
        # Extraire les séries temporelles pour le glacier
        deposition_series = []
        
        for time in raqdps_data.time:
            stats = self.extract_glacier_deposition(
                raqdps_data.sel(time=time), 
                glacier_id
            )
            stats['time'] = pd.Timestamp(time.values)
            deposition_series.append(stats)
        
        # Convertir en DataFrame
        df = pd.DataFrame(deposition_series)
        df.set_index('time', inplace=True)
        
        # Calculer les dépôts cumulatifs
        df['BC_cumul'] = df['total_BC_dep'].rolling(
            window=f'{window_days}D', 
            min_periods=1
        ).sum()
        
        df['PM25_cumul'] = df['total_PM25_dep'].rolling(
            window=f'{window_days}D', 
            min_periods=1
        ).sum()
        
        return df
    
    def load_albedo_data(self, glacier_id, date_start, date_end):
        """
        Charger les données d'albédo satellite pour un glacier
        
        Args:
            glacier_id: ID du glacier
            date_start: Date de début
            date_end: Date de fin
        """
        # Exemple pour MODIS MOD10A1
        albedo_series = []
        
        dates = pd.date_range(date_start, date_end, freq='D')
        for date in dates:
            # Charger le fichier MODIS du jour
            modis_file = f"{self.albedo_path}/MOD10A1.{date.strftime('%Y%j')}.h09v03.hdf"
            
            try:
                # Extraire l'albédo pour le glacier
                albedo_value = self.extract_modis_albedo(modis_file, glacier_id)
                albedo_series.append({
                    'date': date,
                    'albedo': albedo_value
                })
            except:
                continue
                
        return pd.DataFrame(albedo_series).set_index('date')
    
    def correlate_deposition_albedo(self, deposition_df, albedo_df, lag_days=3):
        """
        Corréler les dépôts avec les changements d'albédo
        
        Args:
            deposition_df: DataFrame des dépôts cumulatifs
            albedo_df: DataFrame des valeurs d'albédo
            lag_days: Décalage temporel à considérer
        """
        # Fusionner les données
        merged = pd.merge(
            deposition_df.resample('D').mean(),
            albedo_df,
            left_index=True,
            right_index=True,
            how='inner'
        )
        
        # Calculer le changement d'albédo
        merged['albedo_change'] = merged['albedo'].diff()
        
        # Appliquer le décalage temporel
        merged['BC_cumul_lag'] = merged['BC_cumul'].shift(lag_days)
        merged['PM25_cumul_lag'] = merged['PM25_cumul'].shift(lag_days)
        
        # Calculer les corrélations
        correlations = {
            'BC_correlation': merged['albedo_change'].corr(merged['BC_cumul_lag']),
            'PM25_correlation': merged['albedo_change'].corr(merged['PM25_cumul_lag']),
            'BC_pvalue': stats.pearsonr(
                merged['albedo_change'].dropna(), 
                merged['BC_cumul_lag'].dropna()
            )[1],
            'n_observations': len(merged.dropna())
        }
        
        return merged, correlations
    
    def create_glacier_mask(self, data_array, glacier_geom):
        """
        Créer un masque binaire pour un glacier
        """
        from rasterio.features import geometry_mask
        
        # Obtenir les coordonnées de la grille
        lons = data_array.lon.values
        lats = data_array.lat.values
        
        # Créer le masque
        mask = geometry_mask(
            [glacier_geom],
            transform=rasterio.transform.from_bounds(
                lons.min(), lats.min(), lons.max(), lats.max(),
                len(lons), len(lats)
            ),
            invert=True,
            out_shape=(len(lats), len(lons))
        )
        
        return mask
    
    def plot_analysis_results(self, merged_data, glacier_name):
        """
        Visualiser les résultats de l'analyse
        """
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # Dépôt de carbone noir
        axes[0].plot(merged_data.index, merged_data['BC_cumul'], 
                    label='BC cumulatif', color='black')
        axes[0].set_ylabel('Dépôt BC (kg/m²)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Albédo
        axes[1].plot(merged_data.index, merged_data['albedo'], 
                    label='Albédo', color='blue')
        axes[1].set_ylabel('Albédo')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Changement d'albédo vs dépôt BC
        axes[2].scatter(merged_data['BC_cumul_lag'], 
                       merged_data['albedo_change'],
                       alpha=0.6, color='red')
        axes[2].set_xlabel('Dépôt BC cumulatif avec décalage (kg/m²)')
        axes[2].set_ylabel('Changement d\'albédo')
        axes[2].grid(True, alpha=0.3)
        
        # Ligne de régression
        valid_data = merged_data[['BC_cumul_lag', 'albedo_change']].dropna()
        if len(valid_data) > 2:
            z = np.polyfit(valid_data['BC_cumul_lag'], 
                          valid_data['albedo_change'], 1)
            p = np.poly1d(z)
            axes[2].plot(valid_data['BC_cumul_lag'], 
                        p(valid_data['BC_cumul_lag']), 
                        "r--", alpha=0.8)
        
        plt.suptitle(f'Analyse Dépôt-Albédo: {glacier_name}')
        plt.tight_layout()
        return fig

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser l'analyse
    analysis = RAQDPSGlacierAnalysis(
        raqdps_path="/path/to/raqdps/data",
        glacier_shapefile="/path/to/glaciers.shp",
        albedo_data_path="/path/to/modis/data"
    )
    
    # Définir la période d'analyse
    start_date = datetime(2023, 7, 1)
    end_date = datetime(2023, 8, 31)
    
    # Charger les données RAQDPS
    print("Chargement des données RAQDPS...")
    raqdps_data = analysis.load_raqdps_data(start_date, end_date)
    
    # Analyser un glacier spécifique
    glacier_id = "GL001"  # Remplacer par l'ID réel
    
    # Calculer les dépôts cumulatifs
    print("Calcul des dépôts cumulatifs...")
    deposition_df = analysis.calculate_cumulative_deposition(
        raqdps_data, 
        glacier_id, 
        window_days=7
    )
    
    # Charger les données d'albédo
    print("Chargement des données d'albédo...")
    albedo_df = analysis.load_albedo_data(glacier_id, start_date, end_date)
    
    # Corréler dépôts et albédo
    print("Analyse de corrélation...")
    merged_data, correlations = analysis.correlate_deposition_albedo(
        deposition_df, 
        albedo_df, 
        lag_days=3
    )
    
    # Afficher les résultats
    print("\nRésultats de corrélation:")
    print(f"Corrélation BC-Albédo: {correlations['BC_correlation']:.3f} "
          f"(p={correlations['BC_pvalue']:.4f})")
    print(f"Nombre d'observations: {correlations['n_observations']}")
    
    # Créer les graphiques
    fig = analysis.plot_analysis_results(merged_data, "Glacier Test")
    plt.show()