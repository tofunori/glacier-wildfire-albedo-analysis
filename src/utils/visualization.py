"""
Fonctions utilitaires pour la visualisation
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def plot_time_series(df, variables, title=None, figsize=(12, 6)):
    """
    Créer un graphique de séries temporelles
    
    Args:
        df: DataFrame avec index temporel
        variables: Liste des variables à tracer
        title: Titre du graphique
        figsize: Taille de la figure
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Couleurs pour différentes variables
    colors = plt.cm.tab10(np.linspace(0, 1, len(variables)))
    
    for i, var in enumerate(variables):
        if var in df.columns:
            ax.plot(df.index, df[var], label=var, color=colors[i], linewidth=2)
    
    # Mise en forme
    ax.set_xlabel('Date')
    ax.set_ylabel('Valeur')
    if title:
        ax.set_title(title)
    
    # Format des dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def create_deposition_map(glaciers_gdf, deposition_data, variable='BC_total', 
                         figsize=(14, 10), cmap='YlOrRd'):
    """
    Créer une carte des dépôts sur les glaciers
    
    Args:
        glaciers_gdf: GeoDataFrame des glaciers
        deposition_data: DataFrame avec les données de dépôt
        variable: Variable à cartographier
        figsize: Taille de la figure
        cmap: Palette de couleurs
    
    Returns:
        matplotlib.figure.Figure
    """
    # Fusionner les données
    glaciers_with_data = glaciers_gdf.merge(
        deposition_data[['RGIId', variable]], 
        on='RGIId', 
        how='left'
    )
    
    # Créer la figure avec projection
    fig = plt.figure(figsize=figsize)
    ax = plt.axes(projection=ccrs.AlbersEqualArea(
        central_longitude=-120, 
        central_latitude=50
    ))
    
    # Ajouter les caractéristiques géographiques
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.STATES, linewidth=0.5)
    ax.add_feature(cfeature.RIVERS, linewidth=0.5, edgecolor='blue')
    
    # Tracer les glaciers
    glaciers_with_data.plot(
        column=variable,
        ax=ax,
        transform=ccrs.PlateCarree(),
        legend=True,
        cmap=cmap,
        legend_kwds={
            'label': f'{variable} (kg/m²)',
            'orientation': 'vertical',
            'shrink': 0.7
        },
        missing_kwds={
            'color': 'gray',
            'label': 'Pas de données'
        }
    )
    
    # Limites de la carte
    ax.set_extent([-130, -110, 48, 60], crs=ccrs.PlateCarree())
    
    # Grille
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    
    # Titre
    ax.set_title(f'Dépôt de {variable} sur les glaciers de l\'Ouest Canadien', 
                fontsize=16, pad=20)
    
    return fig

def plot_correlation_matrix(df, variables=None, figsize=(10, 8)):
    """
    Créer une matrice de corrélation
    
    Args:
        df: DataFrame avec les données
        variables: Liste des variables à inclure
        figsize: Taille de la figure
    
    Returns:
        matplotlib.figure.Figure
    """
    if variables is None:
        variables = df.select_dtypes(include=[np.number]).columns
    
    # Calculer la matrice de corrélation
    corr_matrix = df[variables].corr()
    
    # Créer la figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Créer le heatmap
    sns.heatmap(corr_matrix, 
                annot=True, 
                fmt='.2f',
                cmap='coolwarm', 
                center=0,
                square=True,
                linewidths=1,
                cbar_kws={"shrink": .8},
                ax=ax)
    
    ax.set_title('Matrice de corrélation', fontsize=14, pad=20)
    
    return fig

def plot_wind_rose(wind_speed, wind_direction, figsize=(10, 10), bins=16):
    """
    Créer une rose des vents
    
    Args:
        wind_speed: Vitesse du vent (m/s)
        wind_direction: Direction du vent (degrés)
        figsize: Taille de la figure
        bins: Nombre de secteurs de direction
    
    Returns:
        matplotlib.figure.Figure
    """
    # Créer la figure en coordonnées polaires
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='polar')
    
    # Définir les bins de direction
    theta_bins = np.linspace(0, 2*np.pi, bins+1)
    theta_labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                   'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    # Convertir la direction en radians
    wind_dir_rad = np.deg2rad(wind_direction)
    
    # Créer l'histogramme 2D
    speed_bins = [0, 2, 4, 6, 8, 10, 12]
    colors = plt.cm.viridis(np.linspace(0, 1, len(speed_bins)-1))
    
    for i in range(len(speed_bins)-1):
        mask = (wind_speed >= speed_bins[i]) & (wind_speed < speed_bins[i+1])
        theta = wind_dir_rad[mask]
        
        counts, _ = np.histogram(theta, bins=theta_bins)
        counts = counts / counts.sum() * 100  # Convertir en pourcentage
        
        # Tracer les barres
        width = 2 * np.pi / bins
        theta_centers = (theta_bins[:-1] + theta_bins[1:]) / 2
        
        ax.bar(theta_centers, counts, width=width, bottom=0, 
               color=colors[i], alpha=0.8, 
               label=f'{speed_bins[i]}-{speed_bins[i+1]} m/s')
    
    # Configuration
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.arange(0, 360, 22.5), theta_labels)
    ax.set_xlabel('Direction du vent')
    ax.set_ylabel('Fréquence (%)')
    ax.set_title('Rose des vents', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    
    return fig

def plot_deposition_vs_distance(distance_to_fire, deposition, figsize=(10, 6)):
    """
    Tracer le dépôt en fonction de la distance aux feux
    
    Args:
        distance_to_fire: Distance aux feux (km)
        deposition: Valeurs de dépôt
        figsize: Taille de la figure
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Scatter plot
    scatter = ax.scatter(distance_to_fire, deposition, 
                        c=deposition, cmap='YlOrRd', 
                        alpha=0.6, s=50)
    
    # Ajouter une courbe de tendance
    z = np.polyfit(distance_to_fire, deposition, 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(distance_to_fire.min(), distance_to_fire.max(), 100)
    ax.plot(x_smooth, p(x_smooth), 'r--', linewidth=2, label='Tendance')
    
    # Mise en forme
    ax.set_xlabel('Distance aux feux (km)')
    ax.set_ylabel('Dépôt (kg/m²)')
    ax.set_title('Dépôt en fonction de la distance aux feux')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Dépôt (kg/m²)')
    
    return fig

def create_seasonal_comparison(data_dict, variable='BC_dep', figsize=(14, 8)):
    """
    Créer une comparaison saisonnière
    
    Args:
        data_dict: Dictionnaire {saison: DataFrame}
        variable: Variable à comparer
        figsize: Taille de la figure
    
    Returns:
        matplotlib.figure.Figure
    """
    n_seasons = len(data_dict)
    fig, axes = plt.subplots(1, n_seasons, figsize=figsize, sharey=True)
    
    if n_seasons == 1:
        axes = [axes]
    
    for i, (season, df) in enumerate(data_dict.items()):
        ax = axes[i]
        
        # Calculer les moyennes journalières
        daily_mean = df.groupby(df.index.date)[variable].mean()
        
        # Box plot par mois
        df['month'] = df.index.month
        df.boxplot(column=variable, by='month', ax=ax)
        
        ax.set_title(f'{season}')
        ax.set_xlabel('Mois')
        if i == 0:
            ax.set_ylabel(f'{variable} (kg/m²)')
        
        # Nettoyer le titre automatique du boxplot
        ax.set_title(season)
    
    plt.suptitle('Comparaison saisonnière des dépôts', fontsize=16)
    plt.tight_layout()
    
    return fig