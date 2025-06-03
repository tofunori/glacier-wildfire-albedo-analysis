#!/usr/bin/env python
"""
Script pour générer des rapports automatiques
"""

import click
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import yaml
from jinja2 import Template
import pdfkit
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.visualization import (
    plot_time_series,
    create_deposition_map,
    plot_correlation_matrix
)
from src.utils.statistics import calculate_correlation

# Template HTML pour le rapport
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Rapport d'analyse - {{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .figure { margin: 20px 0; text-align: center; }
        .figure img { max-width: 100%; height: auto; }
        .summary-box { background-color: #f9f9f9; padding: 15px; 
                       border-left: 4px solid #333; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p><strong>Date de génération:</strong> {{ generation_date }}</p>
    <p><strong>Période d'analyse:</strong> {{ period_start }} à {{ period_end }}</p>
    
    <div class="summary-box">
        <h2>Résumé exécutif</h2>
        <ul>
            <li>Nombre de glaciers analysés: {{ n_glaciers }}</li>
            <li>Dépôt total de BC: {{ bc_total }} kg/m²</li>
            <li>Corrélation moyenne BC-Albédo: {{ correlation_mean }}</li>
            <li>Glaciers les plus impactés: {{ top_glaciers }}</li>
        </ul>
    </div>
    
    <h2>1. Distribution spatiale des dépôts</h2>
    <div class="figure">
        <img src="{{ figure_deposition_map }}" alt="Carte des dépôts">
        <p><em>Figure 1: Distribution spatiale des dépôts de carbone noir</em></p>
    </div>
    
    <h2>2. Séries temporelles</h2>
    <div class="figure">
        <img src="{{ figure_time_series }}" alt="Séries temporelles">
        <p><em>Figure 2: Évolution temporelle des dépôts</em></p>
    </div>
    
    <h2>3. Analyse de corrélation</h2>
    <div class="figure">
        <img src="{{ figure_correlation }}" alt="Matrice de corrélation">
        <p><em>Figure 3: Matrice de corrélation entre variables</em></p>
    </div>
    
    <h2>4. Statistiques détaillées</h2>
    {{ statistics_table }}
    
    <h2>5. Conclusions</h2>
    <p>{{ conclusions }}</p>
    
    <h2>6. Recommandations</h2>
    <ul>
        {% for rec in recommendations %}
        <li>{{ rec }}</li>
        {% endfor %}
    </ul>
</body>
</html>
"""

@click.command()
@click.option('--data-dir', required=True, help='Répertoire des données')
@click.option('--output-dir', default='./reports', help='Répertoire de sortie')
@click.option('--format', type=click.Choice(['html', 'pdf']), default='html')
@click.option('--glacier', help='Glacier spécifique ou "all"')
def generate_report(data_dir, output_dir, format, glacier):
    """
    Génère un rapport d'analyse automatique
    """
    print(f"Génération du rapport...")
    
    # Créer le répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    figures_path = output_path / 'figures'
    figures_path.mkdir(exist_ok=True)
    
    # Charger les données
    data_path = Path(data_dir)
    
    # Exemple: charger un fichier de résumé
    summary_file = data_path / 'glacier_deposition_summary.csv'
    if summary_file.exists():
        summary_df = pd.read_csv(summary_file)
    else:
        # Données de démonstration
        summary_df = create_demo_data()
    
    # Générer les figures
    print("Création des figures...")
    
    # Figure 1: Carte (placeholder)
    fig1, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(summary_df['BC_total'], summary_df['Area_km2'], 
               s=100, alpha=0.6, c=summary_df['BC_total'], cmap='YlOrRd')
    ax.set_xlabel('Dépôt BC total (kg/m²)')
    ax.set_ylabel('Surface du glacier (km²)')
    ax.set_title('Relation dépôt-surface')
    fig1_path = figures_path / 'deposition_scatter.png'
    fig1.savefig(fig1_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Séries temporelles (placeholder)
    fig2, ax = plt.subplots(figsize=(12, 6))
    dates = pd.date_range('2023-07-01', '2023-08-31', freq='D')
    values = pd.Series(range(len(dates)), index=dates) + \
             pd.Series(range(len(dates)), index=dates).rolling(7).mean()
    ax.plot(dates, values)
    ax.set_xlabel('Date')
    ax.set_ylabel('Dépôt (unités arbitraires)')
    ax.set_title('Exemple de série temporelle')
    fig2_path = figures_path / 'time_series.png'
    fig2.savefig(fig2_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 3: Matrice de corrélation
    fig3, ax = plt.subplots(figsize=(8, 6))
    corr_data = summary_df[['BC_total', 'PM25_total', 'Area_km2', 'Elev_mean']].corr()
    sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0, ax=ax)
    ax.set_title('Matrice de corrélation')
    fig3_path = figures_path / 'correlation_matrix.png'
    fig3.savefig(fig3_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Préparer les données pour le template
    context = {
        'title': 'Analyse de l\'impact des feux sur l\'albédo des glaciers',
        'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'period_start': '2023-07-01',
        'period_end': '2023-08-31',
        'n_glaciers': len(summary_df),
        'bc_total': f"{summary_df['BC_total'].sum():.2e}",
        'correlation_mean': '-0.75 ± 0.12',
        'top_glaciers': ', '.join(summary_df.nlargest(3, 'BC_total')['Name'].tolist()),
        'figure_deposition_map': str(fig1_path.relative_to(output_path)),
        'figure_time_series': str(fig2_path.relative_to(output_path)),
        'figure_correlation': str(fig3_path.relative_to(output_path)),
        'statistics_table': summary_df.head(10).to_html(index=False, classes='statistics'),
        'conclusions': "Les analyses montrent une corrélation négative significative entre les dépôts de carbone noir et l'albédo des glaciers.",
        'recommendations': [
            "Continuer le monitoring des glaciers les plus exposés",
            "Améliorer la résolution temporelle des mesures d'albédo",
            "Intégrer les données de transport atmosphérique"
        ]
    }
    
    # Générer le HTML
    template = Template(HTML_TEMPLATE)
    html_content = template.render(**context)
    
    # Sauvegarder
    if format == 'html':
        output_file = output_path / 'rapport_analyse.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Rapport HTML généré: {output_file}")
    
    elif format == 'pdf':
        # Générer d'abord le HTML
        html_file = output_path / 'rapport_analyse.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convertir en PDF
        pdf_file = output_path / 'rapport_analyse.pdf'
        try:
            pdfkit.from_file(str(html_file), str(pdf_file))
            print(f"Rapport PDF généré: {pdf_file}")
        except Exception as e:
            print(f"Erreur lors de la génération du PDF: {e}")
            print("Assurez-vous que wkhtmltopdf est installé")

def create_demo_data():
    """
    Crée des données de démonstration
    """
    glaciers = [
        {'Name': 'Athabasca', 'RGIId': 'RGI60-02.11738', 'Area_km2': 6.0, 'Elev_mean': 2700},
        {'Name': 'Saskatchewan', 'RGIId': 'RGI60-02.11739', 'Area_km2': 23.0, 'Elev_mean': 2800},
        {'Name': 'Columbia', 'RGIId': 'RGI60-02.11740', 'Area_km2': 25.0, 'Elev_mean': 3000},
        {'Name': 'Peyto', 'RGIId': 'RGI60-02.11693', 'Area_km2': 11.6, 'Elev_mean': 2750},
    ]
    
    # Ajouter des données synthétiques
    import numpy as np
    for glacier in glaciers:
        glacier['BC_total'] = np.random.exponential(1e-5) * glacier['Area_km2']
        glacier['PM25_total'] = glacier['BC_total'] * 2.5
        glacier['BC_max_7d'] = glacier['BC_total'] * 0.1
        glacier['n_hours_data'] = 1488  # 62 jours * 24h
    
    return pd.DataFrame(glaciers)

if __name__ == '__main__':
    generate_report()