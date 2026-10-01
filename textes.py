"""
Textes éditoriaux (La Une, l'essentiel des matchs...).
Ils viennent de data/textes_journee.xlsx (généré à l'étape 2) et ne s'affichent
QUE si le statut est 'OK' : aucun texte non relu n'est publié.
Colonnes : cible | texte_propose | texte_valide | statut
Cibles : 'une:J3', 'match:J3:GARGES' (journée + club à domicile).
"""
import pandas as pd
import config as C


def charger_textes() -> dict:
    if not C.FICHIER_TEXTES.exists():
        return {}
    df = pd.read_excel(C.FICHIER_TEXTES)
    df = df[df.statut.astype(str).str.strip().str.upper() == "OK"]
    txt = df.texte_valide.fillna(df.texte_propose)
    return dict(zip(df.cible.astype(str).str.strip(), txt.astype(str).str.strip()))
