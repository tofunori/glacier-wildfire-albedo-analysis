#!/usr/bin/env python
"""
Script pour traiter les données RAQDPS en batch
"""

import click
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent))

from src.rgi_analysis import RGI_RAQDPS_Analysis
from src.athabasca_glacier import AthabascaGlacierAnalysis

@click.command()
@click.option('--start-date', required=True, help='Date de début (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='Date de fin (YYYY-MM-DD)')
@click.option('--glacier', default='all', help='Glacier spécifique ou "all"')
@click.option('--raqdps-path', required=True, help='Chemin vers les données RAQDPS')
@click.option('--rgi-path', help='Chemin vers le shapefile RGI')
@click.option('--output-dir', default='./results', help='Répertoire de sortie')
@click.option('--min-area', default=1.0, help='Surface minimale des glaciers (km²)')
def main(start_date, end_date, glacier, raqdps_path, rgi_path, output_dir, min_area):
    """
    Traite les données RAQDPS pour l'analyse des dépôts sur les glaciers
    """
    # Parser les dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    print(f"Traitement du {start_date} au {end_date}")
    print(f"Glacier: {glacier}")
    print(f"Données RAQDPS: {raqdps_path}")
    
    if glacier.lower() == 'athabasca':
        # Analyse spécifique pour Athabasca
        print("\nAnalyse du glacier Athabasca...")
        analysis = AthabascaGlacierAnalysis(
            raqdps_path=raqdps_path,
            output_dir=f"{output_dir}/athabasca"
        )
        
        df = analysis.analyze_period(start, end)
        if df is not None:
            summary = analysis.create_summary_report(df)
            print("\nRésumé:")
            print(summary)
            
            # Créer les visualisations
            fig = analysis.plot_seasonal_analysis(df)
            fig.savefig(f"{output_dir}/athabasca/seasonal_analysis.png", dpi=300)
            
    elif glacier.lower() == 'all' and rgi_path:
        # Analyse régionale avec RGI
        print("\nAnalyse régionale de tous les glaciers...")
        analysis = RGI_RAQDPS_Analysis(
            rgi_shapefile=rgi_path,
            raqdps_path=raqdps_path,
            region='02'
        )
        
        # Filtrer par surface
        analysis.filter_glaciers_by_criteria(min_area=min_area)
        
        # Lancer l'analyse
        summary = analysis.batch_analysis_pipeline(
            start, end, output_dir
        )
        
        # Afficher le top 10
        print("\nTop 10 glaciers par dépôt de BC:")
        top10 = summary.nlargest(10, 'BC_total')
        print(top10[['RGIId', 'Name', 'Area_km2', 'BC_total']])
        
        # Créer la carte
        fig = analysis.plot_regional_deposition_map(summary, 'BC_total')
        fig.savefig(f"{output_dir}/regional_deposition_map.png", dpi=300)
        
    else:
        print(f"Glacier '{glacier}' non reconnu. Utiliser 'athabasca' ou 'all'")
        return
    
    print(f"\nTraitement terminé. Résultats dans: {output_dir}")

if __name__ == '__main__':
    main()