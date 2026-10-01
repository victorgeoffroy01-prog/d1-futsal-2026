"""
D1 Futsal · appli mobile.
Lancer en local : streamlit run app_mobile.py
Navigation par URL : ?page=matchs | match&j=3&dom=GARGES | classements | clubs | club&id=LAVAL
                     | joueurs | joueur&id=bilal-bakkali | methodo
"""
from __future__ import annotations
import os

import pandas as pd
import streamlit as st

import config as C
import data
from textes import charger_textes
from ui import components as ui
from ui.components import e, url, fr
from ui.theme import CSS, PAPER, INK, RED, MUTED, LINE, SOFT, SERIF, COND

st.set_page_config(page_title="D1 Futsal", page_icon="⚽", layout="centered", initial_sidebar_state="collapsed")
st.html(CSS)

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
page = qp.get("page", "une")

# Données bloquées : rien n'est publié tant qu'un contrôle bloquant n'est pas levé
if base.bloquant and page != "controle":
    ui.show(ui.appbar("D1 Futsal", "Mise à jour en cours") + ui.section(ui.empty(
        "Les données de la journée sont en cours de vérification. Revenez dans quelques minutes.")))
    st.stop()

NOMS = {r.club_court: (r.nom_affiche if isinstance(r.nom_affiche, str) and r.nom_affiche else C.NOMS_CLUBS.get(r.club_court, r.club_court))
        for r in base.clubs.assign(nom_affiche=base.clubs.get("nom_affiche")).itertuples()}
JREF = base.joueurs.drop_duplicates("id_joueur").set_index("id_joueur")
CLASSEMENT = base.classement()
STATS = base.stats_joueurs()
DERNIERE = max(base.journees) if base.journees else None


def club_de(i):
    return JREF.club_court.get(i, "")


def lien_match(j, dom):
    return url(page="match", j=j, dom=dom)


# ================================================================== LA UNE
def page_une():
    j = int(qp.get("j", DERNIERE))
    m = base.matchs[base.matchs.journee == j]
    b = base.buts[base.buts.journee == j]
    h = ui.appbar("D1 Futsal", f"Saison {C.SAISON}")
    h += ui.pills([(f"J{x}", url(j=x), x == j) for x in base.journees])
    if m.empty:
        ui.show(h + ui.section(ui.empty("Pas encore de match pour cette journée.")) + ui.botnav("une"))
        return
    # match à la une : texte validé s'il existe, sinon le match le plus riche en buts
    top = m.sort_values(["nb_buts", "dom"], ascending=[False, True]).iloc[0]
    titre = TEXTES.get(f"une:J{j}")
    chapo = TEXTES.get(f"match:J{j}:{top.dom}")
    card = (f'<a href="{lien_match(j, top.dom)}" target="_self" style="display: block; margin-top: 12px; background: {INK}; color: #fff; border-radius: 12px; padding: 18px 16px 16px">'
            f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #F2B8C0">Le match de la journée</div>'
            f'<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 12px">'
            f'<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; width: 96px">{ui.logo_or_badge(top.dom, 44, 12, False)}<span style="font-weight: 600; font-size: 13px; color: #fff">{e(NOMS[top.dom])}</span></div>'
            f'<div style="font-family: {SERIF}; font-size: 56px; line-height: 1">{top.bd}-{top.be}</div>'
            f'<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; width: 96px">{ui.logo_or_badge(top.ext, 44, 12, False)}<span style="font-weight: 600; font-size: 13px; color: #fff">{e(NOMS[top.ext])}</span></div></div>'
            + (f'<div style="font-family: {SERIF}; font-size: 22px; line-height: 1.15; margin-top: 14px">{e(titre)}</div>' if titre else "")
            + (f'<div style="font-size: 13px; color: #D9D2C6; margin-top: 6px">{e(chapo)}</div>' if chapo else "")
            + "</a>")
    ecart = m.assign(d=(m.bd - m.be).abs()).sort_values("d", ascending=False).iloc[0]
    h += ui.section(ui.kicker(f"La Une · Journée {j}") + card + ui.tiles(
        ui.tile(len(b), f"buts en J{j}", "red"), ui.tile(fr(len(b) / len(m)), "buts / match"),
        ui.tile(f"{max(ecart.bd, ecart.be)}-{min(ecart.bd, ecart.be)}", "plus large écart"), mt=10), pad="4px 16px 0")
    rows = "".join(ui.match_row(r, NOMS, lien_match(r.journee, r.dom)) for r in m.sort_values("nb_buts", ascending=False).itertuples())
    h += f'<div style="padding: 22px 16px 0">{ui.kicker(f"Résultats · J{j}")}</div><div style="margin-top: 8px; border-top: 1px solid {LINE}">{rows}</div>'
    # leaders
    def podium(df, col, titre, vue):
        cards = ""
        for i, r in enumerate(df.head(3).itertuples()):
            dark = i == 0
            nom = r.joueur.split()
            cards += (f'<a href="{url(page="joueur", id=r.id_joueur)}" target="_self" style="flex: 1; min-width: 0; background: {INK if dark else PAPER}; '
                      f'color: {"#fff" if dark else INK}; border: 1.5px solid {INK}; border-radius: 10px; padding: 12px 10px; display: flex; flex-direction: column; gap: 6px">'
                      f'<div style="font-family: {SERIF}; font-size: 36px; line-height: 1">{getattr(r, col)}</div>'
                      f'<div style="font-weight: 700; font-size: 13px; line-height: 1.15; color: {"#fff" if dark else INK}">{e(nom[0])}<br>{e(" ".join(nom[1:3]))}</div>'
                      f'<div style="font-family: {COND}; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: {"#E9E2D5" if dark else MUTED}">{e(NOMS.get(r.club, r.club))}</div></a>')
        return (ui.section(ui.kicker(titre) + f'<div style="display: flex; gap: 8px; margin-top: 12px">{cards}</div>'
                + f'<a href="{url(page="classements", vue=vue)}" target="_self" style="display: flex; justify-content: flex-end; padding-top: 8px; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em; color: {RED}">TOUT LE CLASSEMENT</a>'))
    h += podium(STATS[STATS.Buts > 0], "Buts", "Meilleurs buteurs", "buteurs")
    h += podium(STATS[STATS.Passes > 0].sort_values(["Passes", "Buts"], ascending=False), "Passes", "Meilleurs passeurs", "passeurs")
    mini = ""
    for r in CLASSEMENT.head(5).itertuples():
        mini += (f'<a href="{url(page="club", id=r.club)}" target="_self" style="display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-bottom: 1px solid {LINE}">'
                 f'<span style="width: 18px; font-family: {COND}; font-weight: 700">{r.Rg}</span>{ui.logo_or_badge(r.club, 24, 8)}'
                 f'<span style="flex: 1; font-weight: 600">{e(NOMS[r.club])}</span><span style="font-family: {COND}; color: {MUTED}; width: 34px; text-align: right">{r.Diff:+d}</span>'
                 f'<span style="font-family: {SERIF}; font-size: 18px; width: 28px; text-align: right">{r.Pts}</span></a>')
    h += f'<div style="padding: 22px 16px 0">{ui.kicker("Classement")}</div><div style="margin-top: 6px">{mini}</div>'
    h += f'<a href="{url(page="classements")}" target="_self" style="display: flex; align-items: center; justify-content: center; min-height: 48px; font-family: {COND}; font-weight: 700; font-size: 13px; letter-spacing: 0.08em; color: {RED}">CLASSEMENT COMPLET</a>'
    ui.show(h + ui.footer() + ui.botnav("une"))


# ================================================================== MATCHS
def page_matchs():
    j = int(qp.get("j", DERNIERE))
    m = base.matchs[base.matchs.journee == j]
    h = ui.appbar("Matchs", f"Journée {j}")
    h += ui.pills([(f"J{x}", url(page="matchs", j=x), x == j) for x in base.journees])
    h += f'<div style="border-top: 1px solid {LINE}">' + "".join(ui.match_row(r, NOMS, lien_match(r.journee, r.dom)) for r in m.itertuples()) + "</div>"
    ui.show(h + ui.footer() + ui.botnav("match"))


def page_match():
    j, dom = int(qp.get("j", DERNIERE)), qp.get("dom")
    mm = base.matchs[(base.matchs.journee == j) & (base.matchs.dom == dom)]
    if mm.empty:
        ui.show(ui.appbar("Match", back=url(page="matchs")) + ui.section(ui.empty("Match introuvable.")) + ui.botnav("match")); return
    m = mm.iloc[0]
    b = base.match(j, dom)
    onglet = qp.get("onglet", "resume")
    lien = lambda o: url(page="match", j=j, dom=dom, onglet=o)

    def buteurs(club, align):
        d = b[b.club_marque == club]
        court = lambda n: n if n == "CSC" or len(n.split()) == 1 else " ".join(n.split()[1:])   # sans le prénom
        parts = [f'{e(court(n))} ' + " ".join(f"{x}\u2019" for x in g.minute) for n, g in d.groupby("buteur", sort=False)]
        return f'<div style="text-align: {align}">{" · ".join(parts)}</div>'
    h = ui.appbar(f"{NOMS[m.dom]} - {NOMS[m.ext]}", f"Journée {j} · Terminé", back=url(page="matchs", j=j))
    h += (f'<section style="background: {PAPER}; border-bottom: 1px solid {LINE}; padding: 18px 16px 14px">'
          f'<div style="display: flex; align-items: center; justify-content: space-between">'
          f'<a href="{url(page="club", id=m.dom)}" target="_self" style="display: flex; flex-direction: column; align-items: center; gap: 6px; width: 96px">{ui.logo_or_badge(m.dom, 52, 13)}<span style="font-weight: 600; text-align: center">{e(NOMS[m.dom])}</span></a>'
          f'<div style="text-align: center"><div style="font-family: {SERIF}; font-size: 60px; line-height: 1">{m.bd}<span style="color: {MUTED}">-</span>{m.be}</div>'
          f'<div style="font-family: {COND}; font-weight: 600; font-size: 12px; color: {MUTED}; letter-spacing: 0.08em; margin-top: 4px">MI-TEMPS {m.mt_d}-{m.mt_e}</div></div>'
          f'<a href="{url(page="club", id=m.ext)}" target="_self" style="display: flex; flex-direction: column; align-items: center; gap: 6px; width: 96px">{ui.logo_or_badge(m.ext, 52, 13, False)}<span style="font-weight: 600; text-align: center">{e(NOMS[m.ext])}</span></a></div>'
          f'<div style="display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 12px; margin-top: 14px; font-size: 12px; color: {MUTED}">'
          f'{buteurs(m.dom, "right")}{buteurs(m.ext, "left")}</div></section>')
    h += ui.tabs([("Résumé", lien("resume"), onglet == "resume"), ("Timeline", lien("timeline"), onglet == "timeline"),
                  ("Stats", lien("stats"), onglet == "stats"), ("Compos", lien("compos"), onglet == "compos")])
    if onglet == "resume":
        txt = TEXTES.get(f"match:J{j}:{dom}")
        bdx = b[b.club_marque == m.ext]
        n_but_ext = bdx[bdx.id_buteur.notna()].id_buteur.nunique(); n_but_dom = b[(b.club_marque == m.dom) & b.id_buteur.notna()].id_buteur.nunique()
        ess = (f'<div style="font-family: {SERIF}; font-size: 21px; line-height: 1.2; margin-top: 10px">{e(txt)}</div>' if txt else "")
        h += ui.section(ui.kicker("L\u2019essentiel") + ess + ui.tiles(
            ui.tile(len(b), "buts", "dark"), ui.tile(f"{n_but_dom}-{n_but_ext}", "buteurs différents"),
            ui.tile(int(b.id_passeur.notna().sum()), "buts avec passe", "red")), pad="16px 16px 0")
        h += ui.section(ui.kicker("Score minute par minute") + f'<div style="margin-top: 10px">{ui.score_progressif(b, m.dom, m.ext, NOMS)}</div>')
        o_d = b[b.club_marque == m.dom].origine_but.value_counts(); o_e = b[b.club_marque == m.ext].origine_but.value_counts()
        keys = sorted(set(o_d.index) | set(o_e.index), key=lambda k: -(o_d.get(k, 0) + o_e.get(k, 0)))
        h += ui.section(ui.kicker("D\u2019où viennent les buts") + '<div style="margin-top: 10px">'
                        + ui.mirror([(ORIG.get(k, k), int(o_d.get(k, 0)), int(o_e.get(k, 0))) for k in keys], NOMS[m.dom], NOMS[m.ext]) + "</div>")
    elif onglet == "timeline":
        ev, mt = "", False
        for r in b.itertuples():
            if r.periode == 2 and not mt:
                ev += (f'<div style="display: flex; align-items: center; gap: 10px; margin: 6px 0"><div style="flex: 1; height: 1px; background: {INK}"></div>'
                       f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.12em">MI-TEMPS · {m.mt_d}-{m.mt_e}</div><div style="flex: 1; height: 1px; background: {INK}"></div></div>')
                mt = True
            home = r.club_marque == m.dom
            nom = e(r.buteur) if r.est_csc is False or not r.est_csc else "CSC"
            lien_j = url(page="joueur", id=r.id_buteur) if r.id_buteur else None
            nom_html = f'<a href="{lien_j}" target="_self" style="font-weight: 700; font-size: 14px">{nom}</a>' if lien_j else f'<span style="font-weight: 700; font-size: 14px">{nom}</span>'
            passe = f'<span style="font-size: 12px; color: {INK}">passe {e(r.passeur)}</span>' if isinstance(r.passeur, str) else ""
            card = (f'<div style="display: flex; flex-direction: column; gap: 2px; {"align-items: flex-end; text-align: right" if home else ""}">{nom_html}{passe}'
                    f'<span style="font-family: {COND}; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: {MUTED}">{e(ORIG.get(r.origine_but, str(r.origine_but)))}</span></div>')
            mid = (f'<div style="display: flex; flex-direction: column; align-items: center"><span style="font-family: {COND}; font-weight: 700; font-size: 12px; color: {RED}">{r.minute}\u2019</span>'
                   f'<span style="font-family: {SERIF}; font-size: 17px; line-height: 1.1">{r.score_dom_apres}-{r.score_ext_apres}</span></div>')
            ev += (f'<div style="display: grid; grid-template-columns: minmax(0,1fr) 58px minmax(0,1fr); align-items: center; gap: 6px; padding: 8px 0; border-bottom: 1px dashed {LINE}">'
                   f'{card if home else "<div></div>"}{mid}{"<div></div>" if home else card}</div>')
        h += ui.section(ui.kicker(f"Les {len(b)} buts") + f'<div style="margin-top: 8px">{ev}</div>', pad="16px 16px 0")
    elif onglet == "stats":
        rows = []
        for lab, f in [("Buts 1re mi-temps", lambda d: (d.periode == 1).sum()), ("Buts 2e mi-temps", lambda d: (d.periode == 2).sum()),
                       ("Buts avec passe", lambda d: d.id_passeur.notna().sum()), ("Buteurs différents", lambda d: d.id_buteur.nunique()),
                       ("Buts 5 dernières min.", lambda d: (d.minute > 35).sum())]:
            rows.append((lab, int(f(b[b.club_marque == m.dom])), int(f(b[b.club_marque == m.ext]))))
        h += ui.section(ui.kicker("Face-à-face") + '<div style="margin-top: 10px">' + ui.mirror(rows, NOMS[m.dom], NOMS[m.ext], mid_w=130) + "</div>", pad="16px 16px 0")
        h += ui.section(ui.empty("Stats détaillées (tirs, duels, pertes, gardiens) disponibles quand le match est analysé."))
    else:
        h += ui.section(ui.empty("Compositions à venir."), pad="16px 16px 0")
    ui.show(h + ui.footer() + ui.botnav("match"))


# ================================================================== CLASSEMENTS
def page_classements():
    vue, lieu = qp.get("vue", "equipes"), qp.get("lieu", "tous")
    h = ui.appbar("Classements", f"D1 · Après J{DERNIERE}")
    h += ui.segmented([("Équipes", url(page="classements"), vue == "equipes"), ("Buteurs", url(page="classements", vue="buteurs"), vue == "buteurs"),
                       ("Passeurs", url(page="classements", vue="passeurs"), vue == "passeurs"), ("B+P", url(page="classements", vue="bp"), vue == "bp")])
    if vue == "equipes":
        h += ui.pills([("Général", url(page="classements"), lieu == "tous"), ("Domicile", url(page="classements", lieu="dom"), lieu == "dom"),
                       ("Extérieur", url(page="classements", lieu="ext"), lieu == "ext")])
        t = base.classement(lieu)
        grid = "grid-template-columns: 20px 26px minmax(0,1fr) 20px 20px 20px 20px 34px 30px"
        h += (f'<div style="display: grid; {grid}; gap: 6px; padding: 6px 12px; font-family: {COND}; font-weight: 700; font-size: 11px; color: {MUTED}; border-bottom: 2px solid {INK}">'
              f'<span>#</span><span></span><span>ÉQUIPE</span><span style="text-align:center">J</span><span style="text-align:center">G</span><span style="text-align:center">N</span>'
              f'<span style="text-align:center">P</span><span style="text-align:right">DIFF</span><span style="text-align:right">PTS</span></div>')
        for r in t.itertuples():
            zone = C.NB_PLAYOFFS and r.Rg <= C.NB_PLAYOFFS
            h += (f'<a href="{url(page="club", id=r.club)}" target="_self" style="display: grid; {grid}; gap: 6px; align-items: center; padding: 10px 12px; '
                  f'border-bottom: 1px solid {LINE}; background: {PAPER}; {"box-shadow: inset 4px 0 0 " + RED if zone else ""}">'
                  f'<span style="font-family: {COND}; font-weight: 700">{r.Rg}</span>{ui.logo_or_badge(r.club, 24, 8)}'
                  f'<span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(NOMS[r.club])}</span>'
                  + "".join(f'<span style="font-family: {COND}; color: {MUTED}; text-align: center">{v}</span>' for v in (r.J, r.G, r.N, r.P))
                  + f'<span style="font-family: {COND}; text-align: right">{r.Diff:+d}</span><span style="font-family: {SERIF}; font-size: 19px; text-align: right">{r.Pts}</span></a>')
        h += f'<div style="padding: 10px 16px; font-size: 12px; color: {MUTED}">Départage : points, différence de buts, buts marqués.</div>'
    else:
        col, tri = {"buteurs": ("Buts", ["Buts", "Passes"]), "passeurs": ("Passes", ["Passes", "Buts"]), "bp": ("B+P", ["B+P", "Buts"])}[vue]
        d = STATS[STATS[col] > 0].sort_values(tri + ["joueur"], ascending=[False, False, True])
        h += '<div style="margin-top: 12px; border-top: 1px solid ' + LINE + '">'
        rang, prev = 0, None
        for i, (_, r) in enumerate(d.iterrows(), 1):
            v = int(r[col])
            rang = i if v != prev else rang
            prev = v
            sous = f"{NOMS.get(r.club, r.club)} · {r.Buts} b · {r.Passes} p"
            h += ui.rank_row(rang, r.joueur, sous, v, url(page="joueur", id=r.id_joueur), rang == 1)
        h += "</div>"
    ui.show(h + ui.footer() + ui.botnav("class"))


# ================================================================== CLUBS
def page_clubs():
    h = ui.appbar("Clubs", "D1 Futsal")
    cards = ""
    for r in CLASSEMENT.sort_values("club").itertuples():
        cards += (f'<a href="{url(page="club", id=r.club)}" target="_self" style="display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px 8px; '
                  f'background: {PAPER}; border: 1.5px solid {INK}; border-radius: 12px">{ui.logo_or_badge(r.club, 48, 12)}'
                  f'<span style="font-weight: 700; text-align: center">{e(NOMS[r.club])}</span><span style="font-family: {COND}; font-size: 12px; color: {MUTED}">{r.Rg}e · {r.Pts} pts</span></a>')
    h += f'<div style="display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; padding: 16px">{cards}</div>'
    ui.show(h + ui.footer() + ui.botnav("club"))


def page_club():
    club = qp.get("id")
    if club not in NOMS:
        ui.show(ui.appbar("Club", back=url(page="clubs")) + ui.section(ui.empty("Club introuvable.")) + ui.botnav("club")); return
    onglet = qp.get("onglet", "resume")
    lien = lambda o: url(page="club", id=club, onglet=o)
    s = base.stats_club(club)
    cl = s["classement"]
    info = base.clubs.set_index("club_court").loc[club]
    meta = " · ".join(x for x in [info.get("salle"), f"Coach {info.get('coach')}" if info.get("coach") else None] if isinstance(x, str) and x)
    best_def = CLASSEMENT.BC.min() == cl["BC"]
    h = ui.appbar("Club", back=url(page="clubs"))
    h += (f'<section style="background: {INK}; color: #fff; padding: 18px 16px 16px"><div style="display: flex; align-items: center; gap: 14px">'
          f'{ui.logo_or_badge(club, 64, 14, False)}<div><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{e(NOMS[club])}</div>'
          + (f'<div style="font-size: 13px; color: #D9D2C6; margin-top: 6px">{e(meta)}</div>' if meta else "") + "</div></div>"
          f'<div style="display: flex; gap: 8px; margin-top: 16px">'
          f'<div style="flex: 1; border: 1.5px solid #fff; border-radius: 10px; padding: 10px"><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{cl["Rg"]}<sup style="font-size: 14px">e</sup></div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em; color: #D9D2C6">CLASSEMENT</div></div>'
          f'<div style="flex: 1; border: 1.5px solid #fff; border-radius: 10px; padding: 10px"><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{cl["Pts"]}</div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em; color: #D9D2C6">POINTS</div></div>'
          f'<div style="flex: 1; background: {RED}; border-radius: 10px; padding: 10px"><div style="font-family: {SERIF}; font-size: 30px; line-height: 1">{cl["BP"]}-{cl["BC"]}</div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.08em">BUTS POUR-CONTRE</div></div></div>'
          + (f'<div style="font-size: 12px; color: #D9D2C6; margin-top: 8px">Meilleure défense de D1</div>' if best_def else "") + "</section>")
    h += ui.tabs([("Résumé", lien("resume"), onglet == "resume"), ("Effectif", lien("effectif"), onglet == "effectif"),
                  ("Buts", lien("buts"), onglet == "buts"), ("Matchs", lien("matchs"), onglet == "matchs")])
    if onglet == "resume":
        h += ui.section(ui.kicker("Forme") + '<div style="display: flex; gap: 6px; margin-top: 10px">' + "".join(ui.form_chip(x, 30) for x in cl["forme"]) + "</div>", pad="16px 16px 0")
        h += ui.section(ui.kicker("Buts par tranche de 5 min") + '<div style="margin-top: 10px">' + ui.tranches_miroir(s["tranches_marques"], s["tranches_encaisses"]) + "</div>")
        top = STATS[STATS.club == club].sort_values(["B+P", "Buts"], ascending=False).head(5)
        h += ui.section(ui.kicker("Joueurs clés") + "".join(
            ui.rank_row(i, r.joueur, f"{r.Buts} buts · {r.Passes} passes", r["B+P"], url(page="joueur", id=r.id_joueur), i == 1)
            for i, (_, r) in enumerate(top.iterrows(), 1)).replace("padding: 10px 16px", "padding: 10px 0"))
    elif onglet == "effectif":
        eff = base.joueurs[base.joueurs.club_court == club]
        st_ = STATS.set_index("id_joueur")
        rows = ""
        for r in eff.itertuples():
            bts = int(st_.Buts.get(r.id_joueur, 0)); pas = int(st_.Passes.get(r.id_joueur, 0))
            poste = r.poste if isinstance(getattr(r, "poste", None), str) else ""
            num = r.numero if pd.notna(getattr(r, "numero", None)) else ""
            rows += (f'<a href="{url(page="joueur", id=r.id_joueur)}" target="_self" style="display: grid; grid-template-columns: 30px minmax(0,1fr) 34px 34px; gap: 8px; align-items: center; padding: 10px 0; border-bottom: 1px solid {LINE}">'
                     f'<span style="font-family: {COND}; color: {MUTED}">{e(str(num).replace(".0", ""))}</span><span><span style="display: block; font-weight: 600">{e(r.nom_affiche)}</span>'
                     f'<span style="font-size: 12px; color: {MUTED}">{e(poste)}</span></span><span style="font-family: {SERIF}; font-size: 17px; text-align: center">{bts}</span>'
                     f'<span style="font-family: {SERIF}; font-size: 17px; text-align: center; color: {MUTED}">{pas}</span></a>')
        head = (f'<div style="display: grid; grid-template-columns: 30px minmax(0,1fr) 34px 34px; gap: 8px; padding: 10px 0 6px; border-bottom: 2px solid {INK}; '
                f'font-family: {COND}; font-weight: 700; font-size: 11px; color: {MUTED}"><span>N°</span><span>JOUEUR</span><span style="text-align:center">B</span><span style="text-align:center">P</span></div>')
        h += ui.section(ui.kicker("Effectif") + head + rows, pad="16px 16px 0")
    elif onglet == "buts":
        orig = s["origines"]
        h += ui.section(ui.kicker("Comment le club marque") + '<div style="margin-top: 12px">'
                        + ui.hbars([(ORIG.get(k, k), v, RED if i == 0 else INK) for i, (k, v) in enumerate(orig.items())], max(orig.values()) if orig else 1) + "</div>", pad="16px 16px 0")
        oe = s["origines_encaisses"]
        h += ui.section(ui.kicker("Comment le club encaisse") + '<div style="margin-top: 12px">'
                        + ui.hbars([(ORIG.get(k, k), v, RED if i == 0 else INK) for i, (k, v) in enumerate(oe.items())], max(oe.values()) if oe else 1) + "</div>")
    else:
        rows = ""
        for r in s["matchs"].itertuples():
            home = r.dom == club
            f_, a_ = (r.bd, r.be) if home else (r.be, r.bd)
            opp = r.ext if home else r.dom
            res = "V" if f_ > a_ else ("N" if f_ == a_ else "D")
            rows += (f'<a href="{lien_match(r.journee, r.dom)}" target="_self" style="display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid {LINE}">'
                     f'<span style="font-family: {COND}; font-weight: 700; color: {MUTED}; width: 26px">J{r.journee}</span><span style="font-family: {COND}; font-size: 12px; color: {MUTED}; width: 28px">{"DOM" if home else "EXT"}</span>'
                     f'{ui.logo_or_badge(opp, 24, 8)}<span style="flex: 1; font-weight: 600">{e(NOMS[opp])}</span><span style="font-family: {SERIF}; font-size: 18px">{f_}-{a_}</span>{ui.form_chip(res, 22)}</a>')
        h += ui.section(ui.kicker("Matchs") + rows, pad="16px 16px 0")
    ui.show(h + ui.footer() + ui.botnav("club"))


# ================================================================== JOUEURS
def page_joueurs():
    ui.show(ui.appbar("Joueurs", "Recherche"))
    q = st.text_input("Rechercher un joueur", placeholder="Nom, prénom ou surnom…")
    d = STATS.copy()
    if q:
        d = d[d.joueur.str.contains(q.strip(), case=False, regex=False)]
    else:
        d = d.sort_values(["B+P", "Buts"], ascending=False).head(30)
    h = ui.section(ui.kicker("Résultats" if q else "Les plus décisifs"), pad="10px 16px 0")
    h += '<div style="margin-top: 6px">' + "".join(
        ui.rank_row(i, r.joueur, f"{NOMS.get(r.club, r.club)} · {r.Buts} b · {r.Passes} p", r["B+P"], url(page="joueur", id=r.id_joueur))
        for i, (_, r) in enumerate(d.iterrows(), 1)) + "</div>"
    if q and d.empty:
        h += ui.section(ui.empty("Aucun joueur trouvé."))
    ui.show(h + ui.footer() + ui.botnav("joueur"))


def page_joueur():
    i = qp.get("id")
    if i not in JREF.index:
        ui.show(ui.appbar("Joueur", back=url(page="joueurs")) + ui.section(ui.empty("Joueur introuvable.")) + ui.botnav("joueur")); return
    j = JREF.loc[i]
    club = j.club_court
    onglet = qp.get("onglet", "resume")
    lien = lambda o: url(page="joueur", id=i, onglet=o)
    s = STATS.set_index("id_joueur").loc[i] if i in set(STATS.id_joueur) else None
    bj = base.buts[base.buts.id_buteur == i].sort_values(["journee", "minute"])
    pj = base.buts[base.buts.id_passeur == i].sort_values(["journee", "minute"])
    num = f"N° {int(j.numero)}" if pd.notna(j.get("numero")) else None
    poste = j.get("poste") if isinstance(j.get("poste"), str) else None
    sur = " · ".join(x for x in [num, poste] if x)
    h = ui.appbar("Joueur", back=url(page="joueurs"))
    h += (f'<section style="padding: 16px; display: flex; gap: 14px; align-items: center; background: {PAPER}; border-bottom: 1px solid {LINE}">{ui.photo(i)}'
          f'<div style="flex: 1; min-width: 0">' + (f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.12em; color: {RED}">{e(sur)}</div>' if sur else "")
          + f'<div style="font-family: {SERIF}; font-size: 28px; line-height: 1.02; margin-top: 4px">{e(j.nom_affiche)}</div>'
          f'<a href="{url(page="club", id=club)}" target="_self" style="display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; font-weight: 600">{ui.logo_or_badge(club, 24, 8)}{e(NOMS.get(club, club))}</a></div></section>')
    h += ui.tabs([("Résumé", lien("resume"), onglet == "resume"), ("Buts", lien("buts"), onglet == "buts"),
                  ("Passes", lien("passes"), onglet == "passes")])
    if onglet == "resume":
        nb, npas = len(bj), len(pj)
        rang = int((STATS.Buts > nb).sum()) + 1
        mj = int(CLASSEMENT.set_index("club").J.get(club, 0))
        h += ui.section(f'<div style="display: flex; align-items: flex-end; gap: 14px"><div style="font-family: {SERIF}; font-size: 96px; line-height: 0.85; color: {RED}">{nb}</div>'
                        f'<div style="padding-bottom: 6px"><div style="font-family: {COND}; font-weight: 700; font-size: 16px; letter-spacing: 0.1em">BUT{"S" if nb > 1 else ""}</div>'
                        f'<div style="font-size: 13px; color: {MUTED}">{"Meilleur buteur de D1" if rang == 1 and nb else (f"{rang}e buteur de D1" if nb else "Pas encore buteur")}</div></div></div>'
                        + ui.tiles(ui.tile(npas, "passes déc.", "dark"), ui.tile(nb + npas, "buts + passes"), ui.tile(fr(nb / mj, 2) if mj else "-", "buts / match"))
                        + ui.tiles(ui.tile(int(s.Pct_buts_club) if s is not None else 0, "% buts du club"), ui.tile(int(bj.ouverture.sum()), "buts d\u2019ouverture"),
                                   ui.tile(f"{int((bj.periode == 1).sum())}/{int((bj.periode == 2).sum())}", "1re / 2e MT"), mt=8), pad="16px 16px 0")
        if nb:
            h += ui.section(ui.kicker("Quand il marque") + f'<div style="margin-top: 10px">{ui.frise([(r.minute, f"{r.minute}’") for r in bj.itertuples()])}</div>')
            o = bj.origine_but.value_counts()
            h += ui.section(ui.kicker("Comment il marque") + '<div style="margin-top: 12px">'
                            + ui.hbars([(ORIG.get(k, k), int(v), RED if n == 0 else INK) for n, (k, v) in enumerate(o.items())], int(o.max())) + "</div>")
        if npas:
            c = pj.groupby("buteur").size().sort_values(ascending=False)
            h += ui.section(ui.kicker("Ses passes pour") + '<div style="margin-top: 12px">'
                            + ui.hbars([(k, int(v), INK) for k, v in c.items()], int(c.max()), label_w=170) + "</div>")
    else:
        d = bj if onglet == "buts" else pj
        rows = ""
        for r in d.itertuples():
            home = r.club_marque == r.club_dom
            opp = r.club_ext if home else r.club_dom
            detail = (f"passe {r.passeur}" if isinstance(r.passeur, str) else "sans passe") if onglet == "buts" else f"but de {r.buteur}"
            rows += (f'<a href="{lien_match(r.journee, r.club_dom)}" target="_self" style="display: grid; grid-template-columns: 30px 38px minmax(0,1fr) 44px; align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid {LINE}">'
                     f'<span style="font-family: {COND}; font-weight: 700; color: {MUTED}">J{r.journee}</span><span style="font-family: {COND}; font-weight: 700; color: {RED}">{r.minute}\u2019</span>'
                     f'<span><span style="display: block; font-weight: 600">vs {e(NOMS[opp])}</span><span style="font-size: 12px; color: {MUTED}">{e(ORIG.get(r.origine_but, str(r.origine_but)))} · {e(detail)}</span></span>'
                     f'<span style="font-family: {SERIF}; font-size: 17px; text-align: right">{r.score_dom_apres}-{r.score_ext_apres}</span></a>')
        lib = "buts" if onglet == "buts" else "passes décisives"
        h += ui.section(ui.kicker(f"{len(d)} {lib}") + (rows or ui.empty(f"Aucun{'' if onglet == 'buts' else 'e'} {lib[:-1] if len(d) != 1 else lib} pour l'instant.")), pad="16px 16px 0")
    ui.show(h + ui.footer() + ui.botnav("joueur"))


# ================================================================== MÉTHODO & CONTRÔLE
def page_methodo():
    lig = base.stats_ligue()
    txt = (f'<p style="font-size: 14px; line-height: 1.55">Toutes les données sont collectées à la main par Victor Geoffroy à partir des matchs de D1 Futsal. '
           f'Elles ne sont pas officielles. Chaque but est saisi avec sa minute, son score, son buteur, son passeur et la phase de jeu qui l\u2019a amené.</p>'
           f'<p style="font-size: 14px; line-height: 1.55">Avant chaque mise en ligne, des contrôles automatiques vérifient l\u2019enchaînement des scores, la cohérence buteur/passeur '
           f'et le rattachement de chaque joueur à un seul club. Si un contrôle échoue, rien n\u2019est publié.</p>'
           f'<p style="font-size: 14px; line-height: 1.55">Classement : 3 points la victoire, 1 le nul. Départage par différence de buts puis buts marqués.</p>'
           f'<p style="font-size: 14px; line-height: 1.55">Crédits : clubs, joueurs, FFF. Photos et logos avec l\u2019accord de leurs auteurs.</p>')
    ui.show(ui.appbar("Méthodologie", back=url()) + ui.section(ui.kicker("Les données") + f'<div style="margin-top: 10px">{txt}</div>'
            + ui.tiles(ui.tile(lig["nb_buts"], "buts saisis", "red"), ui.tile(lig["nb_matchs"], "matchs"), ui.tile(f'{lig["part_avec_passe"]} %', "avec passeur")), pad="16px 16px 0")
            + ui.footer() + ui.botnav(""))


def page_controle():
    """Page privée : ?page=controle&cle=... (clé définie dans .streamlit/secrets.toml)."""
    try:
        cle = st.secrets["CLE_ADMIN"]
    except Exception:
        cle = None
    if not cle or qp.get("cle") != cle:
        ui.show(ui.appbar("Accès refusé") + ui.botnav("")); return
    rows = "".join(f'<div style="padding: 8px 0; border-bottom: 1px solid {LINE}; font-size: 13px"><b style="color: {RED if a.niveau == "BLOQUANT" else INK}">{a.niveau}</b> · {e(a.source)} · {e(a.message)}</div>'
                   for a in base.anomalies) or ui.empty("Aucune anomalie.")
    ui.show(ui.appbar("Contrôle des données") + ui.section(ui.kicker(f"{len(base.anomalies)} anomalie(s)") + rows, pad="16px 16px 0") + ui.botnav(""))


PAGES = {"une": page_une, "matchs": page_matchs, "match": page_match, "classements": page_classements,
         "clubs": page_clubs, "club": page_club, "joueurs": page_joueurs, "joueur": page_joueur,
         "methodo": page_methodo, "controle": page_controle}
PAGES.get(page, page_une)()
