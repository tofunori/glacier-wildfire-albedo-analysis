# Guide de contribution

Merci de votre intérêt pour contribuer à ce projet ! Ce guide vous aidera à démarrer.

## Comment contribuer

### 1. Fork et clone

1. Fork le repository sur GitHub
2. Clone votre fork localement :
```bash
git clone https://github.com/votre-username/glacier-wildfire-albedo-analysis.git
cd glacier-wildfire-albedo-analysis
```

### 2. Créer une branche

Créez une branche pour votre fonctionnalité ou correction :
```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
# ou
git checkout -b fix/correction-bug
```

### 3. Installer l'environnement de développement

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
pip install pytest pytest-cov black flake8
```

### 4. Faire vos modifications

- Suivez le style de code existant
- Ajoutez des tests pour les nouvelles fonctionnalités
- Mettez à jour la documentation si nécessaire

### 5. Vérifier votre code

```bash
# Formater le code
black src/ tests/

# Vérifier le style
flake8 src/ tests/

# Exécuter les tests
pytest tests/
```

### 6. Commit et push

```bash
git add .
git commit -m "Description claire de vos changements"
git push origin feature/ma-nouvelle-fonctionnalite
```

### 7. Créer une Pull Request

1. Allez sur GitHub
2. Créez une Pull Request depuis votre branche
3. Décrivez vos changements en détail
4. Attendez la revue de code

## Standards de code

### Style Python

- Suivre PEP 8
- Utiliser Black pour le formatage
- Docstrings pour toutes les fonctions publiques
- Type hints quand c'est approprié

### Exemple de docstring

```python
def calculate_deposition(data: xr.Dataset, glacier_id: str) -> pd.DataFrame:
    """
    Calcule les dépôts pour un glacier spécifique.
    
    Args:
        data: Dataset xarray avec les champs de dépôt
        glacier_id: Identifiant RGI du glacier
    
    Returns:
        DataFrame avec les séries temporelles de dépôt
    
    Raises:
        ValueError: Si le glacier_id n'est pas trouvé
    """
    # Implementation
    pass
```

### Tests

- Écrire des tests pour toute nouvelle fonctionnalité
- Maintenir la couverture de tests > 80%
- Utiliser pytest et les fixtures

### Commits

- Messages clairs et descriptifs
- Un commit = un changement logique
- Format : `type: description`

Exemples :
- `feat: ajouter support pour Sentinel-2`
- `fix: corriger le calcul des dépôts cumulatifs`
- `docs: mettre à jour le guide d'installation`
- `test: ajouter tests pour RGI_RAQDPS_Analysis`

## Signaler des problèmes

### Bugs

Pour signaler un bug, créez une issue avec :
- Description claire du problème
- Étapes pour reproduire
- Comportement attendu vs observé
- Version de Python et des dépendances
- Logs d'erreur complets

### Demandes de fonctionnalités

Pour proposer une nouvelle fonctionnalité :
- Décrire le cas d'usage
- Expliquer pourquoi c'est utile
- Proposer une implémentation si possible

## Questions ?

N'hésitez pas à :
- Ouvrir une issue pour des questions
- Demander de l'aide dans les discussions
- Contacter les mainteneurs

Merci de contribuer ! 🎉