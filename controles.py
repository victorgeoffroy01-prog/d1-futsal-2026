"""
Contrôles de cohérence des données D1 Futsal.
BLOQUANT : la publication est refusée tant que ce n'est pas corrigé.
ALERTE   : publication possible, mais à vérifier.
Chaque anomalie indique le fichier, l'onglet et la ligne Excel quand c'est possible.
"""
from __future__ import annotations
from dataclasses import dataclass
import difflib

import pandas as pd

import config as C

BLOQUANT, ALERTE = "BLOQUANT", "ALERTE"
CLE = ["journee", "equipe_domicile", "equipe_exterieure", "score_dom_apres", "score_ext_apres"]
NUM = ["journee", "periode", "minute", "score_dom_avant", "score_ext_avant", "score_dom_apres", "score_ext_apres"]


@dataclass
class Anomalie:
    niveau: str
    source: str
    message: str

    def __str__(self):
        return f"[{self.niveau}] {self.source} : {self.message}"


def _ou(r) -> str:
    """Localisation lisible d'une ligne : 'BUT D1 l.28 · J1 TOULON-GARGES 28''."""
    return (f"{r['_onglet']} l.{r['_ligne_excel']} · J{r['journee']} "
            f"{r['equipe_domicile']}-{r['equipe_exterieure']} {r['minute']}'")


def _num(df: pd.DataFrame, src: str, out: list) -> pd.DataFrame:
    df = df.copy()
    for c in NUM:
        v = pd.to_numeric(df[c], errors="coerce")
        for _, r in df[v.isna()].iterrows():
            out.append(Anomalie(BLOQUANT, src, f"{_ou(r)} : '{c}' vide ou non numérique."))
        df[c] = v
    return df


# ----------------------------------------------------------------- buts
def controle_buts(g: pd.DataFrame, clubs: pd.DataFrame) -> list[Anomalie]:
    out = []
    src = "buts"
    if "origine_but" not in g:
        out.append(Anomalie(BLOQUANT, src, "Onglet global sans colonne 'origine_but'. "
                            "Ce n'est sans doute pas la version de référence du fichier."))
        g = g.assign(origine_but=pd.NA)
    g = _num(g, src, out)
    clubs = _num(clubs, src, out)

    for _, r in g.iterrows():
        loc = _ou(r)
        if pd.isna(r.joueur):
            out.append(Anomalie(BLOQUANT, src, f"{loc} : buteur vide."))
        if r.equipe_marque not in (r.equipe_domicile, r.equipe_exterieure):
            out.append(Anomalie(BLOQUANT, src, f"{loc} : equipe_marque ne joue pas ce match."))
        if {r.equipe_marque, r.equipe_encaisse} != {r.equipe_domicile, r.equipe_exterieure}:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : equipe_encaisse incohérente."))
        dom = r.equipe_marque == r.equipe_domicile
        attendu = (r.score_dom_avant + dom, r.score_ext_avant + (not dom))
        if (r.score_dom_apres, r.score_ext_apres) != attendu:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : score après {r.score_dom_apres}-{r.score_ext_apres}, "
                                f"attendu {attendu[0]}-{attendu[1]}."))
        if not 0 <= r.minute <= C.DUREE_MATCH:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : minute hors match."))
        elif (r.minute <= 20) != (r.periode == 1):
            out.append(Anomalie(BLOQUANT, src, f"{loc} : période {r.periode} incohérente avec la minute."))
        if pd.isna(r.origine_but):
            out.append(Anomalie(ALERTE, src, f"{loc} : origine du but manquante."))
        elif r.origine_but not in C.ORIGINES:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : origine '{r.origine_but}' hors liste."))

    # enchaînement des scores dans chaque match
    for (j, d, e), m in g.groupby(["journee", "equipe_domicile", "equipe_exterieure"]):
        prev = (0, 0)
        for _, r in m.sort_values(["score_dom_apres", "score_ext_apres", "minute"]).iterrows():
            if (r.score_dom_avant, r.score_ext_avant) != prev:
                out.append(Anomalie(BLOQUANT, src, f"{_ou(r)} : score avant {r.score_dom_avant}-{r.score_ext_avant}, "
                                    f"le but précédent menait à {prev[0]}-{prev[1]}."))
            prev = (r.score_dom_apres, r.score_ext_apres)
        if m.sort_values("minute").minute.tolist() != m.sort_values(["score_dom_apres", "score_ext_apres"]).minute.tolist() \
                and m.minute.duplicated().sum() == 0:
            out.append(Anomalie(BLOQUANT, src, f"J{j} {d}-{e} : minutes et scores pas dans le même ordre."))

    # doublons
    for _, r in g[g.duplicated(subset=CLE, keep=False)].iterrows():
        out.append(Anomalie(BLOQUANT, src, f"{_ou(r)} : but en double."))

    # global vs onglets clubs (seulement si des onglets clubs sont fournis)
    if clubs.empty:
        return out
    k = ["journee", "equipe_marque", "minute", "joueur"]
    a = g.groupby(k).size(); b = clubs.groupby(k).size()
    diff = pd.concat([a, b], axis=1, keys=["glob", "club"]).fillna(0)
    for idx, r in diff[diff.glob != diff.club].iterrows():
        out.append(Anomalie(BLOQUANT, src, f"Global et onglets clubs différents : J{idx[0]} {idx[1]} {idx[2]}' "
                            f"{idx[3]} (global {int(r.glob)}, clubs {int(r.club)})."))
    return out


# ----------------------------------------------------------------- passes
def controle_passes(pg: pd.DataFrame, pc: pd.DataFrame, bg: pd.DataFrame) -> list[Anomalie]:
    out = []
    src = "passes"
    pg = _num(pg, src, out); pc = _num(pc, src, out)
    bg = bg.copy()
    for c in NUM:
        bg[c] = pd.to_numeric(bg[c], errors="coerce")
    if len(pg) != len(bg):
        out.append(Anomalie(BLOQUANT, src, f"{len(pg)} lignes de passes pour {len(bg)} buts : il faut une ligne par but ('x' si pas de passeur)."))
    buts = bg.set_index(CLE)
    vus = set()
    for _, r in pg.iterrows():
        loc = _ou(r)
        k = tuple(r[c] for c in CLE)
        if pd.isna(r.joueur):
            out.append(Anomalie(BLOQUANT, src, f"{loc} : case passeur vide (mettre 'x' si pas de passeur)."))
        if k in vus:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : passe en double pour ce but."))
        vus.add(k)
        if k not in buts.index:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : aucun but correspondant dans le fichier buts."))
            continue
        but = buts.loc[[k]].iloc[0]
        if but.equipe_marque != r.equipe_marque or but.minute != r.minute or but.periode != r.periode:
            out.append(Anomalie(BLOQUANT, src, f"{loc} : équipe, minute ou période différente du but correspondant."))
        pj = str(r.joueur).upper()
        if pj == str(but.joueur).upper():
            out.append(Anomalie(BLOQUANT, src, f"{loc} : le passeur est aussi le buteur."))
        if str(but.joueur).upper() == C.CSC and pj != C.SANS_PASSE.upper():
            out.append(Anomalie(BLOQUANT, src, f"{loc} : passeur sur un CSC."))
    for k in set(map(tuple, bg[CLE].values.tolist())) - vus:
        out.append(Anomalie(BLOQUANT, src, f"But sans ligne de passe : J{k[0]} {k[1]}-{k[2]} ({k[3]}-{k[4]})."))
    # global vs clubs (seulement si des onglets clubs sont fournis)
    if pc.empty:
        return out
    a = pg.set_index(CLE).joueur.str.upper(); b = pc.set_index(CLE).joueur.str.upper()
    j = pd.concat([a, b], axis=1, keys=["glob", "club"])
    for idx, r in j[j.glob.fillna("") != j.club.fillna("")].iterrows():
        out.append(Anomalie(BLOQUANT, src, f"Global et onglets clubs différents : J{idx[0]} {idx[1]}-{idx[2]} "
                            f"({idx[3]}-{idx[4]}) global '{r.glob}', club '{r.club}'."))
    return out


# ----------------------------------------------------------------- fiches
def controle_fiches(clubs: pd.DataFrame, joueurs: pd.DataFrame, compos: pd.DataFrame) -> list[Anomalie]:
    out = []
    src = "fiches"
    for _, r in clubs.iterrows():
        if not r.get("nom_officiel"):
            out.append(Anomalie(BLOQUANT, src, f"{r.club_court} : nom_officiel vide."))
    for i in joueurs[joueurs.id_joueur.duplicated(keep=False)].id_joueur.unique():
        d = joueurs[joueurs.id_joueur == i]
        out.append(Anomalie(BLOQUANT, src, f"id_joueur '{i}' utilisé plusieurs fois : "
                            + ", ".join(f"{a} l.{b}" for a, b in zip(d.club_court, d._ligne_excel))))
    for n in joueurs[joueurs.nom_base.duplicated(keep=False)].nom_base.unique():
        out.append(Anomalie(BLOQUANT, src, f"{n} présent dans plusieurs fiches clubs : "
                            + ", ".join(joueurs[joueurs.nom_base == n].club_court)))
    ids = set(joueurs.id_joueur)
    for _, r in compos[compos.id_joueur.notna()].iterrows():
        if r.id_joueur not in ids:
            out.append(Anomalie(BLOQUANT, src, f"Compo {r.club_court} {r.poste_terrain} : id '{r.id_joueur}' inconnu."))
    gk = joueurs.groupby("club_court").gardien.apply(lambda s: (s.str.lower() == "oui").sum())
    for c in clubs.club_court:
        if gk.get(c, 0) == 0:
            out.append(Anomalie(ALERTE, src, f"{c} : aucun gardien renseigné."))
    return out


# ----------------------------------------------------------------- après assemblage
def controle_calendrier(matchs: pd.DataFrame, nb_clubs: int) -> list[Anomalie]:
    out = []
    attendu = nb_clubs // 2
    for j, m in matchs.groupby("journee"):
        if len(m) < attendu:
            out.append(Anomalie(ALERTE, "calendrier", f"J{j} : {len(m)} matchs trouvés sur {attendu}. "
                                "Un match 0-0 n'apparaît dans aucun fichier : le classement serait faux."))
        presents = list(m.dom) + list(m.ext)
        for c in set(x for x in presents if presents.count(x) > 1):
            out.append(Anomalie(BLOQUANT, "calendrier", f"J{j} : {c} joue plusieurs matchs."))
    return out


def controle_joueurs(b: pd.DataFrame) -> list[Anomalie]:
    out = []
    lignes = pd.concat([
        b[b.id_buteur.notna()][["id_buteur", "club_marque", "joueur"]].rename(columns={"id_buteur": "id"}),
        b[b.id_passeur.notna()][["id_passeur", "club_marque", "passeur_brut"]].rename(columns={"id_passeur": "id", "passeur_brut": "joueur"}),
    ])
    for i, d in lignes.groupby("id"):
        if d.club_marque.nunique() > 1:
            out.append(Anomalie(BLOQUANT, "joueurs", f"{d.joueur.iloc[0]} apparaît pour plusieurs clubs "
                                f"({', '.join(sorted(d.club_marque.unique()))}) : CSC mal saisi ou transfert à déclarer dans les fiches."))
    noms = sorted(set(lignes.joueur.str.upper()))
    for i, a in enumerate(noms):
        for c in noms[i + 1:]:
            if difflib.SequenceMatcher(None, a, c).ratio() > 0.85:
                out.append(Anomalie(ALERTE, "joueurs", f"Noms très proches : '{a}' / '{c}' (même joueur ?)."))
    return out
