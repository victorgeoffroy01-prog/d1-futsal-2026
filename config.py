"""Paramètres du site D1 Futsal : chemins, listes fermées, constantes."""
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
FICHIER_BUTS = DATA_DIR / "But_D1_26_27.xlsx"
FICHIER_PASSES = DATA_DIR / "PasseD_26_27.xlsx"
FICHIER_FICHES = DATA_DIR / "D1_Fiches_Clubs_Joueurs_26_27.xlsx"

SAISON = "2026-2027"
NB_CLUBS = 12
DUREE_MATCH = 40          # 2 x 20 min
POINTS = {"V": 3, "N": 1, "D": 0}

# Liste fermée des origines de but (identique à la liste déroulante du fichier buts)
ORIGINES = ["attaque placée", "attaque rapide", "transition off", "corner", "touche off",
            "touche def", "coup franc", "jet franc", "power play", "penalty", "csc"]
# Regroupements pour les tableaux
GROUPES_ORIGINE = {
    "attaque placée": "Attaque placée", "attaque rapide": "Attaque rapide",
    "transition off": "Transition off", "corner": "CPA", "touche off": "CPA",
    "touche def": "CPA", "coup franc": "CPA", "jet franc": "CPA",
    "power play": "Power play", "penalty": "Penalty", "csc": "CSC",
}
CSC = "CSC"
SANS_PASSE = "x"
TRANCHES = list(range(0, DUREE_MATCH + 1, 5))   # 0,5,...,40

# Affichage des clubs (remplacé par les fiches si nom_affiche est rempli)
NOMS_CLUBS = {"ACASA": "Paris Acasa", "ARTISTES": "Artistes", "AVION": "Avion", "GARGES": "Garges",
              "GOAL": "Goal FC", "LAVAL": "Laval", "MTP": "Montpellier", "NANTES": "Nantes",
              "NICE": "Nice", "SPORTING": "Sporting", "TOULON": "Toulon", "TOULOUSE": "Toulouse"}
ABREV_CLUBS = {"ACASA": "ACA", "ARTISTES": "ART", "AVION": "AVI", "GARGES": "GAR", "GOAL": "GOA",
               "LAVAL": "LAV", "MTP": "MTP", "NANTES": "NAN", "NICE": "NIC", "SPORTING": "SCP",
               "TOULON": "TLN", "TOULOUSE": "UJS"}
ASSETS_DIR = Path(__file__).parent / "assets"
FICHIER_TEXTES = DATA_DIR / "textes_journee.xlsx"
NB_PLAYOFFS = None     # nombre de places play-offs, None tant que le format n'est pas confirmé
