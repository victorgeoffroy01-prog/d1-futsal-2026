"""
Blocs HTML des nouvelles stats (lots A et C du 12/11/2026), communs au mobile et à l'ordinateur.
Les calculs sont dans contexte.py ; ici, seulement la mise en forme (même DA que le reste du site).
"""
from __future__ import annotations

import components as ui
from components import e, fr
from theme import PAPER, INK, RED, MUTED, LINE, SOFT, SERIF, COND


def _pl(n, mot, pluriel=None):
    return f"{n} {mot if n in (0, 1) else (pluriel or mot + 's')}"


def _note(txt, mt=10):
    return f'<div style="font-size: 12px; color: {MUTED}; line-height: 1.5; margin-top: {mt}px">{txt}</div>'


# ================================================================== joueur
def buts_qui_comptent(s, nb_ouverture: int, mt1: int, mt2: int, numsize=30) -> str:
    """Tuiles « Buts qui comptent » + répartition selon le score de la fiche joueur (s = ligne de stats_joueurs)."""
    t = lambda v, l, st="paper": ui.tile(v, l, st, numsize)
    total = max(int(s.Mene + s.Egal + s.Devant), 1)
    seg = lambda v, c, fg: (f'<div style="flex: {int(v)} 1 0; min-width: {24 if v else 0}px; background: {c}; color: {fg}; display: {"flex" if v else "none"}; '
                            f'align-items: center; justify-content: center; font-family: {COND}; font-weight: 700; font-size: 12px">{int(v)}</div>')
    barre = (f'<div style="display: flex; height: 24px; border-radius: 4px; overflow: hidden; border: 1px solid {LINE}; margin-top: 8px">'
             f'{seg(s.Mene, RED, "#fff")}{seg(s.Egal, SOFT, INK)}{seg(s.Devant, INK, "#fff")}</div>'
             f'<div style="display: flex; justify-content: space-between; font-family: {COND}; font-size: 11px; letter-spacing: 0.06em; color: {MUTED}; margin-top: 4px">'
             f'<span>ÉQUIPE MENÉE {round(100 * s.Mene / total)} %</span><span>ÉGALITÉ {round(100 * s.Egal / total)} %</span><span>ÉQUIPE DEVANT {round(100 * s.Devant / total)} %</span></div>')
    details = " · ".join([f"1re / 2e MT : {mt1}/{mt2}", f"minute moyenne : {fr(s.Minute_moy)}’",
                          _pl(int(s.Doubles), "match à 2 buts ou plus", "matchs à 2 buts ou plus")]
                         + ([_pl(int(s.Triples), "triplé")] if s.Triples else []))
    return (ui.kicker("Buts qui comptent", mt=4)
            + ui.tiles(t(int(s.Pts_rapportes), "points rapportés", "red"), t(int(s.Vainqueurs), "buts vainqueurs", "dark"), t(int(s.Egalisateurs), "égalisateurs"))
            + ui.tiles(t(nb_ouverture, "ouvrent le score"), t(int(s.Avantage), "donnent l’avantage"), t(int(s.Fin_match), "buts 36’-40’"), mt=8)
            + f'<div style="margin-top: 16px; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em">SES BUTS SELON LE SCORE</div>' + barre
            + _note(e(details))
            + _note("Points rapportés : points que son équipe aurait perdus sans ses buts. Donnent l’avantage : buts qui font passer de l’égalité à devant, hors 1er but du match.", 6))


def duo_favori(d) -> str:
    """d = contexte.duo_joueur(...) : (id, nom, total, passes reçues, passes données) ou None. Le nom est cliquable."""
    if not d:
        return ""
    k, nom, n, recu, donne = d
    sens = " · ".join(x for x in [f"{_pl(recu, 'passe')} de lui" if recu else "", f"{_pl(donne, 'passe')} pour lui" if donne else ""] if x)
    return (ui.kicker("Duo favori", mt=22) + f'<div style="display: flex; align-items: center; gap: 12px; margin-top: 10px">'
            f'<div style="font-family: {SERIF}; font-size: 40px; line-height: 1; color: {RED}">{n}</div>'
            f'<div><div style="font-weight: 700">{ui.lien_joueur(k, e(nom))}</div><div style="font-size: 12px; color: {MUTED}">'
            f'but{"s" if n > 1 else ""} ensemble · {e(sens)}</div></div></div>')


def cumul_analyses(lignes) -> str:
    """Lot C : total des matchs analysés d'un joueur (rapports PDF). Jamais ajouté aux totaux de saison."""
    if len(lignes) < 2:
        return ""
    n = len(lignes)
    som = lambda k: sum((jr.get(k) or 0) for _, _, _, jr in lignes)
    paire = lambda k: tuple(sum((jr.get(k) or (0, 0))[i] for _, _, _, jr in lignes) for i in (0, 1))
    do, dd = paire("duels_off"), paire("duels_def")
    gagnes, joues = do[0] + dd[0], do[1] + dd[1]
    tirs, cadres = som("tirs"), som("cadres")
    fs = sum((jr.get("fautes_subies") or 0) for _, _, _, jr in lignes)
    fc = sum((jr.get("fautes_commises") or 0) for _, _, _, jr in lignes)
    moy = lambda v: f"{fr(v / n)} / match"

    def case(v, lab, sous=None, rouge=False):
        return (f'<div style="background: {PAPER}; padding: 12px"><div style="font-family: {SERIF}; font-size: 28px; line-height: 1; color: {RED if rouge else INK}">{v}</div>'
                f'<div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em; color: {MUTED}; text-transform: uppercase">{lab}</div>'
                + (f'<div style="font-family: {COND}; font-size: 12px; color: {MUTED}; margin-top: 2px">{sous}</div>' if sous else "") + "</div>")

    cases = [case(tirs, "tirs", moy(tirs)),
             case(cadres, "cadrés", f"{round(100 * cadres / tirs)} % des tirs" if tirs else None),
             case(som("buts"), "buts", rouge=True),
             case(f"{gagnes}/{joues}", "duels gagnés", f"{round(100 * gagnes / joues)} %" if joues else None),
             case(som("recup"), "récup.", moy(som("recup"))),
             case(som("pertes"), "pertes", moy(som("pertes"))),
             case(som("inter"), "interceptions", moy(som("inter"))),
             case(som("passes_loupees"), "passes loupées", moy(som("passes_loupees"))),
             case(f"{fs}/{fc}", "fautes subies / commises")]
    return (f'<div style="background: {PAPER}; border: 1px solid {LINE}; border-radius: 4px; overflow: hidden; margin-top: 12px">'
            f'<div style="padding: 12px 14px; background: {RED}; color: #fff; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em">'
            f'CUMUL SUR SES {n} MATCHS ANALYSÉS</div>'
            f'<div style="display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1px; background: {LINE}">{"".join(cases)}</div></div>')


# ================================================================== club
def courbe_rangs(points, nb_clubs: int, w=420, h=170, playoffs=4, descente=2) -> str:
    """Évolution au classement journée par journée (1er en haut). points = [(journee, rang)]."""
    if len(points) < 2:
        return ""
    pg, pd_, ph, pb = 34, 14, 14, 26
    xs = lambda i: pg + i * (w - pg - pd_) / (len(points) - 1)
    ys = lambda r: ph + (r - 1) * (h - ph - pb) / max(nb_clubs - 1, 1)
    zone = (f'<rect x="{pg}" y="{ph - 6}" width="{w - pg - pd_}" height="{ys(playoffs) - ph + 6 + 6}" fill="{RED}" opacity="0.08"/>'
            f'<rect x="{pg}" y="{ys(nb_clubs - descente + 1) - 6}" width="{w - pg - pd_}" height="{h - pb - ys(nb_clubs - descente + 1) + 12}" fill="{INK}" opacity="0.07"/>')
    grille = "".join(f'<text x="{pg - 8}" y="{ys(r) + 4}" text-anchor="end" font-family="Archivo Narrow, Arial" font-size="11" fill="{MUTED}">{r}e</text>'
                     for r in (1, playoffs, nb_clubs))
    axe = "".join(f'<text x="{xs(i)}" y="{h - 6}" text-anchor="middle" font-family="Archivo Narrow, Arial" font-size="11" fill="{MUTED}">J{j}</text>'
                  for i, (j, _) in enumerate(points))
    ligne = " ".join(f"{xs(i):.1f},{ys(r):.1f}" for i, (_, r) in enumerate(points))
    pts = "".join(f'<circle cx="{xs(i):.1f}" cy="{ys(r):.1f}" r="{5 if i == len(points) - 1 else 3.5}" fill="{RED if i == len(points) - 1 else INK}"/>'
                  for i, (_, r) in enumerate(points))
    fin = points[-1][1]
    lab = f'<text x="{xs(len(points) - 1) - 9:.1f}" y="{ys(fin) + (16 if fin < 3 else -9):.1f}" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-weight="700" font-size="15" fill="{RED}">{fin}e</text>'
    svg = (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
           f'{zone}{grille}{axe}<polyline points="{ligne}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>{pts}{lab}</svg>')
    return ui.svg_img(svg, alt="Évolution au classement journée par journée") + _note(f'Zone rouge : top {playoffs}, play-offs. Zone grise : les {descente} places de descente.', 4)


def _bilan(b, ppm=True):
    if not b["n"]:
        return "aucun match"
    txt = f'{b["V"]}V {b["N"]}N {b["D"]}D'
    return txt + (f' · {fr(b["ppm"], 2)} pt/m' if ppm else "")


def _ligne(lib, club_html, d1_html, aide="", fort=False, mobile=False):
    """Une ligne du bloc Contexte : libellé | valeur du club | moyenne D1."""
    if mobile:
        return (f'<div style="padding: 10px 0; border-bottom: 1px solid {LINE}"><div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase">{lib}</div>'
                f'<div style="display: flex; justify-content: space-between; gap: 10px; align-items: baseline; margin-top: 4px">'
                f'<span style="font-weight: 600; {"color: " + RED if fort else ""}">{club_html}</span>'
                + (f'<span style="font-size: 12px; color: {MUTED}; text-align: right; white-space: nowrap">D1 : {d1_html}</span>' if d1_html else "") + "</div>"
                + (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 2px">{aide}</div>' if aide else "") + "</div>")
    return (f'<div style="display: grid; grid-template-columns: 210px minmax(0,1fr) 170px; gap: 12px; align-items: baseline; padding: 10px 0; border-bottom: 1px solid {LINE}">'
            f'<span style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase">{lib}'
            + (f'<span style="display: block; font-family: inherit; font-weight: 500; letter-spacing: 0; text-transform: none; font-size: 12px; color: {MUTED}">{aide}</span>' if aide else "")
            + f'</span><span style="font-weight: 600; {"color: " + RED if fort else ""}">{club_html}</span><span style="font-size: 13px; color: {MUTED}; text-align: right">{"D1 : " + d1_html if d1_html else ""}</span></div>')


def temps_score(t: dict, d1: dict) -> str:
    seg = lambda v, c, fg, lab: (f'<div style="flex: {v} 1 0; min-width: {30 if v else 0}px; background: {c}; color: {fg}; display: {"flex" if v else "none"}; align-items: center; '
                                 f'justify-content: center; font-family: {COND}; font-weight: 700; font-size: 12px" title="{lab}">{v} %</div>')
    return (f'<div style="display: flex; height: 26px; border-radius: 4px; overflow: hidden; border: 1px solid {LINE}">'
            f'{seg(t["devant"], INK, "#fff", "Devant")}{seg(t["egal"], SOFT, INK, "Égalité")}{seg(t["derriere"], RED, "#fff", "Derrière")}</div>'
            f'<div style="display: flex; justify-content: space-between; font-family: {COND}; font-size: 11px; letter-spacing: 0.06em; color: {MUTED}; margin-top: 4px">'
            f'<span>DEVANT</span><span>ÉGALITÉ</span><span>DERRIÈRE</span></div>'
            + _note(f'Moyenne D1 : {d1["devant"]} % devant, {d1["egal"]} % à égalité, {d1["derriere"]} % derrière.', 4))


def contexte_club(c: dict, duo, mobile=False) -> str:
    """Bloc Contexte d'une fiche club : chaque ligne comparée à la D1. duo = 1re ligne de contexte.duos(b, club) ou None."""
    L = lambda *a, **k: _ligne(*a, mobile=mobile, **k)
    pp, pc = c["premier_pour"], c["premier_contre"]
    h = (f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em; margin-bottom: 8px">TEMPS PASSÉ SELON LE SCORE</div>'
         + temps_score(c["temps"], c["d1_temps"]) + '<div style="height: 10px"></div>')
    h += L("Marque en premier", f'{_pl(pp["n"], "match")} · {_bilan(pp)}', f'{fr(c["d1_premier_pour"]["ppm"], 2)} pt/m')
    h += L("Encaisse en premier", f'{_pl(pc["n"], "match")} · {_bilan(pc)}', f'{fr(c["d1_premier_contre"]["ppm"], 2)} pt/m')
    m, am = c["mene"], c["a_mene"]
    h += L("Remontadas", f'{_pl(c["remontadas"], "victoire")} après avoir été mené', f'{fr(c["d1_remontadas"])} par club',
           aide=f'Mené dans {_pl(m["n"], "match")} : {_pl(m["pts"], "point")} pris', fort=c["remontadas"] > c["d1_remontadas"])
    h += L("Points perdus en menant", _pl(c["pts_perdus"], "point"), f'{fr(c["d1_pts_perdus"])} par club',
           aide=f'A mené dans {_pl(am["n"], "match")}', fort=c["pts_perdus"] > c["d1_pts_perdus"])
    mtc, mtd = c["mi_temps"], c["d1_mi_temps"]
    for k, lib in (("devant", "Devant à la pause"), ("egal", "Égalité à la pause"), ("derriere", "Mené à la pause")):
        if mtc[k]["n"]:
            h += L(lib, f'{_pl(mtc[k]["n"], "match")} · {_bilan(mtc[k], False)}', f'{fr(mtd[k]["ppm"], 2)} pt/m')
    h += L("Buts 36’-40’", f'{_pl(c["fin_pour"], "marqué")} · {_pl(c["fin_contre"], "encaissé")}', f'{fr(c["d1_fin"])} marqués par club')
    if c["encaisses"]:
        h += L("Réaction en 2 min", f'{c["reactions"]} fois sur {_pl(c["encaisses"], "but")} encaissés ({c["pct_reaction"]} %)', f'{c["d1_pct_reaction"]} %',
               aide="But marqué dans les 2 minutes après un but encaissé", fort=(c["pct_reaction"] or 0) > (c["d1_pct_reaction"] or 0))
    rare = c["clean_sheets"] or c["sans_marquer"]
    h += L("Sans encaisser / sans marquer", f'{c["clean_sheets"]} / {c["sans_marquer"]}',
           f'{c["d1_clean_sheets"]} / {c["d1_sans_marquer"]} en {c["d1_matchs"]} matchs', aide="Nombre de matchs. Rare en futsal", fort=bool(rare))
    if c["top_buteur"]:
        nom, n = c["top_buteur"]
        h += L("Buteurs différents", _pl(c["nb_buteurs"], "buteur"), f'{fr(c["d1_nb_buteurs"])} par club', aide="")
        h += L("Dépendance au meilleur buteur", f'{c["dependance"]} % des buts', f'{c["d1_dependance"]} %',
               aide=f"Part des buts du club marqués par {e(nom)}", fort=(c["dependance"] or 0) > (c["d1_dependance"] or 0))
    if duo is not None:
        h += L("Duo du club", f'{ui.lien_joueur(duo.id_passeur, e(duo.passeur))} pour {ui.lien_joueur(duo.id_buteur, e(duo.buteur))} : {_pl(int(duo.n), "but")}', "")
    return h + _note("Chiffres tirés des buts et passes de la saison. pt/m : points par match. En rouge : au-dessus de la moyenne D1, ou fait rare.")


# ================================================================== Une : records et séries
def record_ligne(r, compact=False) -> str:
    return (f'<div style="display: grid; grid-template-columns: {"58px" if compact else "64px"} minmax(0,1fr); gap: 10px; align-items: center; padding: 8px {"16px" if compact else "0"}; border-bottom: 1px solid {LINE}">'
            f'<span style="font-family: {SERIF}; font-size: {20 if compact else 22}px; line-height: 1; color: {RED}; white-space: nowrap">{e(r["valeur"])}</span>'
            f'<span style="min-width: 0"><span style="display: block; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase">{e(r["libelle"])}</span>'
            f'<span style="display: block; font-size: 12px; color: {MUTED}; {"white-space: nowrap; overflow: hidden; text-overflow: ellipsis" if compact else ""}">{e(r["detail"])}</span></span></div>')


# ================================================================== méthodologie
DEFINITIONS = [
    "Points rapportés : points que l’équipe du joueur aurait perdus si on retirait ses buts du match (exemple : 1 but dans une victoire 3-2 = 2 points rapportés).",
    "But vainqueur : dans une victoire sur le score de 5-3, le 4e but du vainqueur, celui après lequel l’adversaire ne revient plus. Égalisateur : but qui remet les deux équipes à égalité. "
    "Donne l’avantage : but qui fait passer de l’égalité à devant, hors 1er but du match.",
    "Temps passé devant, à égalité, derrière : calculé minute par minute à partir de la minute de chaque but, sur 40 minutes. Réaction : but marqué dans les 2 minutes après un but encaissé.",
    "Remontada : victoire après avoir été mené au moins une fois. Points perdus en menant : points laissés dans les matchs où le club a mené au moins une fois. Buts 36’-40’ : 5 dernières minutes.",
    "Records : en cas d’égalité, le premier en date est affiché. Les séries en cours sont comptées sur les matchs du club jusqu’à la dernière journée.",
]


def series_ligne(series, pad="0") -> str:
    """Séries en cours des clubs, condensées en un seul bloc (au lieu d'une ligne par série)."""
    if not series:
        return ""
    lib = {"victoires": "victoires de suite", "invaincu": "sans défaite", "sans_victoire": "sans victoire"}
    items = "".join(f'<div style="display: flex; align-items: baseline; gap: 8px"><span style="font-family: {SERIF}; font-size: 20px; line-height: 1; color: {RED}; min-width: 18px">{e(r["valeur"])}</span>'
                    f'<span style="font-size: 13px"><b>{e(lib[r["cle"]])}</b> · {e(r["detail"])}</span></div>' for r in series)
    return (f'<div style="padding: {pad}"><div style="background: {PAPER}; border: 1px solid {LINE}; border-radius: 4px; padding: 10px 12px">'
            f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.1em; color: {MUTED}; margin-bottom: 6px">SÉRIES EN COURS</div>'
            f'<div style="display: flex; flex-direction: column; gap: 6px">{items}</div></div></div>')
