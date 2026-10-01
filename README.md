# D1 Futsal · site et appli

## Structure
- `config.py` : chemins, liste des origines, noms et abréviations des clubs.
- `data.py` : lecture des 3 fichiers, rattachement des joueurs (id_joueur), calcul des stats.
- `controles.py` : contrôles BLOQUANT / ALERTE.
- `verifier.py` : contrôle + `export_verification.xlsx`.
- `textes.py` : textes éditoriaux validés (data/textes_journee.xlsx, statut OK uniquement).
- `app_mobile.py` + `ui/` : appli mobile (charte des rapports).
- `assets/clubs/<CLUB>.png` (logos), `assets/joueurs/<id_joueur>.jpg` (photos) : facultatifs.
- `tests/test_routes.py` : ouvre toutes les pages de l'appli et signale les erreurs.

## Routine après chaque journée
1. Remplacer les fichiers dans `data/` (mêmes noms).
2. `python verifier.py` : zéro BLOQUANT avant d'aller plus loin.
3. `streamlit run app_mobile.py` pour vérifier en local.
4. Push GitHub : l'appli en ligne se met à jour seule.

Si un contrôle BLOQUANT subsiste en ligne, l'appli affiche « mise à jour en cours » au lieu de données fausses.
Page privée de contrôle : `?page=controle&cle=<CLE_ADMIN>`.

## Installation
`pip install -r requirements.txt`
