"""
Rapports de match publiés tels quels (PDF produits par l'appli de rapports).

Dépôt : un PDF par match analysé dans le dossier `rapport/` (ou `rapports/`),
nommé  J04_TOULON-NANTES.pdf  : journée sur 2 chiffres, équipe à domicile, équipe à l'extérieur.
Les abréviations habituelles sont acceptées (NMF, UJS, MTP, SCP, ACASA...).
Un fichier qui ne correspond à aucun match n'est pas publié et remonte en alerte (page contrôle).
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path

import config as C
import controles

DOSSIERS = ["rapport", "rapports"]
MOTIF = re.compile(r"^J(\d{1,2})_(.+?)-(.+?)\.pdf$", re.IGNORECASE)

# abréviations utilisées dans les noms de fichiers -> club_court
ALIAS = {
    "NMF": "NANTES", "NANTES METROPOLE": "NANTES", "UJS": "TOULOUSE", "UJS TOULOUSE": "TOULOUSE",
    "SCP": "SPORTING", "SPORTING PARIS": "SPORTING", "SPORTING CLUB PARIS": "SPORTING",
    "PARIS ACASA": "ACASA", "ACA": "ACASA", "MONTPELLIER": "MTP", "GOAL FC": "GOAL", "GOA": "GOAL",
    "ETOILE LAVALLOISE": "LAVAL", "LAV": "LAVAL", "ART": "ARTISTES", "ARTISTES FUTSAL": "ARTISTES",
    "AVI": "AVION", "AS AVION": "AVION", "GAR": "GARGES", "GARGES DJIBSON": "GARGES",
    "NIC": "NICE", "NAN": "NANTES", "TLN": "TOULON", "TOULON METROPOLE": "TOULON",
}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[\s_]+", " ", t).strip()


def _club(nom: str, clubs: set[str]) -> str | None:
    n = _norm(nom)
    if n in clubs:
        return n
    if n in ALIAS:
        return ALIAS[n]
    for court, aff in C.NOMS_CLUBS.items():
        if _norm(aff) == n:
            return court
    for court, ab in C.ABREV_CLUBS.items():
        if ab == n:
            return court
    return None


def lister(base) -> tuple[dict, list]:
    """Renvoie ({(journee, dom): chemin_pdf}, anomalies)."""
    trouves, anomalies = {}, []
    clubs = set(base.clubs.club_court)
    racine = Path(__file__).parent
    for d in DOSSIERS:
        dossier = racine / d
        if not dossier.is_dir():
            continue
        for f in sorted(dossier.glob("*.pdf")) + sorted(dossier.glob("*.PDF")):
            m = MOTIF.match(f.name)
            if not m:
                anomalies.append(controles.Anomalie(controles.ALERTE, "rapports",
                                 f"{f.name} : nom non reconnu, attendu J04_DOMICILE-EXTERIEUR.pdf. Non publié."))
                continue
            j, a, b = int(m.group(1)), _club(m.group(2), clubs), _club(m.group(3), clubs)
            if not a or not b:
                inconnu = m.group(2) if not a else m.group(3)
                anomalies.append(controles.Anomalie(controles.ALERTE, "rapports",
                                 f"{f.name} : équipe '{inconnu}' non reconnue. Non publié."))
                continue
            mm = base.matchs[(base.matchs.journee == j) & (((base.matchs.dom == a) & (base.matchs.ext == b)) |
                                                          ((base.matchs.dom == b) & (base.matchs.ext == a)))]
            if mm.empty:
                anomalies.append(controles.Anomalie(controles.ALERTE, "rapports",
                                 f"{f.name} : aucun match {a}-{b} en J{j} dans le fichier buts. Non publié."))
                continue
            trouves[(j, mm.iloc[0].dom)] = str(f)
    return trouves, anomalies


def pages_png(chemin: str, largeur: int = 900) -> list[bytes]:
    """Pages du PDF en images (aperçu dans le site)."""
    import pymupdf
    doc = pymupdf.open(chemin)
    out = []
    for p in doc:
        zoom = largeur / p.rect.width
        out.append(p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))
    return out
