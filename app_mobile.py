"""
D1 Futsal · appli mobile.
Lancer en local : streamlit run app_mobile.py
Adresses partageables : /matchs?j=3 · /match?j=3&dom=GARGES · /classements?vue=passeurs
                        /club?id=LAVAL · /joueur?id=bilal-bakkali · /methodo
La navigation se fait sans rechargement (voir nav.py).
"""
from __future__ import annotations
import os

import pandas as pd
import streamlit as st

import config as C
import data
import nav
from nav import Sortie
from textes import charger_textes
import components as ui
from components import e, fr
from theme import CSS, PAPER, INK, RED, MUTED, LINE, SERIF, COND

st.set_page_config(page_title="D1 Futsal", page_icon="⚽", layout="centered", initial_sidebar_state="collapsed")
st.html(CSS + nav.CSS_NAV)
nav.reset()

ORIG = {"attaque placée": "Attaque placée", "attaque rapide": "Attaque rapide", "transition off": "Transition off",
        "corner": "Corner", "touche off": "Touche off", "touche def": "Touche déf.", "coup franc": "Coup franc",
        "jet franc": "Jet franc", "power play": "Power play", "penalty": "Penalty", "csc": "CSC"}


# ------------------------------------------------------------------ données (cache invalidé si un fichier change)
def _empreinte():
    fichiers = [C.FICHIER_BUTS, C.FICHIER_PASSES, C.FICHIER_FICHES, C.FICHIER_TEXTES]
    return tuple(os.path.getmtime(f) if os.path.exists(f) else 0 for f in fichiers)


@st.cache_resource(show_spinner=False)
def _base(_cle):
    return data.charger(), charger_textes()


base, TEXTES = _base(_empreinte())
qp = st.query_params

NOMS = {r.club_court: (r.nom_affiche if isinstance(getattr(r, "nom_affiche", None), str) and r.nom_affiche
                       else C.NOMS_CLUBS.get(r.club_court, r.club_court)) for r in base.clubs.itertuples()}
JREF = base.joueurs.drop_duplicates("id_joueur").set_index("id_joueur")
CLASSEMENT = base.classement()
STATS = base.stats_joueurs()
DERNIERE = max(base.journees) if base.journees else 1


def param_int(nom, defaut):
    try:
        return int(qp.get(nom, defaut))
    except (TypeError, ValueError):
        return defaut


def param_choix(nom, choix, defaut):
    v = qp.get(nom, defaut)
    return v if v in choix else defaut


# ------------------------------------------------------------------ cadre commun
def topnav(active):
    items = [("une", "La Une", "une"), ("match", "Matchs", "matchs"), ("class", "Classements", "classements"),
             ("club", "Clubs", "clubs"), ("joueur", "Joueurs", "joueurs")]
    o = Sortie()
    o.rangee([(ui.nav_item(k, lab, k == active), cible, {}) for k, lab, cible in items], key="topnav")


def entete(o: Sortie, titre, sous=None, retour=None):
    """Titre de page, avec flèche retour cliquable si `retour` = (page, params)."""
    items = []
    if retour:
        items.append((ui.back_btn(), retour[0], retour[1], "content"))
    items.append((ui.titre_bar(titre, sous), None, None, "stretch"))
    o.rangee(items, style="bar")


def onglets(o: Sortie, page, base_params, liste, actif):
    o.rangee([(ui.tab_item(lab, k == actif), page, {**base_params, "onglet": k}, "content") for k, lab in liste], style="tabs")


def pieds(o: Sortie):
    o.add(ui.footer())
    o.lien(f'<div style="padding: 0 16px 8px; font-size: 11px; color: {MUTED}; text-decoration: underline">Méthodologie et sources</div>', "methodo")
    o.fin()


# ================================================================== LA UNE
def page_une():
    topnav("une")
    o = Sortie()
    j = param_int("j", DERNIERE)
    m = base.matchs[base.matchs.journee == j]
    b = base.buts[base.buts.journee == j]
    entete(o, "D1 Futsal", f"Saison {C.SAISON}")
    o.rangee([(ui.pill_item(f"J{x}", x == j), "une", {"j": x}, "content") for x in base.journees], style="pills")
    if m.empty:
        o.add(ui.section(ui.empty("Pas encore de match pour cette journée."))); o.fin(); return
    top = m.sort_values(["nb_buts", "dom"], ascending=[False, True]).iloc[0]
    titre, chapo = TEXTES.get(f"une:J{j}"), TEXTES.get(f"match:J{j}:{top.dom}")
    o.add(ui.section(ui.kicker(f"La Une · Journée {j}"), pad="4px 16px 0"))
    card = (f'<div style="margin: 12px 16px 0; background: {INK}; color: #fff; border-radius: 12px; padding: 18px 16px 16px">'
            f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #F2B8C0">Le match de la journée</div>'
            f'<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 12px">'
            f'<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; width: 96px">{ui.logo_or_badge(top.dom, 44, 12, False)}<span style="font-weight: 600; font-size: 13px">{e(NOMS[top.dom])}</span></div>'
            f'<div style="font-family: {SERIF}; font-size: 56px; line-height: 1">{top.bd}-{top.be}</div>'
            f'<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; width: 96px">{ui.logo_or_badge(top.ext, 44, 12, False)}<span style="font-weight: 600; font-size: 13px">{e(NOMS[top.ext])}</span></div></div>'
            + (f'<div style="font-family: {SERIF}; font-size: 22px; line-height: 1.15; margin-top: 14px">{e(titre)}</div>' if titre else "")
            + (f'<div style="font-size: 13px; color: #D9D2C6; margin-top: 6px">{e(chapo)}</div>' if chapo else "") + "</div>")
    o.lien(card, "match", j=j, dom=top.dom)
    ecart = m.assign(d=(m.bd - m.be).abs()).sort_values("d", ascending=False).iloc[0]
    o.add(f'<div style="padding: 0 16px">' + ui.tiles(ui.tile(len(b), f"buts en J{j}", "red"), ui.tile(fr(len(b) / len(m)), "buts / match"),
          ui.tile(f"{max(ecart.bd, ecart.be)}-{min(ecart.bd, ecart.be)}", "plus large écart"), mt=10) + "</div>")
    o.add(f'<div style="padding: 22px 16px 8px">{ui.kicker(f"Résultats · J{j}")}</div><div style="border-top: 1px solid {LINE}"></div>')
    for r in m.sort_values("nb_buts", ascending=False).itertuples():
        o.lien(ui.match_row(r, NOMS), "match", j=r.journee, dom=r.dom)

    def podium(df, col, titre, vue):
        o.add(ui.section(ui.kicker(titre) + '<div style="height: 12px"></div>'))
        cartes = []
        for i, r in enumerate(df.head(3).itertuples()):
            dark = i == 0
            nom = r.joueur.split()
            cartes.append((f'<div style="height: 100%; box-sizing: border-box; background: {INK if dark else PAPER}; color: {"#fff" if dark else INK}; border: 1.5px solid {INK}; '
                           f'border-radius: 10px; padding: 12px 10px; display: flex; flex-direction: column; gap: 6px">'
                           f'<div style="font-family: {SERIF}; font-size: 36px; line-height: 1">{getattr(r, col)}</div>'
                           f'<div style="font-weight: 700; font-size: 13px; line-height: 1.15">{e(nom[0])}<br>{e(" ".join(nom[1:3]))}</div>'
                           f'<div style="font-family: {COND}; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: {"#E9E2D5" if dark else MUTED}">{e(NOMS.get(r.club, r.club))}</div></div>',
                           "joueur", {"id": r.id_joueur}))
        with st.container(key=f"pad-{vue}"):
            o.rangee(cartes, style="cards")
        o.lien(f'<div style="display: flex; justify-content: flex-end; padding: 10px 16px 0; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em; color: {RED}">TOUT LE CLASSEMENT</div>', "classements", vue=vue)
    podium(STATS[STATS.Buts > 0], "Buts", "Meilleurs buteurs", "buteurs")
    podium(STATS[STATS.Passes > 0].sort_values(["Passes", "Buts"], ascending=False), "Passes", "Meilleurs passeurs", "passeurs")
    o.add(f'<div style="padding: 22px 16px 6px">{ui.kicker("Classement")}</div>')
    for r in CLASSEMENT.head(5).itertuples():
        o.lien(f'<div style="display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-bottom: 1px solid {LINE}; {"box-shadow: inset 4px 0 0 " + RED if r.Rg <= C.NB_PLAYOFFS else ""}">'
               f'<span style="width: 18px; font-family: {COND}; font-weight: 700">{r.Rg}</span>{ui.logo_or_badge(r.club, 24, 8)}'
               f'<span style="flex: 1; font-weight: 600">{e(NOMS[r.club])}</span><span style="font-family: {COND}; color: {MUTED}; width: 34px; text-align: right">{r.Diff:+d}</span>'
               f'<span style="font-family: {SERIF}; font-size: 18px; width: 28px; text-align: right">{r.Pts}</span></div>', "club", id=r.club)
    o.lien(f'<div style="display: flex; align-items: center; justify-content: center; min-height: 48px; font-family: {COND}; font-weight: 700; font-size: 13px; letter-spacing: 0.08em; color: {RED}">CLASSEMENT COMPLET</div>', "classements")
    pieds(o)


# ================================================================== MATCHS
def page_matchs():
    topnav("match")
    o = Sortie()
    j = param_int("j", DERNIERE)
    entete(o, "Matchs", f"Journée {j}")
    o.rangee([(ui.pill_item(f"J{x}", x == j), "matchs", {"j": x}, "content") for x in base.journees], style="pills")
    o.add(f'<div style="border-top: 1px solid {LINE}"></div>')
    for r in base.matchs[base.matchs.journee == j].itertuples():
        o.lien(ui.match_row(r, NOMS), "match", j=r.journee, dom=r.dom)
    pieds(o)


def page_match():
    topnav("match")
    o = Sortie()
    j, dom = param_int("j", DERNIERE), qp.get("dom")
    mm = base.matchs[(base.matchs.journee == j) & (base.matchs.dom == dom)]
    if mm.empty:
        entete(o, "Match", retour=("matchs", {})); o.add(ui.section(ui.empty("Match introuvable."))); o.fin(); return
    m = mm.iloc[0]
    b = base.match(j, dom)
    onglet = param_choix("onglet", ["resume", "timeline", "stats", "compos"], "resume")

    def buteurs(club, align):
        d = b[b.club_marque == club]
        court = lambda n: n if n == "CSC" or len(n.split()) == 1 else " ".join(n.split()[1:])
        parts = [f'{e(court(n))} ' + " ".join(f"{x}\u2019" for x in g.minute) for n, g in d.groupby("buteur", sort=False)]
        return f'<div style="text-align: {align}">{" · ".join(parts)}</div>'
    entete(o, f"{NOMS[m.dom]} - {NOMS[m.ext]}", f"Journée {j} · Terminé", retour=("matchs", {"j": j}))
    equipe = lambda club, dark: (f'<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; padding-top: 18px">'
                                 f'{ui.logo_or_badge(club, 52, 13, dark)}<span style="font-weight: 600; text-align: center">{e(NOMS[club])}</span></div>')
    score = (f'<div style="text-align: center; padding-top: 18px"><div style="font-family: {SERIF}; font-size: 60px; line-height: 1">{m.bd}<span style="color: {MUTED}">-</span>{m.be}</div>'
             f'<div style="font-family: {COND}; font-weight: 600; font-size: 12px; color: {MUTED}; letter-spacing: 0.08em; margin-top: 4px">MI-TEMPS {m.mt_d}-{m.mt_e}</div></div>')
    with st.container(key="scorebox"):
        o.rangee([(equipe(m.dom, True), "club", {"id": m.dom}, 100), (score, None, None, "stretch"), (equipe(m.ext, False), "club", {"id": m.ext}, 100)], style="cards")
        o.add(f'<div style="display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 12px; padding: 12px 16px 14px; font-size: 12px; color: {MUTED}">'
              f'{buteurs(m.dom, "right")}{buteurs(m.ext, "left")}</div>')
        o.flush()
    onglets(o, "match", {"j": j, "dom": dom}, [("resume", "Résumé"), ("timeline", "Timeline"), ("stats", "Stats"), ("compos", "Compos")], onglet)
    if onglet == "resume":
        txt = TEXTES.get(f"match:J{j}:{dom}")
        n_d = b[(b.club_marque == m.dom) & b.id_buteur.notna()].id_buteur.nunique()
        n_e = b[(b.club_marque == m.ext) & b.id_buteur.notna()].id_buteur.nunique()
        ess = f'<div style="font-family: {SERIF}; font-size: 21px; line-height: 1.2; margin-top: 10px">{e(txt)}</div>' if txt else ""
        o.add(ui.section(ui.kicker("L\u2019essentiel") + ess + ui.tiles(ui.tile(len(b), "buts", "dark"), ui.tile(f"{n_d}-{n_e}", "buteurs différents"),
                                                                       ui.tile(int(b.id_passeur.notna().sum()), "buts avec passe", "red")), pad="16px 16px 0"))
        o.add(ui.section(ui.kicker("Score minute par minute") + f'<div style="margin-top: 10px">{ui.score_progressif(b, m.dom, m.ext, NOMS)}</div>'))
        o_d, o_e = b[b.club_marque == m.dom].origine_but.value_counts(), b[b.club_marque == m.ext].origine_but.value_counts()
        keys = sorted(set(o_d.index) | set(o_e.index), key=lambda k: -(o_d.get(k, 0) + o_e.get(k, 0)))
        o.add(ui.section(ui.kicker("D\u2019où viennent les buts") + '<div style="margin-top: 10px">'
                         + ui.mirror([(ORIG.get(k, k), int(o_d.get(k, 0)), int(o_e.get(k, 0))) for k in keys], NOMS[m.dom], NOMS[m.ext]) + "</div>"))
    elif onglet == "timeline":
        o.add(ui.section(ui.kicker(f"Les {len(b)} buts"), pad="16px 16px 6px"))
        mt = False
        for r in b.itertuples():
            if r.periode == 2 and not mt:
                o.add(f'<div style="display: flex; align-items: center; gap: 10px; margin: 6px 16px"><div style="flex: 1; height: 1px; background: {INK}"></div>'
                      f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.12em">MI-TEMPS · {m.mt_d}-{m.mt_e}</div><div style="flex: 1; height: 1px; background: {INK}"></div></div>')
                mt = True
            home = r.club_marque == m.dom
            passe = f'<span style="font-size: 12px">passe {e(r.passeur)}</span>' if isinstance(r.passeur, str) else ""
            card = (f'<div style="display: flex; flex-direction: column; gap: 2px; {"align-items: flex-end; text-align: right" if home else ""}">'
                    f'<span style="font-weight: 700; font-size: 14px">{e(r.buteur)}</span>{passe}'
                    f'<span style="font-family: {COND}; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: {MUTED}">{e(ORIG.get(r.origine_but, str(r.origine_but)))}</span></div>')
            mid = (f'<div style="display: flex; flex-direction: column; align-items: center"><span style="font-family: {COND}; font-weight: 700; font-size: 12px; color: {RED}">{r.minute}\u2019</span>'
                   f'<span style="font-family: {SERIF}; font-size: 17px; line-height: 1.1">{r.score_dom_apres}-{r.score_ext_apres}</span></div>')
            ligne = (f'<div style="display: grid; grid-template-columns: minmax(0,1fr) 58px minmax(0,1fr); align-items: center; gap: 6px; padding: 8px 16px; border-bottom: 1px dashed {LINE}">'
                     f'{card if home else "<div></div>"}{mid}{"<div></div>" if home else card}</div>')
            if r.id_buteur:
                o.lien(ligne, "joueur", id=r.id_buteur)
            else:
                o.add(ligne)
    elif onglet == "stats":
        rows = []
        for lab, f in [("Buts 1re mi-temps", lambda d: (d.periode == 1).sum()), ("Buts 2e mi-temps", lambda d: (d.periode == 2).sum()),
                       ("Buts avec passe", lambda d: d.id_passeur.notna().sum()), ("Buteurs différents", lambda d: d.id_buteur.nunique()),
                       ("Buts 5 dernières min.", lambda d: (d.minute > 35).sum())]:
            rows.append((lab, int(f(b[b.club_marque == m.dom])), int(f(b[b.club_marque == m.ext]))))
        o.add(ui.section(ui.kicker("Face-à-face") + '<div style="margin-top: 10px">' + ui.mirror(rows, NOMS[m.dom], NOMS[m.ext], mid_w=130) + "</div>", pad="16px 16px 0"))
        o.add(ui.section(ui.empty("Stats détaillées (tirs, duels, pertes, gardiens) disponibles quand le match est analysé.")))
    else:
        o.add(ui.section(ui.empty("Compositions à venir."), pad="16px 16px 0"))
    pieds(o)


# ================================================================== CLASSEMENTS
def page_classements():
    topnav("class")
    o = Sortie()
    vue = param_choix("vue", ["equipes", "buteurs", "passeurs", "bp"], "equipes")
    lieu = param_choix("lieu", ["tous", "dom", "ext"], "tous")
    entete(o, "Classements", f"D1 · Après J{DERNIERE}")
    o.rangee([(ui.seg_item(lab, k == vue), "classements", {"vue": k}) for k, lab in
              [("equipes", "Équipes"), ("buteurs", "Buteurs"), ("passeurs", "Passeurs"), ("bp", "B+P")]], style="seg")
    if vue == "equipes":
        o.rangee([(ui.pill_item(lab, k == lieu), "classements", {"vue": "equipes", "lieu": k}, "content") for k, lab in
                  [("tous", "Général"), ("dom", "Domicile"), ("ext", "Extérieur")]], style="pills")
        grid = "grid-template-columns: 20px 26px minmax(0,1fr) 20px 20px 20px 20px 34px 30px"
        o.add(f'<div style="display: grid; {grid}; gap: 6px; padding: 6px 12px; font-family: {COND}; font-weight: 700; font-size: 11px; color: {MUTED}; border-bottom: 2px solid {INK}">'
              f'<span>#</span><span></span><span>ÉQUIPE</span><span style="text-align:center">J</span><span style="text-align:center">G</span><span style="text-align:center">N</span>'
              f'<span style="text-align:center">P</span><span style="text-align:right">DIFF</span><span style="text-align:right">PTS</span></div>')
        for r in base.classement(lieu).itertuples():
            nb = len(base.clubs)
            zone = RED if (lieu == "tous" and r.Rg <= C.NB_PLAYOFFS) else (INK if (lieu == "tous" and r.Rg > nb - C.NB_DESCENTE) else None)
            o.lien(f'<div style="display: grid; {grid}; gap: 6px; align-items: center; padding: 10px 12px; border-bottom: 1px solid {LINE}; background: {PAPER}; '
                   f'{"box-shadow: inset 4px 0 0 " + zone if zone else ""}"><span style="font-family: {COND}; font-weight: 700">{r.Rg}</span>{ui.logo_or_badge(r.club, 24, 8)}'
                   f'<span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(NOMS[r.club])}</span>'
                   + "".join(f'<span style="font-family: {COND}; color: {MUTED}; text-align: center">{v}</span>' for v in (r.J, r.G, r.N, r.P))
                   + f'<span style="font-family: {COND}; text-align: right">{r.Diff:+d}</span><span style="font-family: {SERIF}; font-size: 19px; text-align: right">{r.Pts}</span></div>',
                   "club", id=r.club)
        leg = lambda c, t: f'<span style="display: inline-flex; align-items: center; gap: 6px"><span style="width: 4px; height: 14px; background: {c}"></span>{t}</span>'
        o.add(f'<div style="display: flex; flex-wrap: wrap; gap: 14px; padding: 12px 16px 4px; font-size: 12px; color: {MUTED}">'
              f'{leg(RED, f"Top {C.NB_PLAYOFFS} : play-offs")}{leg(INK, f"{C.NB_DESCENTE} derniers : descente en D2")}</div>'
              f'<div style="padding: 4px 16px; font-size: 12px; color: {MUTED}">Départage : points, différence de buts, buts marqués.</div>')
    else:
        col, tri = {"buteurs": ("Buts", ["Buts", "Passes"]), "passeurs": ("Passes", ["Passes", "Buts"]), "bp": ("B+P", ["B+P", "Buts"])}[vue]
        d = STATS[STATS[col] > 0].sort_values(tri + ["joueur"], ascending=[False, False, True])
        o.add(f'<div style="margin-top: 12px; border-top: 1px solid {LINE}"></div>')
        rang, prev = 0, None
        for i, (_, r) in enumerate(d.iterrows(), 1):
            v = int(r[col])
            rang = i if v != prev else rang
            prev = v
            o.lien(ui.rank_row(rang, r.joueur, f"{NOMS.get(r.club, r.club)} · {r.Buts} b · {r.Passes} p", v, rang == 1), "joueur", id=r.id_joueur)
    pieds(o)


# ================================================================== CLUBS
def page_clubs():
    topnav("club")
    o = Sortie()
    entete(o, "Clubs", "D1 Futsal")
    o.add('<div style="height: 16px"></div>')
    clubs = CLASSEMENT.sort_values("club")
    for k in range(0, len(clubs), 2):
        paire = []
        for r in clubs.iloc[k:k + 2].itertuples():
            paire.append((f'<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px 8px; background: {PAPER}; border: 1.5px solid {INK}; border-radius: 12px">'
                          f'{ui.logo_or_badge(r.club, 48, 12)}<span style="font-weight: 700; text-align: center">{e(NOMS[r.club])}</span>'
                          f'<span style="font-family: {COND}; font-size: 12px; color: {MUTED}">{r.Rg}e · {r.Pts} pts</span></div>', "club", {"id": r.club}))
        o.rangee(paire, style="grid")
    pieds(o)


def page_club():
    topnav("club")
    o = Sortie()
    club = qp.get("id")
    if club not in NOMS:
        entete(o, "Club", retour=("clubs", {})); o.add(ui.section(ui.empty("Club introuvable."))); o.fin(); return
    onglet = param_choix("onglet", ["resume", "effectif", "buts", "matchs"], "resume")
    s = base.stats_club(club)
    cl = s["classement"]
    info = base.clubs.set_index("club_court").loc[club]
    meta = " · ".join(x for x in [info.get("salle"), f"Coach {info.get('coach')}" if isinstance(info.get("coach"), str) else None] if isinstance(x, str) and x)
    entete(o, "Club", retour=("clubs", {}))
    o.add(f'<section style="background: {INK}; color: #fff; padding: 18px 16px 16px"><div style="display: flex; align-items: center; gap: 14px">'
          f'{ui.logo_or_badge(club, 64, 14, False)}<div><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{e(NOMS[club])}</div>'
          + (f'<div style="font-size: 13px; color: #D9D2C6; margin-top: 6px">{e(meta)}</div>' if meta else "") + "</div></div>"
          f'<div style="display: flex; gap: 8px; margin-top: 16px">'
          f'<div style="flex: 1; border: 1.5px solid #fff; border-radius: 10px; padding: 10px"><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{cl["Rg"]}<sup style="font-size: 14px">e</sup></div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em; color: #D9D2C6">CLASSEMENT</div></div>'
          f'<div style="flex: 1; border: 1.5px solid #fff; border-radius: 10px; padding: 10px"><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{cl["Pts"]}</div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em; color: #D9D2C6">POINTS</div></div>'
          f'<div style="flex: 1; background: {RED}; border-radius: 10px; padding: 10px"><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{cl["BP"]}-{cl["BC"]}</div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em">BUTS POUR-CONTRE</div></div></div>'
          + (f'<div style="font-size: 12px; color: #D9D2C6; margin-top: 8px">Meilleure défense de D1</div>' if CLASSEMENT.BC.min() == cl["BC"] else "") + "</section>")
    onglets(o, "club", {"id": club}, [("resume", "Résumé"), ("effectif", "Effectif"), ("buts", "Buts"), ("matchs", "Matchs")], onglet)
    if onglet == "resume":
        o.add(ui.section(ui.kicker("Forme") + '<div style="display: flex; gap: 6px; margin-top: 10px">' + "".join(ui.form_chip(x, 30) for x in cl["forme"]) + "</div>", pad="16px 16px 0"))
        o.add(ui.section(ui.kicker("Buts par tranche de 5 min") + '<div style="margin-top: 10px">' + ui.tranches_miroir(s["tranches_marques"], s["tranches_encaisses"]) + "</div>"))
        o.add(ui.section(ui.kicker("Joueurs clés"), pad="22px 16px 4px"))
        top = STATS[STATS.club == club].sort_values(["B+P", "Buts"], ascending=False).head(5)
        for i, (_, r) in enumerate(top.iterrows(), 1):
            o.lien(ui.rank_row(i, r.joueur, f"{r.Buts} buts · {r.Passes} passes", r["B+P"], i == 1), "joueur", id=r.id_joueur)
    elif onglet == "effectif":
        st_ = STATS.set_index("id_joueur")
        o.add(ui.section(ui.kicker("Effectif") + f'<div style="display: grid; grid-template-columns: 30px minmax(0,1fr) 34px 34px; gap: 8px; padding: 10px 0 6px; border-bottom: 2px solid {INK}; '
                         f'font-family: {COND}; font-weight: 700; font-size: 11px; color: {MUTED}"><span>N°</span><span>JOUEUR</span><span style="text-align:center">B</span><span style="text-align:center">P</span></div>', pad="16px 16px 0"))
        for r in base.joueurs[base.joueurs.club_court == club].itertuples():
            bts, pas = int(st_.Buts.get(r.id_joueur, 0)), int(st_.Passes.get(r.id_joueur, 0))
            poste = r.poste if isinstance(getattr(r, "poste", None), str) else ""
            num = str(r.numero).replace(".0", "") if pd.notna(getattr(r, "numero", None)) else ""
            o.lien(f'<div style="display: grid; grid-template-columns: 30px minmax(0,1fr) 34px 34px; gap: 8px; align-items: center; padding: 10px 16px; border-bottom: 1px solid {LINE}">'
                   f'<span style="font-family: {COND}; color: {MUTED}">{e(num)}</span><span><span style="display: block; font-weight: 600">{e(r.nom_affiche)}</span>'
                   f'<span style="font-size: 12px; color: {MUTED}">{e(poste)}</span></span><span style="font-family: {SERIF}; font-size: 17px; text-align: center">{bts}</span>'
                   f'<span style="font-family: {SERIF}; font-size: 17px; text-align: center; color: {MUTED}">{pas}</span></div>', "joueur", id=r.id_joueur)
    elif onglet == "buts":
        for titre, orig, pad in [("Comment le club marque", s["origines"], "16px 16px 0"), ("Comment le club encaisse", s["origines_encaisses"], "22px 16px 0")]:
            o.add(ui.section(ui.kicker(titre) + '<div style="margin-top: 12px">'
                             + ui.hbars([(ORIG.get(k, k), v, RED if i == 0 else INK) for i, (k, v) in enumerate(orig.items())], max(orig.values()) if orig else 1) + "</div>", pad=pad))
    else:
        o.add(ui.section(ui.kicker("Matchs"), pad="16px 16px 4px"))
        for r in s["matchs"].itertuples():
            home = r.dom == club
            f_, a_ = (r.bd, r.be) if home else (r.be, r.bd)
            opp = r.ext if home else r.dom
            res = "V" if f_ > a_ else ("N" if f_ == a_ else "D")
            o.lien(f'<div style="display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-bottom: 1px solid {LINE}">'
                   f'<span style="font-family: {COND}; font-weight: 700; color: {MUTED}; width: 26px">J{r.journee}</span><span style="font-family: {COND}; font-size: 12px; color: {MUTED}; width: 28px">{"DOM" if home else "EXT"}</span>'
                   f'{ui.logo_or_badge(opp, 24, 8)}<span style="flex: 1; font-weight: 600">{e(NOMS[opp])}</span><span style="font-family: {SERIF}; font-size: 18px">{f_}-{a_}</span>{ui.form_chip(res, 22)}</div>',
                   "match", j=r.journee, dom=r.dom)
    pieds(o)


# ================================================================== JOUEURS
def page_joueurs():
    topnav("joueur")
    o = Sortie()
    entete(o, "Joueurs", "Recherche")
    o.flush()
    q = st.text_input("Rechercher un joueur", placeholder="Nom, prénom ou surnom…")
    d = STATS[STATS.joueur.str.contains(q.strip(), case=False, regex=False)] if q else STATS.sort_values(["B+P", "Buts"], ascending=False).head(30)
    o.add(ui.section(ui.kicker("Résultats" if q else "Les plus décisifs"), pad="10px 16px 6px"))
    for i, (_, r) in enumerate(d.iterrows(), 1):
        o.lien(ui.rank_row(i, r.joueur, f"{NOMS.get(r.club, r.club)} · {r.Buts} b · {r.Passes} p", r["B+P"]), "joueur", id=r.id_joueur)
    if q and d.empty:
        o.add(ui.section(ui.empty("Aucun joueur trouvé.")))
    pieds(o)


def page_joueur():
    topnav("joueur")
    o = Sortie()
    i = qp.get("id")
    if i not in JREF.index:
        entete(o, "Joueur", retour=("joueurs", {})); o.add(ui.section(ui.empty("Joueur introuvable."))); o.fin(); return
    j = JREF.loc[i]
    club = j.club_court
    onglet = param_choix("onglet", ["resume", "buts", "passes"], "resume")
    s = STATS.set_index("id_joueur").loc[i] if i in set(STATS.id_joueur) else None
    bj = base.buts[base.buts.id_buteur == i].sort_values(["journee", "minute"])
    pj = base.buts[base.buts.id_passeur == i].sort_values(["journee", "minute"])
    num = f"N° {int(j.numero)}" if pd.notna(j.get("numero")) else None
    poste = j.get("poste") if isinstance(j.get("poste"), str) else None
    sur = " · ".join(x for x in [num, poste] if x)
    entete(o, "Joueur", retour=("joueurs", {}))
    o.add(f'<section style="padding: 16px; display: flex; gap: 14px; align-items: center; background: {PAPER}; border-bottom: 1px solid {LINE}">{ui.photo(i)}'
          f'<div style="flex: 1; min-width: 0">' + (f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.12em; color: {RED}">{e(sur)}</div>' if sur else "")
          + f'<div style="font-family: {SERIF}; font-size: 28px; line-height: 1.02; margin-top: 4px">{e(j.nom_affiche)}</div></div></section>')
    o.lien(f'<div style="display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: {PAPER}; border-bottom: 1px solid {LINE}; font-weight: 600">'
           f'{ui.logo_or_badge(club, 24, 8)}{e(NOMS.get(club, club))}<span style="margin-left: auto">{ui.icon("chev", 16, MUTED)}</span></div>', "club", id=club)
    onglets(o, "joueur", {"id": i}, [("resume", "Résumé"), ("buts", "Buts"), ("passes", "Passes")], onglet)
    if onglet == "resume":
        nb, npas = len(bj), len(pj)
        rang = int((STATS.Buts > nb).sum()) + 1
        mj = int(CLASSEMENT.set_index("club").J.get(club, 0))
        o.add(ui.section(f'<div style="display: flex; align-items: flex-end; gap: 14px"><div style="font-family: {SERIF}; font-size: 96px; line-height: 0.85; color: {RED}">{nb}</div>'
                         f'<div style="padding-bottom: 6px"><div style="font-family: {COND}; font-weight: 700; font-size: 16px; letter-spacing: 0.1em">BUT{"S" if nb > 1 else ""}</div>'
                         f'<div style="font-size: 13px; color: {MUTED}">{"Meilleur buteur de D1" if rang == 1 and nb else (f"{rang}e buteur de D1" if nb else "Pas encore buteur")}</div></div></div>'
                         + ui.tiles(ui.tile(npas, "passes déc.", "dark"), ui.tile(nb + npas, "buts + passes"), ui.tile(fr(nb / mj, 2) if mj else "-", "buts / match"))
                         + ui.tiles(ui.tile(int(s.Pct_buts_club) if s is not None else 0, "% buts du club"), ui.tile(int(bj.ouverture.sum()), "buts d\u2019ouverture"),
                                    ui.tile(f"{int((bj.periode == 1).sum())}/{int((bj.periode == 2).sum())}", "1re / 2e MT"), mt=8), pad="16px 16px 0"))
        if nb:
            o.add(ui.section(ui.kicker("Quand il marque") + f'<div style="margin-top: 10px">{ui.frise([(r.minute, f"{r.minute}’") for r in bj.itertuples()])}</div>'))
            og = bj.origine_but.value_counts()
            o.add(ui.section(ui.kicker("Comment il marque") + '<div style="margin-top: 12px">'
                             + ui.hbars([(ORIG.get(k, k), int(v), RED if n == 0 else INK) for n, (k, v) in enumerate(og.items())], int(og.max())) + "</div>"))
        if npas:
            c = pj.groupby("buteur").size().sort_values(ascending=False)
            o.add(ui.section(ui.kicker("Ses passes pour") + '<div style="margin-top: 12px">' + ui.hbars([(k, int(v), INK) for k, v in c.items()], int(c.max()), label_w=170) + "</div>"))
    else:
        d = bj if onglet == "buts" else pj
        lib = "buts" if onglet == "buts" else "passes décisives"
        o.add(ui.section(ui.kicker(f"{len(d)} {lib}"), pad="16px 16px 4px"))
        for r in d.itertuples():
            home = r.club_marque == r.club_dom
            opp = r.club_ext if home else r.club_dom
            detail = (f"passe {r.passeur}" if isinstance(r.passeur, str) else "sans passe") if onglet == "buts" else f"but de {r.buteur}"
            o.lien(f'<div style="display: grid; grid-template-columns: 30px 38px minmax(0,1fr) 44px; align-items: center; gap: 8px; padding: 10px 16px; border-bottom: 1px solid {LINE}">'
                   f'<span style="font-family: {COND}; font-weight: 700; color: {MUTED}">J{r.journee}</span><span style="font-family: {COND}; font-weight: 700; color: {RED}">{r.minute}\u2019</span>'
                   f'<span><span style="display: block; font-weight: 600">vs {e(NOMS[opp])}</span><span style="font-size: 12px; color: {MUTED}">{e(ORIG.get(r.origine_but, str(r.origine_but)))} · {e(detail)}</span></span>'
                   f'<span style="font-family: {SERIF}; font-size: 17px; text-align: right">{r.score_dom_apres}-{r.score_ext_apres}</span></div>', "match", j=r.journee, dom=r.club_dom)
        if d.empty:
            o.add(ui.section(ui.empty("Rien pour l\u2019instant.")))
    pieds(o)


# ================================================================== MÉTHODO & CONTRÔLE
def page_methodo():
    topnav("")
    o = Sortie()
    lig = base.stats_ligue()
    p = lambda t: f'<p style="font-size: 14px; line-height: 1.55">{t}</p>'
    entete(o, "Méthodologie", retour=("une", {}))
    o.add(ui.section(ui.kicker("Les données") + '<div style="margin-top: 10px">'
          + p("Toutes les données sont collectées à la main par Victor Geoffroy à partir des matchs de D1 Futsal. Elles ne sont pas officielles. "
              "Chaque but est saisi avec sa minute, son score, son buteur, son passeur et la phase de jeu qui l\u2019a amené.")
          + p("Avant chaque mise en ligne, des contrôles automatiques vérifient l\u2019enchaînement des scores, la cohérence buteur/passeur et le rattachement "
              "de chaque joueur à un seul club. Si un contrôle échoue, rien n\u2019est publié.")
          + p("Classement : 3 points la victoire, 1 le nul. Départage par différence de buts puis buts marqués.")
          + p("Crédits : clubs, joueurs, FFF. Photos et logos avec l\u2019accord de leurs auteurs.") + "</div>"
          + ui.tiles(ui.tile(lig["nb_buts"], "buts saisis", "red"), ui.tile(lig["nb_matchs"], "matchs"), ui.tile(f'{lig["part_avec_passe"]} %', "avec passeur")), pad="16px 16px 0"))
    o.fin()


def page_controle():
    """Page privée : /controle?cle=... (clé dans les Secrets Streamlit)."""
    o = Sortie()
    try:
        cle = st.secrets["CLE_ADMIN"]
    except Exception:
        cle = None
    if not cle or qp.get("cle") != cle:
        entete(o, "Accès refusé"); o.fin(); return
    rows = "".join(f'<div style="padding: 8px 0; border-bottom: 1px solid {LINE}; font-size: 13px"><b style="color: {RED if a.niveau == "BLOQUANT" else INK}">{a.niveau}</b> · {e(a.source)} · {e(a.message)}</div>'
                   for a in base.anomalies) or ui.empty("Aucune anomalie.")
    entete(o, "Contrôle des données")
    o.add(ui.section(ui.kicker(f"{len(base.anomalies)} anomalie(s)") + rows, pad="16px 16px 0"))
    o.add(ui.section(ui.kicker("Textes à valider") + f'<p style="font-size: 13px; color: {MUTED}">Télécharge le fichier, relis, corrige dans texte_valide si besoin, '
                     f'mets OK dans statut, puis dépose-le dans le dépôt avec tes données. Les textes déjà validés sont conservés.</p>'))
    o.flush()
    if not base.bloquant:
        import generer_textes
        jt = st.selectbox("Journée", base.journees[::-1], format_func=lambda x: f"J{x}")
        st.download_button("Télécharger textes_journee.xlsx", generer_textes.fichier_pour_telechargement(base, jt),
                           file_name="textes_journee.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    o.fin()


def page_maintenance():
    o = Sortie()
    entete(o, "D1 Futsal", "Mise à jour en cours")
    o.add(ui.section(ui.empty("Les données de la journée sont en cours de vérification. Revenez dans quelques minutes.")))
    o.fin()


# ================================================================== routage
DEFS = [("une", page_une, "La Une", ""), ("matchs", page_matchs, "Matchs", "matchs"), ("match", page_match, "Match", "match"),
        ("classements", page_classements, "Classements", "classements"), ("clubs", page_clubs, "Clubs", "clubs"),
        ("club", page_club, "Club", "club"), ("joueurs", page_joueurs, "Joueurs", "joueurs"), ("joueur", page_joueur, "Joueur", "joueur"),
        ("methodo", page_methodo, "Méthodologie", "methodo"), ("controle", page_controle, "Contrôle", "controle")]

if base.bloquant:
    # aucune donnée publiée tant qu'un contrôle bloquant n'est pas levé (sauf la page contrôle)
    DEFS = [(n, f if n == "controle" else page_maintenance, t, u) for n, f, t, u in DEFS]

for nom, fonction, titre, chemin in DEFS:
    kwargs = {"default": True} if nom == "une" else {"url_path": chemin}
    nav.PAGES[nom] = st.Page(fonction, title=f"{titre} · D1 Futsal", **kwargs)

st.navigation(list(nav.PAGES.values()), position="hidden").run()
