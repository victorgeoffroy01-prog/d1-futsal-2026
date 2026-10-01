"""
Couche données du site D1 Futsal.
Lit les 3 fichiers sources (buts, passes, fiches clubs), normalise, relie les joueurs
par id_joueur et calcule toutes les stats utilisées par l'appli mobile et le site.

Usage :
    from data import charger
    base = charger()                 # lit, contrôle et prépare tout
    base.anomalies                   # liste des contrôles (voir controles.py)
    base.classement()                # DataFrame du classement
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

import config as C
import controles

COLS_BUT = ["journee", "equipe_domicile", "equipe_exterieure", "equipe_marque", "equipe_encaisse",
            "periode", "minute", "score_dom_avant", "score_ext_avant", "score_dom_apres",
            "score_ext_apres", "joueur"]
NUM = ["journee", "periode", "minute", "score_dom_avant", "score_ext_avant",
       "score_dom_apres", "score_ext_apres"]
CLE_BUT = ["journee", "equipe_domicile", "equipe_exterieure", "score_dom_apres", "score_ext_apres"]


# ----------------------------------------------------------------- outils
def slug(texte: str) -> str:
    """'Francisco Martínez' -> 'francisco-martinez' (id_joueur et URL)."""
    t = unicodedata.normalize("NFKD", str(texte)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def nettoie(s: pd.Series) -> pd.Series:
    """Supprime espaces en trop (début, fin, doubles) sans toucher au reste."""
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def nom_affiche(nom_base: str) -> str:
    """'FRANCISCO MARTINEZ VILLALBA' -> 'Francisco Martinez Villalba'."""
    return " ".join(m.capitalize() if "-" not in m else "-".join(x.capitalize() for x in m.split("-"))
                    for m in str(nom_base).split())


def _onglet_global(xl: pd.ExcelFile) -> str:
    return xl.sheet_names[0]


def _lire_table(xl: pd.ExcelFile, onglet: str, ncols: int) -> pd.DataFrame:
    """Lit un onglet dont l'en-tête commence par 'journee' (ligne 1 ou 2)."""
    brut = pd.read_excel(xl, onglet, header=None).iloc[:, :ncols]
    lignes = brut.index[brut[0] == "journee"]
    if len(lignes) == 0:
        raise ValueError(f"Onglet '{onglet}' : en-tête 'journee' introuvable")
    h = lignes[0]
    df = brut.iloc[h + 1:].copy()
    df.columns = [str(c).strip() for c in brut.iloc[h]]
    df = df.dropna(subset=["journee"])
    df["_ligne_excel"] = df.index + 1     # numéro de ligne Excel, pour les messages d'erreur
    df["_onglet"] = onglet.strip()
    return df.reset_index(drop=True)


# ----------------------------------------------------------------- lecture
def lire_buts(path=C.FICHIER_BUTS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne (onglet global, onglets clubs concaténés)."""
    xl = pd.ExcelFile(path)
    g = _lire_table(xl, _onglet_global(xl), 13)
    clubs = pd.concat([_lire_table(xl, s, 13) for s in xl.sheet_names[1:]], ignore_index=True)
    for df in (g, clubs):
        for c in COLS_BUT[:5] + ["joueur"]:
            df[c] = nettoie(df[c])
        if "origine_but" in df:
            df["origine_but"] = nettoie(df["origine_but"]).str.lower()
    return g, clubs


def lire_passes(path=C.FICHIER_PASSES) -> tuple[pd.DataFrame, pd.DataFrame]:
    xl = pd.ExcelFile(path)
    g = _lire_table(xl, _onglet_global(xl), 12)
    clubs = pd.concat([_lire_table(xl, s, 12) for s in xl.sheet_names[1:]], ignore_index=True)
    for df in (g, clubs):
        for c in COLS_BUT[:5] + ["joueur"]:
            df[c] = nettoie(df[c])
    return g, clubs


def lire_fiches(path=C.FICHIER_FICHES) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Retourne (clubs, joueurs, compos) depuis le fichier fiches (1 onglet par club)."""
    xl = pd.ExcelFile(path)
    clubs, joueurs, compos = [], [], []
    for s in xl.sheet_names:
        if s.lower().startswith("mode"):
            continue
        brut = pd.read_excel(xl, s, header=None)
        col0 = brut[0].astype("string").str.strip()
        # Bloc infos club : paires champ / valeur sous la ligne 'CLUB'
        info = {"club_court": s.strip()}
        debut = col0[col0 == "CLUB"].index[0]
        h_j = col0[col0 == "id_joueur"].index[0]
        for i in range(debut + 1, h_j):
            k = col0.iloc[i]
            if pd.notna(k) and k not in ("JOUEURS",):
                v = brut.iloc[i, 1]
                info[k.split(" (")[0]] = None if pd.isna(v) else str(v).strip()
        clubs.append(info)
        # Tableau joueurs : jusqu'à la première ligne totalement vide après l'en-tête
        fin = h_j + 1
        while fin < len(brut) and brut.iloc[fin].notna().any() and col0.iloc[fin] != "COMPO TYPE":
            fin += 1
        tj = brut.iloc[h_j + 1:fin].copy()
        tj.columns = [str(c).strip() for c in brut.iloc[h_j]]
        tj = tj[tj["nom_base"].notna()]
        tj["club_court"] = s.strip()
        tj["_ligne_excel"] = tj.index + 1
        joueurs.append(tj)
        # Compo type
        ct = col0[col0 == "COMPO TYPE"].index
        if len(ct):
            bloc = brut.iloc[ct[0] + 2: ct[0] + 7, :2]
            for _, r in bloc.iterrows():
                compos.append({"club_court": s.strip(), "poste_terrain": r[0],
                               "id_joueur": None if pd.isna(r[1]) else str(r[1]).strip()})
    j = pd.concat(joueurs, ignore_index=True)
    j = j.drop(columns=[c for c in j.columns if "(info)" in str(c)])
    for c in ["id_joueur", "nom_base", "surnom", "prenom", "nom", "poste", "gardien", "pied",
              "nationalite", "photo", "credit_photo", "actif"]:
        if c in j:
            j[c] = nettoie(j[c])
    j["nom_base"] = j["nom_base"].str.upper()
    j["id_auto"] = j["id_joueur"].isna()
    j.loc[j["id_auto"], "id_joueur"] = j.loc[j["id_auto"], "nom_base"].map(slug)
    j["nom_affiche"] = j["surnom"].fillna(j["nom_base"].map(nom_affiche))
    return pd.DataFrame(clubs), j, pd.DataFrame(compos)


# ----------------------------------------------------------------- base
@dataclass
class Base:
    buts: pd.DataFrame             # 1 ligne = 1 but, avec passeur, ids et clubs courts
    matchs: pd.DataFrame           # 1 ligne = 1 match (score final, mi-temps)
    joueurs: pd.DataFrame          # référentiel joueurs (fiches + joueurs générés)
    clubs: pd.DataFrame            # référentiel clubs
    compos: pd.DataFrame
    anomalies: list = field(default_factory=list)

    # ---------- état
    @property
    def bloquant(self) -> bool:
        return any(a.niveau == controles.BLOQUANT for a in self.anomalies)

    @property
    def journees(self) -> list[int]:
        return sorted(self.matchs.journee.unique().tolist())

    # ---------- classements
    def classement(self, lieu: str = "tous", jusqua: int | None = None) -> pd.DataFrame:
        """lieu : 'tous' | 'dom' | 'ext'. jusqua : dernière journée prise en compte."""
        m = self.matchs if jusqua is None else self.matchs[self.matchs.journee <= jusqua]
        lignes = []
        for r in m.itertuples():
            for club, bp, bc, cote in ((r.dom, r.bd, r.be, "dom"), (r.ext, r.be, r.bd, "ext")):
                if lieu != "tous" and lieu != cote:
                    continue
                res = "V" if bp > bc else ("N" if bp == bc else "D")
                lignes.append(dict(club=club, journee=r.journee, BP=bp, BC=bc, res=res))
        df = pd.DataFrame(lignes)
        out = []
        for club in self.clubs.club_court:
            d = df[df.club == club].sort_values("journee") if len(df) else df
            n = lambda x: int((d.res == x).sum()) if len(d) else 0
            out.append(dict(club=club, J=len(d), G=n("V"), N=n("N"), P=n("D"),
                            BP=int(d.BP.sum()) if len(d) else 0, BC=int(d.BC.sum()) if len(d) else 0,
                            forme="".join(d.res.tolist()[-5:]) if len(d) else ""))
        t = pd.DataFrame(out)
        t["Diff"] = t.BP - t.BC
        t["Pts"] = t.G * C.POINTS["V"] + t.N * C.POINTS["N"]
        # Départage provisoire : points, diff, buts marqués [règlement FFF à confirmer]
        t = t.sort_values(["Pts", "Diff", "BP", "club"], ascending=[False, False, False, True])
        t.insert(0, "Rg", range(1, len(t) + 1))
        return t.reset_index(drop=True)

    # ---------- joueurs
    def stats_joueurs(self) -> pd.DataFrame:
        """Tableau complet façon FBref : 1 ligne par joueur ayant marqué ou passé."""
        b = self.buts[self.buts.id_buteur.notna()]
        p = self.buts[self.buts.id_passeur.notna()]
        mj_club = self.classement().set_index("club").J
        rows = []
        ids = set(b.id_buteur) | set(p.id_passeur)
        jref = self.joueurs.set_index("id_joueur")
        tot_club = self.buts.groupby("club_marque").size()
        for i in ids:
            bj = b[b.id_buteur == i]; pj = p[p.id_passeur == i]
            club = jref.club_court.get(i) if i in jref.index else (bj.club_marque.iloc[0] if len(bj) else pj.club_marque.iloc[0])
            grp = bj.groupe_origine.value_counts()
            nb = len(bj)
            rows.append({
                "id_joueur": i, "joueur": jref.nom_affiche.get(i, i), "club": club,
                "MJ_club": int(mj_club.get(club, 0)),
                "Buts": nb, "Passes": len(pj), "B+P": nb + len(pj),
                "Buts_1MT": int((bj.periode == 1).sum()), "Buts_2MT": int((bj.periode == 2).sum()),
                "Buts_dom": int((bj.club_marque == bj.club_dom).sum()),
                "Buts_ext": int((bj.club_marque == bj.club_ext).sum()),
                "Att_placee": int(grp.get("Attaque placée", 0)), "Transition": int(grp.get("Transition off", 0)),
                "Att_rapide": int(grp.get("Attaque rapide", 0)), "CPA": int(grp.get("CPA", 0)),
                "Power_play": int(grp.get("Power play", 0)), "Penalty": int(grp.get("Penalty", 0)),
                "Buts_ouverture": int(bj.ouverture.sum()),
                "Pct_buts_club": round(100 * nb / tot_club.get(club, 1)) if nb else 0,
            })
        df = pd.DataFrame(rows)
        df["Buts_par_match"] = (df.Buts / df.MJ_club.where(df.MJ_club > 0)).round(2)
        return df.sort_values(["Buts", "B+P", "joueur"], ascending=[False, False, True]).reset_index(drop=True)

    def buteurs(self) -> pd.DataFrame:
        return self.stats_joueurs().query("Buts > 0")[["joueur", "club", "Buts", "Passes", "B+P"]]

    def passeurs(self) -> pd.DataFrame:
        s = self.stats_joueurs().query("Passes > 0")
        return s.sort_values(["Passes", "Buts", "joueur"], ascending=[False, False, True])[["joueur", "club", "Passes", "Buts", "B+P"]]

    def buts_plus_passes(self) -> pd.DataFrame:
        s = self.stats_joueurs()
        return s.sort_values(["B+P", "Buts", "joueur"], ascending=[False, False, True])[["joueur", "club", "B+P", "Buts", "Passes"]]

    # ---------- clubs
    def stats_club(self, club: str) -> dict:
        b = self.buts
        marques = b[b.club_marque == club]
        encaisses = b[b.club_encaisse == club]
        tr = lambda d: pd.cut(d.minute, bins=C.TRANCHES, labels=[f"{a}-{a+5}" for a in C.TRANCHES[:-1]]).value_counts().sort_index()
        return {
            "classement": self.classement().set_index("club").loc[club].to_dict(),
            "tranches_marques": tr(marques).to_dict(),
            "tranches_encaisses": tr(encaisses).to_dict(),
            "origines": marques.origine_but.value_counts().to_dict(),
            "origines_encaisses": encaisses.origine_but.value_counts().to_dict(),
            "buteurs": marques[marques.id_buteur.notna()].groupby("buteur").size().sort_values(ascending=False).to_dict(),
            "passeurs": marques[marques.id_passeur.notna()].groupby("passeur").size().sort_values(ascending=False).to_dict(),
            "matchs": self.matchs[(self.matchs.dom == club) | (self.matchs.ext == club)],
        }

    def stats_ligue(self) -> dict:
        b = self.buts
        return {
            "nb_buts": len(b), "nb_matchs": len(self.matchs),
            "buts_par_match": round(len(b) / max(len(self.matchs), 1), 2),
            "origines": b.origine_but.value_counts().to_dict(),
            "tranches": pd.cut(b.minute, bins=C.TRANCHES, labels=[f"{a}-{a+5}" for a in C.TRANCHES[:-1]]).value_counts().sort_index().to_dict(),
            "part_avec_passe": round(100 * b.id_passeur.notna().mean()),
        }

    def match(self, journee: int, dom: str) -> pd.DataFrame:
        """Timeline d'un match (dom = club court)."""
        return self.buts[(self.buts.journee == journee) & (self.buts.club_dom == dom)].sort_values(["minute", "score_dom_apres", "score_ext_apres"])


# ----------------------------------------------------------------- assemblage
def charger(f_buts=C.FICHIER_BUTS, f_passes=C.FICHIER_PASSES, f_fiches=C.FICHIER_FICHES) -> Base:
    anomalies = []
    bg, bc = lire_buts(f_buts)
    pg, pc = lire_passes(f_passes)
    clubs, joueurs, compos = lire_fiches(f_fiches)

    # 1. contrôles sur les sources brutes
    anomalies += controles.controle_buts(bg, bc)
    anomalies += controles.controle_passes(pg, pc, bg)
    anomalies += controles.controle_fiches(clubs, joueurs, compos)

    # 2. table des buts enrichie
    officiel_vers_court = dict(zip(clubs.nom_officiel, clubs.club_court))
    b = bg.copy()
    if "origine_but" not in b:
        b["origine_but"] = pd.NA
    for c in NUM:
        b[c] = pd.to_numeric(b[c], errors="coerce").astype("Int64")
    for src, dst in [("equipe_domicile", "club_dom"), ("equipe_exterieure", "club_ext"),
                     ("equipe_marque", "club_marque"), ("equipe_encaisse", "club_encaisse")]:
        b[dst] = b[src].map(officiel_vers_court)
    inconnus = set(b.equipe_marque) - set(officiel_vers_court)
    for o in sorted(inconnus):
        anomalies.append(controles.Anomalie(controles.BLOQUANT, "fiches",
                         f"Club '{o}' présent dans le fichier buts mais absent des fiches (nom_officiel)."))
    b["est_csc"] = b.joueur.str.upper() == C.CSC
    b["groupe_origine"] = b.origine_but.map(C.GROUPES_ORIGINE)
    b["ouverture"] = (b.score_dom_apres + b.score_ext_apres) == 1

    # passeur : jointure sur la clé unique du but
    p = pg.copy()
    for c in NUM:
        p[c] = pd.to_numeric(p[c], errors="coerce").astype("Int64")
    p = p[CLE_BUT + ["joueur"]].rename(columns={"joueur": "passeur_brut"})
    b = b.merge(p, on=CLE_BUT, how="left")
    b["passeur_brut"] = b.passeur_brut.where(b.passeur_brut.str.lower() != C.SANS_PASSE)

    # 3. rattachement aux id_joueur (nom_base + club), joueurs absents des fiches générés
    ref = {(r.nom_base, r.club_court): r.id_joueur for r in joueurs.itertuples()}
    ref_nom = joueurs.groupby("nom_base").id_joueur.first().to_dict()
    nouveaux = []

    def resoudre(nom, club):
        if pd.isna(nom):
            return None
        nom = nom.upper()
        if (nom, club) in ref:
            return ref[(nom, club)]
        if nom in ref_nom:     # présent dans les fiches mais sous un autre club
            anomalies.append(controles.Anomalie(controles.ALERTE, "fiches",
                             f"{nom} : fiche dans un autre club que {club} (transfert ?)."))
            return ref_nom[nom]
        i = slug(nom)
        nouveaux.append(dict(id_joueur=i, nom_base=nom, club_court=club, id_auto=True,
                             nom_affiche=nom_affiche(nom), absent_fiches=True))
        ref[(nom, club)] = i
        ref_nom[nom] = i
        return i

    b["id_buteur"] = [None if csc else resoudre(n, c) for n, c, csc in zip(b.joueur, b.club_marque, b.est_csc)]
    b["id_passeur"] = [resoudre(n, c) for n, c in zip(b.passeur_brut, b.club_marque)]
    if nouveaux:
        anomalies.append(controles.Anomalie(controles.ALERTE, "fiches",
                         f"{len(nouveaux)} joueur(s) absent(s) des fiches, id généré automatiquement : "
                         + ", ".join(n['nom_base'] for n in nouveaux)))
        joueurs = pd.concat([joueurs, pd.DataFrame(nouveaux)], ignore_index=True)
    noms = joueurs.set_index("id_joueur").nom_affiche
    b["buteur"] = b.id_buteur.map(noms).where(~b.est_csc, "CSC")
    b["passeur"] = b.id_passeur.map(noms)

    # 4. matchs (score final et mi-temps)
    rows = []
    for (j, d, e), m in b.groupby(["journee", "club_dom", "club_ext"]):
        m = m.sort_values(["score_dom_apres", "score_ext_apres"])
        mt = m[m.periode == 1]
        rows.append(dict(journee=int(j), dom=d, ext=e, bd=int(m.score_dom_apres.max()),
                         be=int(m.score_ext_apres.max()),
                         mt_d=int(mt.score_dom_apres.max()) if len(mt) else 0,
                         mt_e=int(mt.score_ext_apres.max()) if len(mt) else 0,
                         nb_buts=len(m)))
    matchs = pd.DataFrame(rows).sort_values(["journee", "dom"]).reset_index(drop=True)
    anomalies += controles.controle_calendrier(matchs, len(clubs))
    anomalies += controles.controle_joueurs(b)

    return Base(buts=b, matchs=matchs, joueurs=joueurs, clubs=clubs, compos=compos, anomalies=anomalies)
