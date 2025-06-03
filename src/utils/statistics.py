"""
Fonctions utilitaires pour les analyses statistiques
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import r2_score
from statsmodels.tsa.stattools import acf, pacf
import statsmodels.api as sm

def calculate_correlation(x, y, method='pearson'):
    """
    Calculer la corrélation entre deux variables
    
    Args:
        x, y: Séries de données
        method: 'pearson', 'spearman', ou 'kendall'
    
    Returns:
        dict: {correlation, p_value, confidence_interval}
    """
    # Enlever les NaN
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return {'correlation': np.nan, 'p_value': np.nan, 'confidence_interval': (np.nan, np.nan)}
    
    if method == 'pearson':
        corr, p_value = stats.pearsonr(x_clean, y_clean)
    elif method == 'spearman':
        corr, p_value = stats.spearmanr(x_clean, y_clean)
    elif method == 'kendall':
        corr, p_value = stats.kendalltau(x_clean, y_clean)
    else:
        raise ValueError(f"Méthode {method} non supportée")
    
    # Intervalle de confiance (95%) pour Pearson
    if method == 'pearson' and len(x_clean) > 3:
        z = np.arctanh(corr)
        se = 1 / np.sqrt(len(x_clean) - 3)
        z_crit = 1.96  # 95% CI
        ci_lower = np.tanh(z - z_crit * se)
        ci_upper = np.tanh(z + z_crit * se)
    else:
        ci_lower, ci_upper = np.nan, np.nan
    
    return {
        'correlation': corr,
        'p_value': p_value,
        'confidence_interval': (ci_lower, ci_upper),
        'n_observations': len(x_clean)
    }

def compute_lag_analysis(x, y, max_lag=10, method='correlation'):
    """
    Analyser la corrélation avec différents décalages temporels
    
    Args:
        x: Série temporelle (cause)
        y: Série temporelle (effet)
        max_lag: Décalage maximal à tester
        method: 'correlation' ou 'regression'
    
    Returns:
        DataFrame avec les résultats pour chaque lag
    """
    results = []
    
    for lag in range(0, max_lag + 1):
        if lag == 0:
            x_lagged = x
            y_current = y
        else:
            x_lagged = x[:-lag]
            y_current = y[lag:]
        
        if method == 'correlation':
            result = calculate_correlation(x_lagged, y_current)
            results.append({
                'lag': lag,
                'correlation': result['correlation'],
                'p_value': result['p_value'],
                'n_obs': result['n_observations']
            })
        
        elif method == 'regression':
            # Régression linéaire simple
            mask = ~(np.isnan(x_lagged) | np.isnan(y_current))
            if mask.sum() > 2:
                X = sm.add_constant(x_lagged[mask])
                model = sm.OLS(y_current[mask], X).fit()
                
                results.append({
                    'lag': lag,
                    'slope': model.params[1],
                    'intercept': model.params[0],
                    'r_squared': model.rsquared,
                    'p_value': model.pvalues[1],
                    'n_obs': len(x_lagged[mask])
                })
    
    return pd.DataFrame(results)

def calculate_trends(df, variables, window_sizes=[7, 30, 90]):
    """
    Calculer les tendances à différentes échelles temporelles
    
    Args:
        df: DataFrame avec index temporel
        variables: Liste des variables à analyser
        window_sizes: Tailles des fenêtres en jours
    
    Returns:
        DataFrame avec les tendances
    """
    trends = {}
    
    for var in variables:
        if var in df.columns:
            trends[f'{var}_original'] = df[var]
            
            for window in window_sizes:
                # Moyenne mobile
                trends[f'{var}_ma{window}d'] = df[var].rolling(f'{window}D').mean()
                
                # Tendance linéaire sur la fenêtre
                def calc_trend(x):
                    if len(x.dropna()) < 2:
                        return np.nan
                    idx = np.arange(len(x))
                    mask = ~np.isnan(x)
                    if mask.sum() < 2:
                        return np.nan
                    z = np.polyfit(idx[mask], x[mask], 1)
                    return z[0]  # Pente
                
                trends[f'{var}_trend{window}d'] = df[var].rolling(f'{window}D').apply(calc_trend)
    
    return pd.DataFrame(trends, index=df.index)

def compute_extreme_statistics(data, threshold_percentiles=[90, 95, 99]):
    """
    Calculer les statistiques d'événements extrêmes
    
    Args:
        data: Série de données
        threshold_percentiles: Percentiles pour définir les extrêmes
    
    Returns:
        dict avec les statistiques
    """
    results = {
        'mean': np.nanmean(data),
        'std': np.nanstd(data),
        'min': np.nanmin(data),
        'max': np.nanmax(data)
    }
    
    for p in threshold_percentiles:
        threshold = np.nanpercentile(data, p)
        extreme_mask = data > threshold
        
        results[f'p{p}_threshold'] = threshold
        results[f'p{p}_count'] = extreme_mask.sum()
        results[f'p{p}_frequency'] = extreme_mask.mean()
        
        # Durée moyenne des événements
        if isinstance(data, pd.Series):
            # Identifier les événements consécutifs
            events = (extreme_mask != extreme_mask.shift()).cumsum()
            event_durations = extreme_mask.groupby(events).sum()
            event_durations = event_durations[event_durations > 0]
            
            if len(event_durations) > 0:
                results[f'p{p}_mean_duration'] = event_durations.mean()
                results[f'p{p}_max_duration'] = event_durations.max()
            else:
                results[f'p{p}_mean_duration'] = 0
                results[f'p{p}_max_duration'] = 0
    
    return results

def perform_regression_analysis(X, y, include_interaction=False):
    """
    Effectuer une analyse de régression multiple
    
    Args:
        X: DataFrame des variables explicatives
        y: Variable dépendante
        include_interaction: Inclure les termes d'interaction
    
    Returns:
        dict avec les résultats de régression
    """
    # Préparer les données
    mask = ~(X.isnull().any(axis=1) | y.isnull())
    X_clean = X[mask]
    y_clean = y[mask]
    
    if len(X_clean) < len(X.columns) + 1:
        return {'error': 'Pas assez de données pour la régression'}
    
    # Ajouter la constante
    X_with_const = sm.add_constant(X_clean)
    
    # Régression de base
    model = sm.OLS(y_clean, X_with_const).fit()
    
    results = {
        'coefficients': model.params.to_dict(),
        'p_values': model.pvalues.to_dict(),
        'r_squared': model.rsquared,
        'r_squared_adj': model.rsquared_adj,
        'aic': model.aic,
        'bic': model.bic,
        'f_statistic': model.fvalue,
        'f_pvalue': model.f_pvalue,
        'n_observations': model.nobs
    }
    
    # Diagnostics
    results['durbin_watson'] = sm.stats.durbin_watson(model.resid)
    
    # VIF pour la multicolinéarité
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X_with_const.columns
    vif_data["VIF"] = [variance_inflation_factor(X_with_const.values, i) 
                       for i in range(X_with_const.shape[1])]
    results['vif'] = vif_data.to_dict('records')
    
    # Termes d'interaction si demandé
    if include_interaction and X.shape[1] > 1:
        # Ajouter les interactions deux à deux
        X_interact = X_clean.copy()
        for i, col1 in enumerate(X.columns[:-1]):
            for col2 in X.columns[i+1:]:
                X_interact[f'{col1}*{col2}'] = X_clean[col1] * X_clean[col2]
        
        X_interact_const = sm.add_constant(X_interact)
        model_interact = sm.OLS(y_clean, X_interact_const).fit()
        
        results['interaction_model'] = {
            'r_squared': model_interact.rsquared,
            'significant_interactions': [
                col for col, p in model_interact.pvalues.items() 
                if '*' in col and p < 0.05
            ]
        }
    
    return results

def calculate_autocorrelation(series, lags=40):
    """
    Calculer l'autocorrélation et l'autocorrélation partielle
    
    Args:
        series: Série temporelle
        lags: Nombre de lags à calculer
    
    Returns:
        dict avec ACF et PACF
    """
    # Enlever les NaN
    series_clean = series.dropna()
    
    if len(series_clean) < lags:
        lags = len(series_clean) // 4
    
    # Calculer ACF et PACF
    acf_values = acf(series_clean, nlags=lags)
    pacf_values = pacf(series_clean, nlags=lags)
    
    # Intervalles de confiance
    n = len(series_clean)
    ci = 1.96 / np.sqrt(n)
    
    return {
        'acf': acf_values,
        'pacf': pacf_values,
        'confidence_interval': ci,
        'lags': np.arange(0, lags + 1)
    }