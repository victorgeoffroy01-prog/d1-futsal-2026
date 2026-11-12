"""
Stats de contexte du site D1 Futsal (lot A du 12/11/2026), tirées UNIQUEMENT des buts et des passes.
- joueurs : buts qui comptent, points rapportés, buts selon le score, 36'-40', doublés, minute moyenne, duos
- équipes : marque/encaisse en premier, remontadas, temps devant/égalité/derrière, mi-temps, réaction, dépendance...
- records et séries de la D1 (bloc compact de la Une)
Tout part de base.buts (1 ligne = 1 but) et base.matchs. Aucune donnée des rapports PDF ici.
"""
from __future__ import annotations

import pandas as pd

import config as C

FIN = 36                 # « money time » : buts de la 36e à la 40e minute
REACTION = 2             # réaction : but marqué dans les 2 minutes après un but encaissé


def _pts(f, a) -> int:
    return C.POINTS["V"] if f > a else (C.POINTS["N"] if f == a else C.POINTS["D"])


def ordonner(b: pd.DataFrame) -> pd.DataFrame:
    """Buts dans l'ordre du match (période, minute, puis score cumulé pour deux buts dans la même minute)."""
    return b.assign(_tot=b.score_dom_apres + b.score_ext_apres).sort_values(["journee", "club_dom", "periode", "minute", "_tot"]).drop(columns="_tot")


# ================================================================== colonnes ajoutées à chaque but
def enrichir_buts(b: pd.DataFrame, matchs: pd.DataFrame) -> pd.DataFrame:
    """Ajoute à chaque but le contexte du point de vue de l'équipe qui marque :
    ecart_avant (+ devant, - mené), etat_avant (mene/egal/devant), egalisateur, avantage (donne l'avantage, hors 1er but),
    vainqueur (but de la victoire), fin_match (36'-40')."""
    b = b.copy()
    dom = b.club_marque == b.club_dom
    pour = b.score_dom_avant.where(dom, b.score_ext_avant)
    contre = b.score_ext_avant.where(dom, b.score_dom_avant)
    b["ecart_avant"] = (pour - contre).astype("Int64")
    b["etat_avant"] = b.ecart_avant.map(lambda d: "mene" if d < 0 else ("egal" if d == 0 else "devant")).astype("string")
    b["egalisateur"] = b.ecart_avant == -1
    b["avantage"] = (b.ecart_avant == 0) & ~b.ouverture
    b["fin_match"] = b.minute >= FIN
    # but vainqueur : pour un score final f-a gagné, c'est le (a+1)e but du vainqueur
    b["vainqueur"] = False
    fin = {(r.journee, r.dom): (r.bd, r.be) for r in matchs.itertuples()}
    for (j, d), g in ordonner(b).groupby(["journee", "club_dom"], sort=False):
        bd, be = fin[(j, d)]
        if bd == be:
            continue
        gagnant = d if bd > be else g.club_ext.iloc[0]
        a = min(bd, be)
        idx = g[g.club_marque == gagnant].index
        if len(idx) > a:
            b.loc[idx[a], "vainqueur"] = True
    return b


# ================================================================== joueurs
def stats_joueurs(b: pd.DataFrame, matchs: pd.DataFrame) -> pd.DataFrame:
    """1 ligne par buteur : buts qui comptent, points rapportés, selon le score, 36'-40', doublés, minute moyenne."""
    bj = b[b.id_buteur.notna()]
    if bj.empty:
        return pd.DataFrame(columns=["id_joueur"] + list(COLS))
    fin = {(r.journee, r.dom): (r.bd, r.be) for r in matchs.itertuples()}
    rows = []
    for i, g in bj.groupby("id_buteur"):
        pts = 0
        par_match = g.groupby(["journee", "club_dom"])
        for (j, d), gm in par_match:
            if (j, d) not in fin:
                continue
            bd, be = fin[(j, d)]
            dom = gm.club_marque.iloc[0] == d
            f, a = (bd, be) if dom else (be, bd)
            pts += _pts(f, a) - _pts(f - len(gm), a)      # points perdus si on retire ses buts
        n_match = par_match.size()
        rows.append({"id_joueur": i,
                     "Egalisateurs": int(g.egalisateur.sum()), "Avantage": int(g.avantage.sum()),
                     "Vainqueurs": int(g.vainqueur.sum()), "Pts_rapportes": int(pts),
                     "Mene": int((g.etat_avant == "mene").sum()), "Egal": int((g.etat_avant == "egal").sum()),
                     "Devant": int((g.etat_avant == "devant").sum()), "Fin_match": int(g.fin_match.sum()),
                     "Doubles": int((n_match >= 2).sum()), "Triples": int((n_match >= 3).sum()),
                     "Minute_moy": round(float(g.minute.mean()), 1)})
    return pd.DataFrame(rows)


# colonnes du tableau « Contexte » (libellés complets pour l'export, courts pour l'écran)
COLS = {"Egalisateurs": "Buts égalisateurs", "Avantage": "Buts qui donnent l'avantage", "Vainqueurs": "Buts vainqueurs",
        "Pts_rapportes": "Points rapportés", "Mene": "Buts quand l'équipe est menée", "Egal": "Buts à égalité",
        "Devant": "Buts quand l'équipe mène", "Fin_match": "Buts 36'-40'", "Doubles": "Matchs à 2 buts ou plus",
        "Minute_moy": "Minute moyenne de ses buts"}
COURTS = {"Egalisateurs": "Égalis.", "Avantage": "Avantage", "Vainqueurs": "Vainq.", "Pts_rapportes": "Pts rapp.",
          "Mene": "Mené", "Egal": "Égalité", "Devant": "Devant", "Fin_match": "36'-40'", "Doubles": "Doublés", "Minute_moy": "Min. moy."}


def duos(b: pd.DataFrame, club: str | None = None) -> pd.DataFrame:
    """Duos passeur -> buteur, du plus prolifique au moins prolifique (club = None : toute la D1)."""
    d = b[b.id_buteur.notna() & b.id_passeur.notna()]
    if club:
        d = d[d.club_marque == club]
    if d.empty:
        return pd.DataFrame(columns=["id_passeur", "passeur", "id_buteur", "buteur", "club", "n"])
    t = d.groupby(["id_passeur", "passeur", "id_buteur", "buteur", "club_marque"]).size().reset_index(name="n")
    return t.rename(columns={"club_marque": "club"}).sort_values(["n", "buteur"], ascending=[False, True]).reset_index(drop=True)


def duo_joueur(b: pd.DataFrame, i: str):
    """Partenaire favori d'un joueur, dans les deux sens : (id, nom, total, passes reçues de lui, passes données à lui) ou None."""
    recu = b[(b.id_buteur == i) & b.id_passeur.notna()].groupby(["id_passeur", "passeur"]).size()
    donne = b[(b.id_passeur == i) & b.id_buteur.notna()].groupby(["id_buteur", "buteur"]).size()
    tout = {}
    for (k, nom), n in recu.items():
        tout.setdefault(k, [nom, 0, 0])[1] += int(n)
    for (k, nom), n in donne.items():
        tout.setdefault(k, [nom, 0, 0])[2] += int(n)
    if not tout:
        return None
    k, (nom, r, d) = max(tout.items(), key=lambda kv: (kv[1][1] + kv[1][2], kv[1][1], kv[1][0]))
    return k, nom, r + d, r, d


# ================================================================== équipes : déroulé de chaque match
def deroules(b: pd.DataFrame, matchs: pd.DataFrame) -> pd.DataFrame:
    """1 ligne par (match, club) avec tout le contexte du match vu par ce club."""
    rows = []
    par_match = {k: g for k, g in ordonner(b).groupby(["journee", "club_dom"], sort=False)}
    for m in matchs.itertuples():
        g = par_match.get((m.journee, m.dom), b.iloc[0:0])
        for club, adv, f, a, mt_f, mt_a in ((m.dom, m.ext, m.bd, m.be, m.mt_d, m.mt_e), (m.ext, m.dom, m.be, m.bd, m.mt_e, m.mt_d)):
            pour = contre = 0
            devant = egal = derriere = 0.0
            t0, mene_max, a_mene, a_ete_mene = 0.0, 0, False, False
            reactions, encaisses = 0, 0
            buts = list(g.itertuples())
            for n, x in enumerate(buts):
                t = x.minute - 0.5                       # but dans la minute m : changement d'état à m - 0,5
                ecart = pour - contre
                duree = t - t0
                devant += duree if ecart > 0 else 0; egal += duree if ecart == 0 else 0; derriere += duree if ecart < 0 else 0
                t0 = t
                if x.club_marque == club:
                    pour += 1
                else:
                    contre += 1
                    encaisses += 1
                    if any(y.club_marque == club and y.minute - x.minute <= REACTION for y in buts[n + 1:]):
                        reactions += 1
                ecart = pour - contre
                a_mene |= ecart > 0
                a_ete_mene |= ecart < 0
                mene_max = max(mene_max, -ecart)
            ecart = pour - contre
            duree = C.DUREE_MATCH - t0
            devant += duree if ecart > 0 else 0; egal += duree if ecart == 0 else 0; derriere += duree if ecart < 0 else 0
            premier = buts[0].club_marque if buts else None
            res = "V" if f > a else ("N" if f == a else "D")
            rows.append(dict(journee=m.journee, dom=m.dom, club=club, adv=adv, BP=f, BC=a, res=res, pts=_pts(f, a),
                             premier=("pour" if premier == club else ("contre" if premier else None)),
                             a_mene=a_mene, a_ete_mene=a_ete_mene, mene_max=mene_max,
                             mt=("devant" if mt_f > mt_a else ("egal" if mt_f == mt_a else "derriere")),
                             devant=devant, egal=egal, derriere=derriere,
                             fin_pour=int(((g.club_marque == club) & g.fin_match).sum()),
                             fin_contre=int(((g.club_marque != club) & g.fin_match).sum()),
                             reactions=reactions, encaisses=encaisses))
    return pd.DataFrame(rows)


def _bilan(d: pd.DataFrame) -> dict:
    """V/N/D, points et points par match d'un ensemble de matchs."""
    n = len(d)
    return {"n": n, "V": int((d.res == "V").sum()), "N": int((d.res == "N").sum()), "D": int((d.res == "D").sum()),
            "pts": int(d.pts.sum()), "ppm": round(d.pts.sum() / n, 2) if n else None}


def contexte_club(dr: pd.DataFrame, b: pd.DataFrame, club: str) -> dict:
    """Bloc « Contexte » d'une fiche club, chaque chiffre avec la moyenne D1 pour comparer."""
    d = dr[dr.club == club]
    tot = lambda x: float(x.devant.sum() + x.egal.sum() + x.derriere.sum()) or 1.0
    marques = b[b.club_marque == club]
    buteurs = marques[marques.id_buteur.notna()].groupby("buteur").size().sort_values(ascending=False)
    par_club = b[b.id_buteur.notna()].groupby(["club_marque", "id_buteur"]).size()
    dep_d1 = [100 * g.max() / b[b.club_marque == c].shape[0] for c, g in par_club.groupby(level=0) if len(b[b.club_marque == c])]
    nb_clubs = max(dr.club.nunique(), 1)
    return {
        "premier_pour": _bilan(d[d.premier == "pour"]), "premier_contre": _bilan(d[d.premier == "contre"]),
        "d1_premier_pour": _bilan(dr[dr.premier == "pour"]), "d1_premier_contre": _bilan(dr[dr.premier == "contre"]),
        # remontadas : matchs où le club a été mené ; points perdus : matchs où il a mené
        "mene": _bilan(d[d.a_ete_mene]), "remontadas": int((d.a_ete_mene & (d.res == "V")).sum()),
        "a_mene": _bilan(d[d.a_mene]), "pts_perdus": int((C.POINTS["V"] - d[d.a_mene].pts).sum()),
        "d1_pts_perdus": round((C.POINTS["V"] - dr[dr.a_mene].pts).sum() / nb_clubs, 1),
        "d1_remontadas": round((dr.a_ete_mene & (dr.res == "V")).sum() / nb_clubs, 1),
        "temps": {k: round(100 * d[k].sum() / tot(d)) for k in ("devant", "egal", "derriere")},
        "d1_temps": {k: round(100 * dr[k].sum() / tot(dr)) for k in ("devant", "egal", "derriere")},
        "mi_temps": {k: _bilan(d[d.mt == k]) for k in ("devant", "egal", "derriere")},
        "d1_mi_temps": {k: _bilan(dr[dr.mt == k]) for k in ("devant", "egal", "derriere")},
        "fin_pour": int(d.fin_pour.sum()), "fin_contre": int(d.fin_contre.sum()),
        "d1_fin": round(dr.fin_pour.sum() / nb_clubs, 1),
        "reactions": int(d.reactions.sum()), "encaisses": int(d.encaisses.sum()),
        "pct_reaction": round(100 * d.reactions.sum() / d.encaisses.sum()) if d.encaisses.sum() else None,
        "d1_pct_reaction": round(100 * dr.reactions.sum() / dr.encaisses.sum()) if dr.encaisses.sum() else None,
        "clean_sheets": int((d.BC == 0).sum()), "sans_marquer": int((d.BP == 0).sum()),
        "d1_clean_sheets": int((dr.BC == 0).sum()), "d1_sans_marquer": int((dr.BP == 0).sum()), "d1_matchs": len(dr) // 2,
        "nb_buteurs": int(len(buteurs)), "top_buteur": (buteurs.index[0], int(buteurs.iloc[0])) if len(buteurs) else None,
        "dependance": round(100 * buteurs.iloc[0] / len(marques)) if len(buteurs) and len(marques) else None,
        "d1_dependance": round(sum(dep_d1) / len(dep_d1)) if dep_d1 else None,
        "d1_nb_buteurs": round(b[b.id_buteur.notna()].groupby("club_marque").id_buteur.nunique().mean(), 1),
    }


def rangs(base) -> dict:
    """Rang de chaque club après chaque journée : {club: [(journee, rang), ...]}."""
    out = {c: [] for c in base.clubs.club_court}
    for j in base.journees:
        for r in base.classement(jusqua=j).itertuples():
            out[r.club].append((j, r.Rg))
    return out


# ================================================================== records et séries de la D1
def _serie_en_cours(resultats: list, ok) -> int:
    n = 0
    for r in reversed(resultats):
        if not ok(r):
            break
        n += 1
    return n


def records(b: pd.DataFrame, matchs: pd.DataFrame, dr: pd.DataFrame, noms: dict) -> list[dict]:
    """Liste de records : {cle, valeur, libelle, detail, lien (j, dom) | None}. Le premier en date l'emporte en cas d'égalité."""
    if b.empty:
        return []
    N = lambda c: noms.get(c, c)
    vs = lambda x: f"{N(x.club_dom)}-{N(x.club_ext)}, J{x.journee}"
    out = []
    joueurs = b[b.id_buteur.notna()]
    # but le plus rapide
    x = joueurs.sort_values(["minute", "journee"]).iloc[0] if len(joueurs) else None
    if x is not None:
        out.append(dict(cle="rapide", valeur=f"{x.minute}'", libelle="But le plus rapide",
                        detail=f"{x.buteur} ({N(x.club_marque)}) · {vs(x)}", lien=(x.journee, x.club_dom)))
    # but vainqueur le plus tardif
    v = b[b.vainqueur].sort_values(["minute", "journee"], ascending=[False, True])
    if len(v):
        x = v.iloc[0]
        out.append(dict(cle="vainqueur", valeur=f"{x.minute}'", libelle="But vainqueur le plus tardif",
                        detail=f"{x.buteur} ({N(x.club_marque)}) · {vs(x)}", lien=(x.journee, x.club_dom)))
    # égalisation la plus tardive
    v = b[b.egalisateur].sort_values(["minute", "journee"], ascending=[False, True])
    if len(v):
        x = v.iloc[0]
        out.append(dict(cle="egalisation", valeur=f"{x.minute}'", libelle="Égalisation la plus tardive",
                        detail=f"{x.buteur} ({N(x.club_marque)}) · {vs(x)}", lien=(x.journee, x.club_dom)))
    # plus grande remontada (victoire après avoir été mené de k buts)
    r = dr[(dr.res == "V") & (dr.mene_max > 0)].sort_values(["mene_max", "journee"], ascending=[False, True])
    if len(r):
        x = r.iloc[0]
        out.append(dict(cle="remontada", valeur=f"-{x.mene_max}", libelle="Plus grande remontada",
                        detail=f"{N(x.club)} bat {N(x.adv)} {x.BP}-{x.BC} · J{x.journee}", lien=(x.journee, x.dom)))
    # plus large victoire et plus large victoire à l'extérieur
    for cle, lib, d in [("ecart", "Plus large victoire", dr[dr.res == "V"]), ("ecart_ext", "Plus large victoire à l'extérieur", dr[(dr.res == "V") & (dr.club != dr.dom)])]:
        d = d.assign(e=d.BP - d.BC).sort_values(["e", "BP", "journee"], ascending=[False, False, True])
        if len(d):
            x = d.iloc[0]
            out.append(dict(cle=cle, valeur=f"{x.BP}-{x.BC}", libelle=lib, detail=f"{N(x.club)} face à {N(x.adv)} · J{x.journee}", lien=(x.journee, x.dom)))
    # match le plus prolifique
    x = matchs.sort_values(["nb_buts", "journee"], ascending=[False, True]).iloc[0]
    out.append(dict(cle="prolifique", valeur=str(x.nb_buts), libelle="Buts dans un match",
                    detail=f"{N(x.dom)} {x.bd}-{x.be} {N(x.ext)} · J{x.journee}", lien=(x.journee, x.dom)))
    # rafale : le plus de buts d'une équipe en 5 minutes
    best = None
    for (j, d, c), g in b.groupby(["journee", "club_dom", "club_marque"]):
        mins = sorted(g.minute.tolist())
        for k, m0 in enumerate(mins):
            n = sum(1 for m in mins[k:] if m - m0 <= 4)
            if best is None or n > best[0] or (n == best[0] and j < best[1]):
                best = (n, j, d, c, m0, max(m for m in mins[k:] if m - m0 <= 4), g.club_ext.iloc[0])
    if best and best[0] >= 2:
        n, j, d, c, m0, m1, e = best
        out.append(dict(cle="rafale", valeur=str(n), libelle="Buts d'une équipe en 5 min",
                        detail=f"{N(c)} ({m0}'-{m1}') · {N(d)}-{N(e)}, J{j}", lien=(j, d)))
    # triplé le plus rapide
    best = None
    for (j, d, i), g in joueurs.groupby(["journee", "club_dom", "id_buteur"]):
        mins = sorted(g.minute.tolist())
        for k in range(len(mins) - 2):
            ecart = mins[k + 2] - mins[k]
            if best is None or ecart < best[0]:
                best = (ecart, j, d, g.buteur.iloc[0], g.club_marque.iloc[0], mins[k], mins[k + 2])
    if best:
        ecart, j, d, nom, c, m0, m2 = best
        out.append(dict(cle="triple", valeur=f"{ecart} min", libelle="Triplé le plus rapide",
                        detail=f"{nom} ({N(c)}) · {m0}' à {m2}', J{j}", lien=(j, d)))
    # plus de buteurs différents dans un match (une équipe)
    t = joueurs.groupby(["journee", "club_dom", "club_marque"]).id_buteur.nunique().reset_index(name="n").sort_values(["n", "journee"], ascending=[False, True])
    if len(t):
        x = t.iloc[0]
        out.append(dict(cle="buteurs", valeur=str(x.n), libelle="Buteurs différents dans un match",
                        detail=f"{N(x.club_marque)} · J{x.journee}", lien=(x.journee, x.club_dom)))
    # plus de buts en une période (une équipe)
    t = b.groupby(["journee", "club_dom", "club_marque", "periode"]).size().reset_index(name="n").sort_values(["n", "journee"], ascending=[False, True])
    if len(t):
        x = t.iloc[0]
        out.append(dict(cle="periode", valeur=str(x.n), libelle="Buts d'une équipe en une mi-temps",
                        detail=f"{N(x.club_marque)} · {'1re' if x.periode == 1 else '2e'} MT, J{x.journee}", lien=(x.journee, x.club_dom)))
    # joueur décisif (but ou passe) dans le plus de matchs différents
    dec = pd.concat([b[["journee", "club_dom", "id_buteur", "buteur", "club_marque"]].rename(columns={"id_buteur": "id", "buteur": "nom"}),
                     b[["journee", "club_dom", "id_passeur", "passeur", "club_marque"]].rename(columns={"id_passeur": "id", "passeur": "nom"})]).dropna(subset=["id"])
    t = dec.drop_duplicates(["journee", "club_dom", "id"]).groupby(["id", "nom", "club_marque"]).size().reset_index(name="n").sort_values(["n", "nom"], ascending=[False, True])
    if len(t):
        x = t.iloc[0]
        nb_j = matchs.journee.nunique()
        out.append(dict(cle="decisif", valeur=f"{x.n}/{nb_j}", libelle="Matchs avec but ou passe",
                        detail=f"{x.nom} ({N(x.club_marque)})", lien=None, joueur=x.id))
    # duo le plus prolifique
    du = duos(b)
    if len(du):
        x = du.iloc[0]
        out.append(dict(cle="duo", valeur=str(x.n), libelle="Duo passeur-buteur",
                        detail=f"{x.passeur} pour {x.buteur} ({N(x.club)})", lien=None, joueur=x.id_buteur))
    return out


def series(dr: pd.DataFrame, noms: dict) -> list[dict]:
    """Séries en cours des équipes (après la dernière journée) : victoires, invincibilité, sans victoire."""
    out = []
    par_club = {c: g.sort_values("journee").res.tolist() for c, g in dr.groupby("club")}
    for cle, lib, ok in [("victoires", "victoires de suite", lambda r: r == "V"),
                         ("invaincu", "matchs sans défaite", lambda r: r != "D"),
                         ("sans_victoire", "matchs sans victoire", lambda r: r != "V")]:
        t = sorted(((_serie_en_cours(res, ok), c) for c, res in par_club.items()), key=lambda x: (-x[0], noms.get(x[1], x[1])))
        if t and t[0][0] >= 2:
            n = t[0][0]
            ex = [c for k, c in t if k == n]
            out.append(dict(cle=cle, valeur=str(n), libelle=f"Série en cours : {lib}", clubs=ex,
                            detail=" · ".join(noms.get(c, c) for c in ex)))
    return out
