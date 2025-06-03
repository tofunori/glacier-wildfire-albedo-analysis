import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import seaborn as sns
from scipy import stats
import os

class AthabascaGlacierAnalysis:
    """
    Analyse spécifique pour le glacier Athabasca
    Champ de glace Columbia, Alberta, Canada
    """
    
    def __init__(self, raqdps_path, output_dir='./athabasca_results'):
        """
        Initialisation pour le glacier Athabasca
        """
        self.raqdps_path = raqdps_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Coordonnées du glacier Athabasca
        # RGI ID: RGI60-02.11738 (approximatif)
        self.glacier_info = {
            'name': 'Athabasca Glacier',
            'rgi_id': 'RGI60-02.11738',
            'lat_center': 52.185,
            'lon_center': -117.252,
            'area_km2': 6.0,  # Surface approximative actuelle
            'elevation_mean': 2700,  # m
            'elevation_terminus': 2000,  # m
            'aspect': 'NE'  # Orientation principale
        }
        
        # Définir le polygone approximatif du glacier
        # Points basés sur les contours connus du glacier Athabasca
        self.glacier_polygon = Polygon([
            (-117.270, 52.170),  # SW
            (-117.240, 52.170),  # SE
            (-117.235, 52.200),  # NE
            (-117.265, 52.200),  # NW
            (-117.270, 52.170)   # Fermer le polygone
        ])
        
        # Créer un GeoDataFrame pour le glacier
        self.glacier_gdf = gpd.GeoDataFrame(
            [self.glacier_info], 
            geometry=[self.glacier_polygon],
            crs='EPSG:4326'
        )
        
        print(f"Analyse initialisée pour le glacier Athabasca")
        print(f"Surface: {self.glacier_info['area_km2']} km²")
        print(f"Coordonnées centre: {self.glacier_info['lat_center']}°N, {self.glacier_info['lon_center']}°W")
        
    def load_raqdps_hourly(self, date_time):
        """
        Charger les données RAQDPS pour une heure spécifique
        """
        filename = f"{self.raqdps_path}/{date_time.strftime('%Y%m%d%H')}_000.nc"
        
        try:
            ds = xr.open_dataset(filename)
            return ds
        except FileNotFoundError:
            print(f"Fichier non trouvé: {filename}")
            return None
            
    def extract_glacier_data(self, raqdps_ds, variables=['BC_dep', 'PM2.5_dep']):
        """
        Extraire les données pour le glacier Athabasca
        """
        if raqdps_ds is None:
            return None
            
        # Définir la boîte englobante du glacier
        lon_min, lat_min, lon_max, lat_max = self.glacier_polygon.bounds
        
        # Ajouter un buffer pour s'assurer de capturer toutes les cellules
        buffer = 0.1  # degrés
        roi = raqdps_ds.sel(
            lat=slice(lat_min - buffer, lat_max + buffer),
            lon=slice(lon_min - buffer, lon_max + buffer)
        )
        
        # Extraire les valeurs pour chaque variable
        data = {'time': pd.Timestamp(raqdps_ds.time.values[0])}
        
        for var in variables:
            if var in roi:
                # Calculer les statistiques sur la région
                data[f'{var}_mean'] = float(roi[var].mean().values)
                data[f'{var}_max'] = float(roi[var].max().values)
                data[f'{var}_sum'] = float(roi[var].sum().values)
                
                # Valeur au point central
                try:
                    data[f'{var}_center'] = float(
                        roi[var].sel(
                            lat=self.glacier_info['lat_center'],
                            lon=self.glacier_info['lon_center'],
                            method='nearest'
                        ).values
                    )
                except:
                    data[f'{var}_center'] = np.nan
                    
        # Ajouter les variables météo si disponibles
        meteo_vars = ['t_2m', 'rh_2m', 'ws_10m', 'precip', 'pres_sfc']
        for var in meteo_vars:
            if var in roi:
                data[var] = float(
                    roi[var].sel(
                        lat=self.glacier_info['lat_center'],
                        lon=self.glacier_info['lon_center'],
                        method='nearest'
                    ).values
                )
                
        # Direction du vent
        if 'u_10m' in roi and 'v_10m' in roi:
            u = float(roi['u_10m'].sel(
                lat=self.glacier_info['lat_center'],
                lon=self.glacier_info['lon_center'],
                method='nearest'
            ).values)
            v = float(roi['v_10m'].sel(
                lat=self.glacier_info['lat_center'],
                lon=self.glacier_info['lon_center'],
                method='nearest'
            ).values)
            
            data['wind_speed'] = np.sqrt(u**2 + v**2)
            data['wind_dir'] = np.arctan2(v, u) * 180 / np.pi
            
        return data
    
    def analyze_period(self, start_date, end_date, 
                      variables=['BC_dep', 'PM2.5_dep', 'PM10_dep']):
        """
        Analyser une période complète
        """
        print(f"\nAnalyse du {start_date} au {end_date}")
        
        # Collecter les données horaires
        hourly_data = []
        current = start_date
        
        while current <= end_date:
            ds = self.load_raqdps_hourly(current)
            if ds is not None:
                data = self.extract_glacier_data(ds, variables)
                if data:
                    hourly_data.append(data)
            
            current += timedelta(hours=1)
            
            # Afficher la progression
            if current.hour == 0:
                print(f"Traitement: {current.strftime('%Y-%m-%d')}")
        
        # Convertir en DataFrame
        df = pd.DataFrame(hourly_data)
        if len(df) > 0:
            df.set_index('time', inplace=True)
            
            # Calculer les dépôts cumulatifs
            for var in variables:
                if f'{var}_sum' in df.columns:
                    # Cumulatif sur différentes fenêtres
                    df[f'{var}_cumul_24h'] = df[f'{var}_sum'].rolling('24H').sum()
                    df[f'{var}_cumul_7d'] = df[f'{var}_sum'].rolling('7D').sum()
                    df[f'{var}_cumul_total'] = df[f'{var}_sum'].cumsum()
            
            # Sauvegarder les données
            output_file = f"{self.output_dir}/athabasca_raqdps_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            df.to_csv(output_file)
            print(f"Données sauvegardées: {output_file}")
            
            return df
        else:
            print("Aucune donnée extraite pour cette période")
            return None
    
    def analyze_fire_events(self, df, fire_dates):
        """
        Analyser l'impact d'événements de feux spécifiques
        
        Args:
            df: DataFrame avec les données RAQDPS
            fire_dates: Liste de dates d'événements de feux majeurs
        """
        fig, axes = plt.subplots(len(fire_dates), 1, figsize=(14, 4*len(fire_dates)))
        if len(fire_dates) == 1:
            axes = [axes]
        
        for i, fire_date in enumerate(fire_dates):
            # Fenêtre d'analyse: 3 jours avant à 10 jours après
            window_start = fire_date - timedelta(days=3)
            window_end = fire_date + timedelta(days=10)
            
            # Extraire la fenêtre
            window_df = df[window_start:window_end].copy()
            
            if len(window_df) > 0:
                ax = axes[i]
                
                # Graphique double axe
                ax2 = ax.twinx()
                
                # Dépôt de BC (axe gauche)
                ax.plot(window_df.index, window_df['BC_dep_sum'], 
                       'k-', label='BC horaire', alpha=0.5)
                ax.plot(window_df.index, window_df['BC_dep_cumul_24h'], 
                       'k-', label='BC 24h', linewidth=2)
                
                # PM2.5 (axe droit)
                ax2.plot(window_df.index, window_df['PM2.5_dep_cumul_24h'], 
                        'r-', label='PM2.5 24h', linewidth=2)
                
                # Marquer l'événement de feu
                ax.axvline(fire_date, color='orange', linestyle='--', 
                          linewidth=2, label='Événement de feu')
                
                # Conditions météo (précipitations)
                if 'precip' in window_df.columns:
                    ax_precip = ax.twinx()
                    ax_precip.spines['right'].set_position(('outward', 60))
                    ax_precip.bar(window_df.index, window_df['precip'], 
                                 alpha=0.3, color='blue', width=0.04)
                    ax_precip.set_ylabel('Précip. (mm/h)', color='blue')
                    ax_precip.tick_params(axis='y', labelcolor='blue')
                
                # Mise en forme
                ax.set_xlabel('Date')
                ax.set_ylabel('Dépôt BC (kg/m²)', color='black')
                ax2.set_ylabel('Dépôt PM2.5 (kg/m²)', color='red')
                ax.tick_params(axis='y', labelcolor='black')
                ax2.tick_params(axis='y', labelcolor='red')
                
                ax.set_title(f'Impact de l\'événement de feu du {fire_date.strftime("%Y-%m-%d")}')
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left')
                ax2.legend(loc='upper right')
                
                # Format des dates
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator())
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        return fig
    
    def create_summary_report(self, df):
        """
        Créer un rapport résumé pour le glacier Athabasca
        """
        report = {
            'Glacier': self.glacier_info['name'],
            'Période': f"{df.index[0].strftime('%Y-%m-%d')} à {df.index[-1].strftime('%Y-%m-%d')}",
            'Nombre d\'heures analysées': len(df),
            'Données manquantes (%)': (1 - len(df) / ((df.index[-1] - df.index[0]).total_seconds() / 3600)) * 100
        }
        
        # Statistiques de dépôt
        for var in ['BC_dep', 'PM2.5_dep', 'PM10_dep']:
            if f'{var}_sum' in df.columns:
                report[f'{var}_total_kg'] = df[f'{var}_sum'].sum()
                report[f'{var}_max_horaire'] = df[f'{var}_sum'].max()
                report[f'{var}_max_24h'] = df[f'{var}_cumul_24h'].max() if f'{var}_cumul_24h' in df else np.nan
                report[f'{var}_max_7j'] = df[f'{var}_cumul_7d'].max() if f'{var}_cumul_7d' in df else np.nan
        
        # Conditions météo moyennes
        if 't_2m' in df.columns:
            report['Température_moy_C'] = df['t_2m'].mean() - 273.15  # Convertir de K à °C
            report['Précip_totale_mm'] = df['precip'].sum() if 'precip' in df else np.nan
            report['Vent_moy_m/s'] = df['wind_speed'].mean() if 'wind_speed' in df else np.nan
        
        # Créer un tableau de résumé
        summary_df = pd.DataFrame([report]).T
        summary_df.columns = ['Valeur']
        
        # Sauvegarder
        summary_file = f"{self.output_dir}/athabasca_summary.csv"
        summary_df.to_csv(summary_file)
        
        return summary_df
    
    def plot_seasonal_analysis(self, df):
        """
        Analyse saisonnière des dépôts
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Série temporelle complète
        ax = axes[0, 0]
        ax.plot(df.index, df['BC_dep_cumul_total'], 'k-', label='BC cumulatif')
        ax.set_ylabel('Dépôt BC cumulatif (kg/m²)')
        ax.set_title('Accumulation totale de carbone noir')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 2. Cycle journalier moyen
        ax = axes[0, 1]
        hourly_mean = df.groupby(df.index.hour)['BC_dep_mean'].mean()
        ax.plot(hourly_mean.index, hourly_mean.values, 'ko-')
        ax.set_xlabel('Heure (UTC)')
        ax.set_ylabel('Dépôt BC moyen (kg/m²/h)')
        ax.set_title('Cycle journalier moyen')
        ax.grid(True, alpha=0.3)
        
        # 3. Distribution des vents
        if 'wind_dir' in df.columns:
            ax = axes[1, 0]
            wind_rose = ax.hist(df['wind_dir'].dropna(), bins=16, density=True, alpha=0.7)
            ax.set_xlabel('Direction du vent (degrés)')
            ax.set_ylabel('Fréquence')
            ax.set_title('Rose des vents')
            ax.grid(True, alpha=0.3)
        
        # 4. Corrélation dépôt vs météo
        ax = axes[1, 1]
        if 'wind_speed' in df.columns and 'BC_dep_mean' in df.columns:
            valid_data = df[['wind_speed', 'BC_dep_mean']].dropna()
            ax.scatter(valid_data['wind_speed'], valid_data['BC_dep_mean'], 
                      alpha=0.5, s=10)
            ax.set_xlabel('Vitesse du vent (m/s)')
            ax.set_ylabel('Dépôt BC (kg/m²/h)')
            ax.set_title('Dépôt vs vitesse du vent')
            ax.grid(True, alpha=0.3)
            
            # Ajouter la corrélation
            corr = valid_data.corr().iloc[0, 1]
            ax.text(0.05, 0.95, f'r = {corr:.3f}', 
                   transform=ax.transAxes, va='top')
        
        plt.suptitle(f'Analyse saisonnière - Glacier Athabasca\n{df.index[0].strftime("%Y-%m-%d")} à {df.index[-1].strftime("%Y-%m-%d")}')
        plt.tight_layout()
        
        return fig

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser l'analyse
    analysis = AthabascaGlacierAnalysis(
        raqdps_path="/path/to/raqdps/data",
        output_dir="./athabasca_results"
    )
    
    # Analyser la saison des feux 2023
    start_date = datetime(2023, 7, 1, 0, 0)
    end_date = datetime(2023, 8, 31, 23, 0)
    
    print("Extraction des données RAQDPS...")
    df = analysis.analyze_period(start_date, end_date)
    
    if df is not None:
        # Créer le rapport de synthèse
        print("\nCréation du rapport de synthèse...")
        summary = analysis.create_summary_report(df)
        print("\nRésumé:")
        print(summary)
        
        # Analyser des événements de feux spécifiques
        # Dates d'événements de feux majeurs près du glacier (à adapter)
        fire_events = [
            datetime(2023, 7, 15),  # Exemple: feu majeur mi-juillet
            datetime(2023, 8, 5),   # Exemple: feu début août
        ]
        
        print("\nAnalyse des événements de feux...")
        fig_events = analysis.analyze_fire_events(df, fire_events)
        plt.savefig(f"{analysis.output_dir}/fire_events_impact.png", 
                   dpi=300, bbox_inches='tight')
        
        # Analyse saisonnière
        print("\nCréation des graphiques d'analyse saisonnière...")
        fig_seasonal = analysis.plot_seasonal_analysis(df)
        plt.savefig(f"{analysis.output_dir}/seasonal_analysis.png", 
                   dpi=300, bbox_inches='tight')
        
        print(f"\nAnalyse terminée. Résultats dans: {analysis.output_dir}")