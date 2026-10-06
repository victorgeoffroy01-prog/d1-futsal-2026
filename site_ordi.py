"""
D1 Futsal · version ordinateur (même lien, mêmes adresses que l'appli mobile).
Tout le contenu à plat et comparable, façon FBref. Les données et les contrôles sont
communs avec la version mobile ; seul l'affichage change.
app_mobile.py appelle init(...) puis la page demandée.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config as C
import data
import analyse
import nav
import rapports
from nav import Sortie
import components as ui
from components import e, fr, svg_img
from theme import CR, PAPER, INK, RED, MUTED, LINE, SOFT, SERIF, SANS, COND

CSS_ORDI = f"""
<style>
.block-container, [data-testid="stMainBlockContainer"] {{ max-width: 100% !important; width: 100% !important; padding: 0 40px 110px !important; }}
[class*="st-key-rw-dnav"] {{ gap: 26px !important; border-top: 2px solid {INK}; border-bottom: 1px solid {INK}; margin-top: 18px; }}
[class*="st-key-rw-dgrid"] {{ gap: 14px !important; margin-top: 12px; }}
[class*="st-key-rw-dtabs"] {{ gap: 28px !important; border-bottom: 1px solid {INK}; margin-bottom: 24px; }}
[class*="st-key-rw-pills"] {{ padding: 12px 0 !important; }}
[class*="st-key-rw-seg"] {{ margin: 12px 0 0 !important; width: 100% !important; }}
[data-testid="stSelectbox"], [data-testid="stMultiSelect"], [data-testid="stSlider"], [data-testid="stRadio"] {{ padding: 0 !important; }}
[data-testid="stDataFrame"] {{ border: 1.5px solid {INK}; border-radius: 10px; overflow: hidden; }}
[data-testid="stTextInput"] {{ padding: 0 !important; }}
.st-key-filtres {{ background: {SOFT}; border-radius: 10px; padding: 14px 16px; gap: 14px !important; margin: 10px 0 14px; }}
.st-key-filtres label p {{ font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: {MUTED}; }}
</style>
"""

X: dict = {}       # contexte fourni par app_mobile.py (base, textes, noms...)


def init(**ctx):
    X.update(ctx)


def P(nom, defaut):
    return X["param"](nom, defaut)


# ------------------------------------------------------------------ briques
def card(inner, pad=18):
    return f'<div style="background: {PAPER}; border: 1.5px solid {INK}; border-radius: 12px; padding: {pad}px">{inner}</div>'


def sous_titre(t):
    return f'<div style="font-size: 13px; color: {MUTED}; margin: 10px 0 8px">{t}</div>'


def kick(t, mt=0):
    return ui.kicker(t, mt=mt)


def entete_site(active):
    """Bandeau + titre + navigation horizontale (zones cliquables sans rechargement)."""
    o = Sortie()
    lig = X["base"].stats_ligue()
    o.add(f'<div style="background: {INK}; color: #E9E2D5; font-family: {COND}; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; '
          f'margin: 0 -40px; padding: 8px 40px; display: flex; justify-content: space-between">'
          f'<span>Saison {C.SAISON} · Après la journée {X["derniere"]} · {lig["nb_buts"]} buts</span>'
          f'<span>Données collectées par V. Geoffroy · non officielles · crédits clubs, joueurs, FFF</span></div>')
    o.add(f'<div style="padding-top: 22px"><div style="font-family: {SERIF}; font-size: 60px; line-height: 0.95">D1 Futsal</div>'
          f'<div style="font-family: {COND}; font-weight: 700; font-size: 13px; letter-spacing: 0.16em; text-transform: uppercase; color: {RED}; margin-top: 8px">'
          f'Le championnat en données</div></div>')
    items = [("une", "La Une", "une"), ("matchs", "Résultats", "matchs"), ("classements", "Classements", "classements"),
             ("stats", "Statistiques", "joueurs"), ("clubs", "Clubs", "clubs"), ("methodo", "Méthodologie", "methodo")]
    nav_items = []
    for k, lab, cible in items:
        on = k == active
        nav_items.append((f'<div style="padding: 12px 0 10px; border-bottom: 3px solid {RED if on else "transparent"}; font-family: {COND}; '
                          f'font-weight: 700; font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; white-space: nowrap">{lab}</div>',
                          cible, {}, "content"))
    o.rangee(nav_items, style="dnav")
    o.fin()


def onglets_d(page, params, liste, actif):
    o = Sortie()
    o.rangee([(f'<div style="padding: 12px 0 10px; border-bottom: 3px solid {RED if k == actif else "transparent"}; font-family: {COND}; font-weight: 700; '
               f'font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; color: {INK if k == actif else MUTED}; white-space: nowrap">{lab}</div>',
               page, {**params, "onglet": k}, "content") for k, lab in liste], style="dtabs")
    o.fin()


def pied():
    o = Sortie()
    o.add(f'<div style="margin-top: 48px; padding: 18px 0; border-top: 2px solid {INK}; display: flex; justify-content: space-between; '
          f'font-size: 12px; color: {MUTED}"><span>Données collectées à la main par Victor Geoffroy à partir des matchs de D1 Futsal. Non officielles.</span>'
          f'<span>Crédits : clubs, joueurs, FFF.</span></div>')
    o.fin()
    X["bascule"]()


def vbars(dic, w=420, h=210, hi=(), color=INK, aria="Graphique"):
    ks = list(dic); mx = max(list(dic.values()) + [1]); n = len(ks); bw = (w - 40) / max(n, 1)
    s = ""
    for i, k in enumerate(ks):
        v = dic[k]; bh = (h - 46) * v / mx; x = 30 + i * bw + bw * 0.18; y = h - 24 - bh
        s += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*0.64:.1f}" height="{bh:.1f}" fill="{RED if k in hi else color}" rx="2"/>'
              f'<text x="{x+bw*0.32:.1f}" y="{y-6:.1f}" text-anchor="middle" font-size="12" font-weight="700" font-family="Archivo Narrow" fill="{INK}">{v}</text>'
              f'<text x="{x+bw*0.32:.1f}" y="{h-6}" text-anchor="middle" font-size="11" font-family="Archivo" fill="{MUTED}">{k}’</text>')
    s += (f'<line x1="26" x2="{w-6}" y1="{h-24}" y2="{h-24}" stroke="{INK}" stroke-width="1.5"/>'
          f'<line x1="{30+4*bw-2:.1f}" x2="{30+4*bw-2:.1f}" y1="12" y2="{h-24}" stroke="{INK}" stroke-dasharray="3 3"/>'
          f'<text x="{30+4*bw+4:.1f}" y="22" font-size="10" font-family="Archivo Narrow" fill="{MUTED}" letter-spacing="1">2E MI-TEMPS</text>')
    return svg_img(f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{s}</svg>', alt=aria)


def bars_groupees(a: dict, b: dict, w=620, h=230):
    ks = list(a); mx = max(list(a.values()) + list(b.values()) + [1]); bw = (w - 50) / len(ks)
    s = ""
    for i, k in enumerate(ks):
        x = 40 + i * bw
        for j, (v, c) in enumerate([(a[k], INK), (b.get(k, 0), RED)]):
            bh = (h - 50) * v / mx; xx = x + bw * 0.15 + j * bw * 0.34
            s += f'<rect x="{xx:.1f}" y="{h-26-bh:.1f}" width="{bw*0.3:.1f}" height="{bh:.1f}" fill="{c}" rx="2"/>'
            if v:
                s += f'<text x="{xx+bw*0.15:.1f}" y="{h-32-bh:.1f}" font-size="11" text-anchor="middle" font-family="Archivo Narrow" font-weight="700" fill="{INK}">{v}</text>'
        s += f'<text x="{x+bw/2:.1f}" y="{h-8}" font-size="11" text-anchor="middle" font-family="Archivo" fill="{MUTED}">{k}’</text>'
    s += (f'<line x1="36" x2="{w-6}" y1="{h-26}" y2="{h-26}" stroke="{INK}" stroke-width="1.5"/>'
          f'<line x1="{40+4*bw:.1f}" x2="{40+4*bw:.1f}" y1="10" y2="{h-26}" stroke="{INK}" stroke-dasharray="3 3"/>')
    leg = (f'<div style="display: flex; gap: 16px; margin-bottom: 8px; font-size: 12px"><span style="display: inline-flex; align-items: center; gap: 6px">'
           f'<span style="width: 12px; height: 12px; background: {INK}"></span>Marqués</span><span style="display: inline-flex; align-items: center; gap: 6px">'
           f'<span style="width: 12px; height: 12px; background: {RED}"></span>Encaissés</span></div>')
    return leg + svg_img(f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{s}</svg>', alt="Buts marqués et encaissés par tranche")


def tableau_html(cols, rows, tpl, link=None):
    """cols = [(libellé, align)], rows = liste de listes de cellules HTML. Renvoie le HTML d'en-tête et la liste des lignes."""
    head = (f'<div style="display: grid; {tpl}; gap: 6px; padding: 8px 10px; border-bottom: 2px solid {INK}; font-family: {COND}; font-weight: 700; '
            f'font-size: 11px; letter-spacing: 0.08em; color: {MUTED}; text-transform: uppercase">'
            + "".join(f'<span style="text-align: {a}">{l}</span>' for l, a in cols) + "</div>")
    lignes = [f'<div style="display: grid; {tpl}; gap: 6px; align-items: center; padding: 8px 10px; border-bottom: 1px solid {LINE}; background: {PAPER if i % 2 == 0 else CR}">'
              + "".join(f'<span style="text-align: {a}">{c}</span>' for (l, a), c in zip(cols, r)) + "</div>" for i, r in enumerate(rows)]
    return head, lignes


def chiffre(v, size=17, color=INK):
    return f'<span style="font-family: {SERIF}; font-size: {size}px; color: {color}">{v}</span>'


def cond(v, color=INK):
    return f'<span style="font-family: {COND}; color: {color}">{v}</span>'


def carte_match(m, analyse):
    N = X["noms"]
    wd, we = m.bd > m.be, m.be > m.bd

    def ligne(t, s, w):
        return (f'<div style="display: flex; align-items: center; gap: 10px">{ui.logo_or_badge(t, 28, 9)}<span style="flex: 1; font-weight: {700 if w else 500}; '
                f'font-size: 15px">{e(N[t])}</span><span style="font-family: {SERIF}; font-size: 24px; color: {INK if w or not (wd or we) else MUTED}">{s}</span></div>')
    return (f'<div style="height: 100%; box-sizing: border-box; display: flex; flex-direction: column; gap: 8px; background: {PAPER}; border: 1.5px solid {INK}; '
            f'border-radius: 10px; padding: 14px 16px"><div style="display: flex; justify-content: space-between; align-items: center; font-family: {COND}; font-weight: 700; '
            f'font-size: 11px; letter-spacing: 0.1em; color: {MUTED}"><span>J{m.journee} · TERMINÉ · MT {m.mt_d}-{m.mt_e}</span>{ui.BADGE_ANALYSE if analyse else ""}</div>'
            f'{ligne(m.dom, m.bd, wd)}{ligne(m.ext, m.be, we)}</div>')


def grille_matchs(matchs, par_ligne=3):
    o = Sortie()
    lst = list(matchs.itertuples())
    for k in range(0, len(lst), par_ligne):
        rang = [(carte_match(m, (m.journee, m.dom) in X["rapports"]), "match", {"j": m.journee, "dom": m.dom}) for m in lst[k:k + par_ligne]]
        rang += [("<div></div>", None, None)] * (par_ligne - len(rang))
        o.rangee(rang, style="dgrid")
    o.fin()


def classement_table(t, lieu="tous", compact=False):
    N = X["noms"]; nb = len(X["base"].clubs)
    if compact:
        tpl = "grid-template-columns: 20px 26px minmax(0,1fr) repeat(4, 20px) 32px 28px 84px"
        cols = [("#", "left"), ("", "left"), ("Équipe", "left"), ("J", "center"), ("G", "center"), ("N", "center"), ("P", "center"),
                ("Diff", "center"), ("Pts", "right"), ("Forme", "right")]
    else:
        tpl = "grid-template-columns: 28px 34px minmax(0,1fr) repeat(8, 46px) 130px"
        cols = [("#", "left"), ("", "left"), ("Équipe", "left"), ("J", "center"), ("G", "center"), ("N", "center"), ("P", "center"),
                ("BP", "center"), ("BC", "center"), ("Diff", "center"), ("Pts", "right"), ("Forme", "right")]
    rows = []
    for r in t.itertuples():
        forme = f'<span style="display: inline-flex; gap: 2px">{"".join(ui.form_chip(x, 18 if compact else 20) for x in r.forme)}</span>'
        base = [f'<span style="font-family: {COND}; font-weight: 700; color: {RED if lieu == "tous" and r.Rg <= C.NB_PLAYOFFS else INK}">{r.Rg}</span>',
                ui.logo_or_badge(r.club, 24 if compact else 26, 8),
                f'<span style="display: block; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(N[r.club])}</span>',
                cond(r.J), cond(r.G), cond(r.N), cond(r.P)]
        base += [cond(f"{r.Diff:+d}")] if compact else [cond(r.BP), cond(r.BC), cond(f"{r.Diff:+d}")]
        rows.append(base + [chiffre(r.Pts, 19), forme])
    head, lignes = tableau_html(cols, rows, tpl)
    o = Sortie()
    o.add(head)
    for r, l in zip(t.itertuples(), lignes):
        zone = RED if (lieu == "tous" and r.Rg <= C.NB_PLAYOFFS) else (INK if (lieu == "tous" and r.Rg > nb - C.NB_DESCENTE) else None)
        if zone:
            l = l.replace('<div style="display: grid;', f'<div style="box-shadow: inset 4px 0 0 {zone}; display: grid;', 1)
        o.lien(l, "club", id=r.club)
    if lieu == "tous":
        leg = lambda c, tx: f'<span style="display: inline-flex; align-items: center; gap: 6px; white-space: nowrap"><span style="width: 4px; height: 14px; background: {c}"></span>{tx}</span>'
        o.add(f'<div style="display: flex; flex-wrap: wrap; gap: 6px 18px; padding: 10px 0; font-size: 12px; color: {MUTED}">{leg(RED, f"Top {C.NB_PLAYOFFS} : play-offs")}'
              f'{leg(INK, f"{C.NB_DESCENTE} derniers : descente en D2")}<span style="white-space: nowrap">Départage : points, différence, buts marqués</span></div>')
    o.fin()


def top_liste(df, col, n=10, sous=lambda r: ""):
    o = Sortie()
    rang, prev = 0, None
    for i, (_, r) in enumerate(df.head(n).iterrows(), 1):
        v = int(r[col]); rang = i if v != prev else rang; prev = v
        o.lien(f'<div style="display: grid; grid-template-columns: 24px minmax(0,1fr) 50px 34px; gap: 8px; align-items: center; padding: 8px 0; border-bottom: 1px solid {LINE}">'
               f'<span style="font-family: {COND}; font-weight: 700; color: {RED if rang == 1 else MUTED}">{rang}</span>'
               f'<span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(r.joueur)}</span>'
               f'<span style="font-family: {COND}; font-size: 12px; color: {MUTED}">{C.ABREV_CLUBS.get(r.club, r.club)}</span>{chiffre(v, 18)}</div>',
               "joueur", id=r.id_joueur)
    o.fin()


# ================================================================== LA UNE
def page_une():
    entete_site("une")
    base, N, T = X["base"], X["noms"], X["textes"]
    j = P("j", X["derniere"])
    m = base.matchs[base.matchs.journee == j]
    b = base.buts[base.buts.journee == j]
    if m.empty:
        st.html(ui.empty("Pas encore de match pour cette journée.")); return
    top = m.sort_values(["nb_buts", "dom"], ascending=[False, True]).iloc[0]
    titre, chapo = T.get(f"une:J{j}"), T.get(f"match:J{j}:{top.dom}")
    st.html('<div style="height: 26px"></div>')
    g, d = st.columns([1.55, 1], gap="large")
    with g:
        o = Sortie()
        o.rangee([(ui.pill_item(f"J{x}", x == j), "une", {"j": x}, "content") for x in X["journees"]], style="pills")
        o.add(kick(f"La Une · Journée {j}") + '<div style="height: 14px"></div>')
        hero = (f'<div style="display: grid; grid-template-columns: minmax(0,1fr) 300px; gap: 28px; background: {INK}; color: #fff; border-radius: 14px; padding: 28px">'
                f'<div><div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.14em; color: #F2B8C0">LE MATCH DE LA JOURNÉE</div>'
                + (f'<div style="font-family: {SERIF}; font-size: 38px; line-height: 1.05; margin-top: 12px">{e(titre)}</div>' if titre else
                   f'<div style="font-family: {SERIF}; font-size: 38px; line-height: 1.05; margin-top: 12px">{e(N[top.dom])} - {e(N[top.ext])}</div>')
                + (f'<div style="font-size: 15px; color: #D9D2C6; margin-top: 12px">{e(chapo)}</div>' if chapo else "")
                + f'</div><div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; border-left: 1px solid #444">'
                f'<div style="display: flex; align-items: center; gap: 18px">{ui.logo_or_badge(top.dom, 56, 14, False)}'
                f'<span style="font-family: {SERIF}; font-size: 64px; line-height: 1">{top.bd}-{top.be}</span>{ui.logo_or_badge(top.ext, 56, 14, False)}</div>'
                f'<span style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.1em; color: #D9D2C6">MI-TEMPS {top.mt_d}-{top.mt_e}</span>'
                + (ui.BADGE_ANALYSE if (j, top.dom) in X["rapports"] else "") + "</div></div>")
        o.lien(hero, "match", j=j, dom=top.dom)
        ecart = m.assign(dd=(m.bd - m.be).abs()).sort_values("dd", ascending=False).iloc[0]
        o.add(ui.tiles(ui.tile(len(b), f"buts en J{j}", "red", 40), ui.tile(fr(len(b) / len(m)), "buts / match", numsize=40),
                       ui.tile(f"{max(ecart.bd, ecart.be)}-{min(ecart.bd, ecart.be)}", "plus large écart", numsize=40),
                       ui.tile(len(base.buts), "buts depuis J1", "dark", 40), mt=14))
        o.add(kick(f"Résultats · Journée {j}", mt=26))
        o.fin()
        grille_matchs(m.sort_values("nb_buts", ascending=False))
    with d:
        st.html('<div style="height: 60px"></div>' + kick(f"Classement · Après J{X['derniere']}"))
        classement_table(X["classement"], compact=True)
    st.html('<div style="height: 30px"></div>')
    c1, c2, c3 = st.columns(3, gap="large")
    lig = base.stats_ligue()
    with c1:
        tr = lig["tranches"]; mx = max(tr.values())
        st.html(kick("Quand tombent les buts") + sous_titre("Par tranche de 5 minutes, toute la D1.")
                + card(vbars(tr, 380, 220, hi=[k for k, v in tr.items() if v == mx], aria="Buts par tranche de 5 minutes"), 12))
    with c2:
        org = lig["origines"]; n = lig["nb_buts"]
        st.html(kick("D’où viennent les buts") + sous_titre(f"Origine des {n} buts saisis.")
                + card(ui.hbars([(X["orig"].get(k, k), v, RED if i < 2 else INK) for i, (k, v) in enumerate(org.items())], max(org.values()), 120), 16))
    with c3:
        st.html(kick("Meilleurs buteurs") + sous_titre(f"{lig['part_avec_passe']} % des buts ont un passeur."))
        top_liste(X["stats"][X["stats"].Buts > 0], "Buts", 8)
        st.html(kick("Meilleurs passeurs", mt=18))
        top_liste(X["stats"][X["stats"].Passes > 0].sort_values(["Passes", "Buts"], ascending=False), "Passes", 5)
    pied()


# ================================================================== RÉSULTATS
def page_matchs():
    entete_site("matchs")
    j = P("j", X["derniere"])
    o = Sortie()
    o.add('<div style="height: 22px"></div>')
    o.rangee([(ui.pill_item(f"Journée {x}", x == j), "matchs", {"j": x}, "content") for x in X["journees"]], style="pills")
    o.add(kick(f"Résultats · Journée {j}"))
    o.fin()
    grille_matchs(X["base"].matchs[X["base"].matchs.journee == j])
    pied()


def page_match():
    entete_site("matchs")
    base, N, T = X["base"], X["noms"], X["textes"]
    j, dom = P("j", X["derniere"]), st.query_params.get("dom")
    mm = base.matchs[(base.matchs.journee == j) & (base.matchs.dom == dom)]
    if mm.empty:
        st.html(ui.section(ui.empty("Match introuvable."), pad="20px 0")); return
    m = mm.iloc[0]
    b = base.match(j, dom)
    rapport = X["rapports"].get((j, dom))
    choix = ["resume", "timeline"] + (["rapport"] if rapport else [])
    onglet = X["choix"]("onglet", choix, "resume")

    def buteurs(club, align):
        d = b[b.club_marque == club]
        return "<br>".join(f'{e(n)} ' + " ".join(f"{x}’" for x in g.minute) for n, g in d.groupby("buteur", sort=False))
    o = Sortie()
    o.add(f'<div style="height: 18px"></div><section style="background: {INK}; color: #fff; border-radius: 14px; padding: 26px 32px; '
          f'display: grid; grid-template-columns: minmax(0,1fr) auto minmax(0,1fr); align-items: center; gap: 24px">'
          f'<div style="display: flex; align-items: center; gap: 16px; justify-content: flex-end"><span style="font-family: {SERIF}; font-size: 38px">{e(N[m.dom])}</span>{ui.logo_or_badge(m.dom, 64, 15, False)}</div>'
          f'<div style="text-align: center">{"<div style=\"margin-bottom: 8px\">" + ui.BADGE_ANALYSE + "</div>" if rapport else ""}'
          f'<div style="font-family: {SERIF}; font-size: 84px; line-height: 1">{m.bd}-{m.be}</div>'
          f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.12em; color: #D9D2C6; margin-top: 6px">JOURNÉE {j} · MI-TEMPS {m.mt_d}-{m.mt_e}</div></div>'
          f'<div style="display: flex; align-items: center; gap: 16px">{ui.logo_or_badge(m.ext, 64, 15, False)}<span style="font-family: {SERIF}; font-size: 38px">{e(N[m.ext])}</span></div>'
          f'<div style="text-align: right; font-size: 13px; color: #D9D2C6">{buteurs(m.dom, "right")}</div><div></div>'
          f'<div style="font-size: 13px; color: #D9D2C6">{buteurs(m.ext, "left")}</div></section>')
    o.rangee([(f'<div style="padding: 12px 18px 12px 0; font-family: {COND}; font-weight: 700; font-size: 13px; letter-spacing: 0.08em; color: {RED}">FICHE {e(N[c]).upper()} →</div>',
               "club", {"id": c}, "content") for c in (m.dom, m.ext)], style="cards")
    o.fin()
    onglets_d("match", {"j": j, "dom": dom}, [("resume", "Résumé"), ("timeline", "Timeline")] + ([("rapport", "Analyse du match")] if rapport else []), onglet)
    if onglet == "resume":
        g, d = st.columns([1.3, 1], gap="large")
        txt = T.get(f"match:J{j}:{dom}")
        n_d = b[(b.club_marque == m.dom) & b.id_buteur.notna()].id_buteur.nunique()
        n_e = b[(b.club_marque == m.ext) & b.id_buteur.notna()].id_buteur.nunique()
        with g:
            st.html(kick("L’essentiel") + (f'<div style="font-family: {SERIF}; font-size: 28px; line-height: 1.15; margin-top: 12px">{e(txt)}</div>' if txt else "")
                    + ui.tiles(ui.tile(len(b), "buts", "dark", 38), ui.tile(f"{n_d}-{n_e}", "buteurs différents", numsize=38),
                               ui.tile(int(b.id_passeur.notna().sum()), "buts avec passe", "red", 38),
                               ui.tile(int((b.minute > 35).sum()), "buts 5 dern. min.", numsize=38), mt=16)
                    + kick("Score minute par minute", mt=26) + '<div style="height: 10px"></div>' + card(ui.score_progressif(b, m.dom, m.ext, N), 16))
        with d:
            o_d, o_e = b[b.club_marque == m.dom].origine_but.value_counts(), b[b.club_marque == m.ext].origine_but.value_counts()
            keys = sorted(set(o_d.index) | set(o_e.index), key=lambda k: -(o_d.get(k, 0) + o_e.get(k, 0)))
            rows = []
            for lab, f in [("Buts 1re mi-temps", lambda x: (x.periode == 1).sum()), ("Buts 2e mi-temps", lambda x: (x.periode == 2).sum()),
                           ("Buts avec passe", lambda x: x.id_passeur.notna().sum()), ("Buteurs différents", lambda x: x.id_buteur.nunique())]:
                rows.append((lab, int(f(b[b.club_marque == m.dom])), int(f(b[b.club_marque == m.ext]))))
            st.html(kick("D’où viennent les buts") + '<div style="height: 12px"></div>'
                    + card(ui.mirror([(X["orig"].get(k, k), int(o_d.get(k, 0)), int(o_e.get(k, 0))) for k in keys], N[m.dom], N[m.ext], mid_w=130), 16)
                    + kick("Face-à-face", mt=26) + '<div style="height: 12px"></div>' + card(ui.mirror(rows, N[m.dom], N[m.ext], mid_w=140), 16))
            if rapport:
                st.html(card(f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.1em; color: {RED}">MATCH ANALYSÉ</div>'
                             f'<div style="font-size: 14px; margin-top: 6px">Tirs, duels, pertes, gardiens, joueur par joueur : voir l’onglet Analyse du match.</div>', 14)
                        .replace(f"background: {PAPER}", f"background: {PAPER}; margin-top: 20px"))
    elif onglet == "timeline":
        tpl = "grid-template-columns: 44px 70px minmax(0,1fr) minmax(0,1fr) 150px 60px"
        cols = [("Min.", "left"), ("Équipe", "left"), ("Buteur", "left"), ("Passeur", "left"), ("Origine", "left"), ("Score", "right")]
        rows = [[f'<span style="font-family: {COND}; font-weight: 700; color: {RED}">{r.minute}’</span>', cond(C.ABREV_CLUBS.get(r.club_marque, r.club_marque), MUTED),
                 f'<span style="font-weight: 600">{e(r.buteur)}</span>', e(r.passeur) if isinstance(r.passeur, str) else f'<span style="color: {MUTED}">sans passe</span>',
                 f'<span style="font-size: 13px">{e(X["orig"].get(r.origine_but, str(r.origine_but)))}</span>', chiffre(f"{r.score_dom_apres}-{r.score_ext_apres}", 18)]
                for r in b.itertuples()]
        head, lignes = tableau_html(cols, rows, tpl)
        o = Sortie(); o.add(kick(f"Les {len(b)} buts") + '<div style="height: 8px"></div>' + head)
        mt = False
        for r, l in zip(b.itertuples(), lignes):
            if r.periode == 2 and not mt:
                o.add(f'<div style="padding: 6px 10px; background: {INK}; color: #fff; font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.12em">MI-TEMPS · {m.mt_d}-{m.mt_e}</div>')
                mt = True
            if r.id_buteur:
                o.lien(l, "joueur", id=r.id_buteur)
            else:
                o.add(l)
        o.fin()
    else:
        r = X["analyses"].get((j, dom))
        if r is None:        # chiffres non lus : on montre les pages du PDF
            X["afficher_rapport"](rapport, colonnes=3, largeur=800)
        else:
            c = r["collectif"]
            g, d = st.columns([1.35, 1], gap="large")
            with g:
                st.html(kick("L’analyse en chiffres") + ui.tiles(
                    ui.tile(f"{analyse.conversion(r, 0)} %", f"tirs cadrés convertis {e(N[m.dom])}", "dark", 40),
                    ui.tile(f"{analyse.conversion(r, 1)} %", f"tirs cadrés convertis {e(N[m.ext])}", "red", 40),
                    ui.tile(f"{c['tirs'][0]}-{c['tirs'][1]}", "tirs", numsize=40),
                    ui.tile(f"{c['duels'][0][0]}-{c['duels'][1][0]}", "duels gagnés", numsize=40),
                    ui.tile(f"{c['inter'][0]}-{c['inter'][1]}", "interceptions", numsize=40), mt=14)
                    + kick("Face-à-face complet", mt=28) + '<div style="height: 12px"></div>'
                    + card(analyse.miroir(analyse.face_a_face(r), N[m.dom], N[m.ext], mid_w=170, taille=18), 20))
            with d:
                st.html(kick("Les tirs") + '<div style="height: 12px"></div>' + card(analyse.bloc_tirs(r, N), 18)
                        + kick("Gardiens", mt=28) + '<div style="display: flex; flex-direction: column; gap: 10px; margin-top: 12px">'
                        + "".join(analyse.cartes_gardiens(r, N)) + "</div>")
                st.html('<div style="height: 14px"></div>')
                X["bouton_pdf"](rapport)
            st.html('<div style="height: 30px"></div>' + kick("Joueurs de champ"))
            cols = st.columns(2, gap="large")
            for k, col in enumerate(cols):
                with col:
                    head, lignes = analyse.tableau_joueurs(r, k, analyse.COLS_ORDI, pad="10px")
                    o = Sortie()
                    o.add(f'<div style="font-family: {SERIF}; font-size: 24px; margin: 12px 0 6px; color: {INK if k == 0 else RED}">{e(N[r["clubs"][k]])}</div>' + head)
                    for h, i in lignes:
                        if i:
                            o.lien(h, "joueur", id=i)
                        else:
                            o.add(h)
                    o.fin()
            st.html(f'<div style="font-size: 12px; color: {MUTED}; margin-top: 14px">{analyse.LEGENDE} Cliquer un joueur ouvre sa fiche quand il a déjà marqué ou passé.</div>')
    pied()


# ================================================================== CLASSEMENTS
def page_classements():
    entete_site("classements")
    lieu = X["choix"]("lieu", ["tous", "dom", "ext"], "tous")
    vue = X["choix"]("vue", ["buteurs", "passeurs", "bp"], "buteurs")
    st.html('<div style="height: 22px"></div>')
    g, d = st.columns([1.6, 1], gap="large")
    with g:
        o = Sortie()
        o.add(kick("Classement des équipes"))
        o.rangee([(ui.pill_item(lab, k == lieu), "classements", {"lieu": k, "vue": vue}, "content") for k, lab in
                  [("tous", "Général"), ("dom", "Domicile"), ("ext", "Extérieur")]], style="pills")
        o.fin()
        classement_table(X["base"].classement(lieu), lieu)
    with d:
        o = Sortie()
        o.add(kick("Classements individuels"))
        o.rangee([(ui.seg_item(lab, k == vue), "classements", {"vue": k, "lieu": lieu}) for k, lab in
                  [("buteurs", "Buteurs"), ("passeurs", "Passeurs"), ("bp", "Buts + passes")]], style="seg")
        o.add('<div style="height: 8px"></div>')
        o.fin()
        col, tri = {"buteurs": ("Buts", ["Buts", "Passes"]), "passeurs": ("Passes", ["Passes", "Buts"]), "bp": ("B+P", ["B+P", "Buts"])}[vue]
        s = X["stats"]
        top_liste(s[s[col] > 0].sort_values(tri + ["joueur"], ascending=[False, False, True]), col, 20)
        o = Sortie()
        o.lien(f'<div style="padding: 12px 0; font-family: {COND}; font-weight: 700; font-size: 13px; letter-spacing: 0.08em; color: {RED}">TOUTES LES STATISTIQUES JOUEURS</div>', "joueurs")
        o.fin()
    pied()


# ================================================================== STATISTIQUES (FBref)
COLS_STATS = {"joueur": "Joueur", "club": "Club", "MJ_club": "MJ", "Buts": "Buts", "Passes": "Passes", "B+P": "B+P",
              "Buts_par_match": "B/M", "Buts_1MT": "1re MT", "Buts_2MT": "2e MT", "Buts_dom": "Dom", "Buts_ext": "Ext",
              "Att_placee": "Att. placée", "Transition": "Transition", "Att_rapide": "Att. rapide", "CPA": "CPA",
              "Power_play": "Power play", "Penalty": "Penalty", "Buts_ouverture": "1er but", "Pct_buts_club": "% club"}


def _sous_base(base, j1, j2, lieu, groupe):
    b = base.buts[(base.buts.journee >= j1) & (base.buts.journee <= j2)]
    m = base.matchs[(base.matchs.journee >= j1) & (base.matchs.journee <= j2)]
    if lieu == "Domicile":
        b = b[b.club_marque == b.club_dom]
    elif lieu == "Extérieur":
        b = b[b.club_marque == b.club_ext]
    if groupe != "Toutes":
        b = b[b.groupe_origine == groupe]
    return data.Base(buts=b, matchs=m, joueurs=base.joueurs, clubs=base.clubs, compos=base.compos)


def page_joueurs():
    entete_site("stats")
    base, N = X["base"], X["noms"]
    vue = X["choix"]("vue", ["tableau", "comparer"], "tableau")
    o = Sortie()
    o.add(f'<div style="height: 24px"></div><div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.14em; color: {RED}">STATISTIQUES · JOUEURS</div>'
          f'<h1 style="margin: 6px 0 0; font-family: {SERIF}; font-weight: 400; font-size: 44px; line-height: 1">Tous les buteurs et passeurs de D1</h1>')
    o.rangee([(ui.pill_item(lab, k == vue), "joueurs", {"vue": k}, "content") for k, lab in [("tableau", "Tableau complet"), ("comparer", "Comparer 2 joueurs")]], style="pills")
    o.fin()
    js = X["journees"]
    if vue == "tableau":
        with st.container(horizontal=True, key="filtres"):
            q = st.text_input("Joueur", placeholder="Rechercher…")
            clubs = st.multiselect("Clubs", sorted(N), format_func=lambda c: N[c], placeholder="Tous")
            j1, j2 = st.select_slider("Journées", options=js, value=(js[0], js[-1]), format_func=lambda x: f"J{x}") if len(js) > 1 else (js[0], js[0])
            lieu = st.selectbox("Lieu", ["Tous", "Domicile", "Extérieur"])
            groupe = st.selectbox("Phase de jeu", ["Toutes", "Attaque placée", "Transition off", "Attaque rapide", "CPA", "Power play", "Penalty"])
            mode = st.radio("Valeurs", ["Totaux", "Par match"], horizontal=True)
        sb = _sous_base(base, j1, j2, lieu, groupe)
        s = sb.stats_joueurs() if len(sb.buts) else pd.DataFrame(columns=["id_joueur"] + list(COLS_STATS))
        if clubs:
            s = s[s.club.isin(clubs)]
        if q:
            s = s[s.joueur.str.contains(q.strip(), case=False, regex=False)]
        s = s[(s.Buts > 0) | (s.Passes > 0)].reset_index(drop=True)
        aff = s.copy()
        aff["club"] = aff.club.map(lambda c: N.get(c, c))
        if mode == "Par match":
            for c in ["Buts", "Passes", "B+P", "Buts_1MT", "Buts_2MT", "Buts_dom", "Buts_ext", "Att_placee", "Transition", "Att_rapide", "CPA", "Power_play", "Penalty", "Buts_ouverture"]:
                aff[c] = (aff[c] / aff.MJ_club.where(aff.MJ_club > 0)).round(2)
        aff = aff[list(COLS_STATS)].rename(columns=COLS_STATS)
        st.html(f'<div style="font-size: 13px; color: {MUTED}; margin-bottom: 8px">{len(aff)} joueurs · cliquer un en-tête pour trier, une ligne pour ouvrir la fiche du joueur.</div>')
        cfg = {"Buts": st.column_config.NumberColumn(width="small"), "Joueur": st.column_config.TextColumn(width="large"),
               "% club": st.column_config.NumberColumn(format="%d %%")}
        ev = st.dataframe(aff, hide_index=True, use_container_width=True, height=min(38 * (len(aff) + 1) + 4, 760),
                          column_config=cfg, on_select="rerun", selection_mode="single-row", key="tab_stats")
        if ev and ev.selection.rows:
            st.switch_page(nav.PAGES["joueur"], query_params={"id": s.iloc[ev.selection.rows[0]].id_joueur})
        st.download_button("Exporter en CSV", aff.to_csv(index=False, sep=";").encode("utf-8-sig"), file_name="d1futsal_stats_joueurs.csv", mime="text/csv")
        st.html(f'<div style="font-size: 12px; color: {MUTED}; line-height: 1.6; margin-top: 10px">MJ : matchs joués par l’équipe. B/M : buts par match. '
                f'CPA : corner, touche, coup franc, jet franc. 1er but : buts d’ouverture du score. % club : part des buts de son équipe. '
                f'Les filtres Lieu et Phase de jeu s’appliquent aux buts et aux passes.</div>')
    else:
        s = X["stats"]
        opts = s.sort_values(["B+P", "Buts"], ascending=False).id_joueur.tolist()
        lab = dict(zip(s.id_joueur, s.joueur + " · " + s.club.map(lambda c: N.get(c, c))))
        with st.container(horizontal=True, key="filtres"):
            a = st.selectbox("Joueur 1", opts, index=0, format_func=lambda i: lab[i])
            b_ = st.selectbox("Joueur 2", opts, index=1 if len(opts) > 1 else 0, format_func=lambda i: lab[i])
        A, B = s.set_index("id_joueur").loc[a], s.set_index("id_joueur").loc[b_]
        rows = [(COLS_STATS[c], A[c], B[c]) for c in ["Buts", "Passes", "B+P", "Buts_1MT", "Buts_2MT", "Buts_dom", "Buts_ext", "Att_placee", "Transition",
                                                      "Att_rapide", "CPA", "Power_play", "Buts_ouverture"]]
        rows = [(l, int(x), int(y)) for l, x, y in rows]
        g, d = st.columns(2, gap="large")
        for col, J in [(g, A), (d, B)]:
            with col:
                st.html(card(f'<div style="display: flex; gap: 16px; align-items: center">{ui.photo(J.name, 80, 96)}<div>'
                             f'<div style="font-family: {SERIF}; font-size: 28px; line-height: 1.05">{e(J.joueur)}</div>'
                             f'<div style="font-weight: 600; margin-top: 6px">{e(N.get(J.club, J.club))}</div></div></div>'
                             + ui.tiles(ui.tile(int(J.Buts), "buts", "red"), ui.tile(int(J.Passes), "passes", "dark"), ui.tile(fr(J.Buts_par_match, 2) if pd.notna(J.Buts_par_match) else "-", "buts / match")), 18))
        st.html('<div style="height: 22px"></div>' + kick("Face-à-face") + '<div style="height: 12px"></div>'
                + card(ui.mirror(rows, A.joueur, B.joueur, mid_w=160), 20))
    pied()


# ================================================================== CLUBS
def page_clubs():
    entete_site("clubs")
    N = X["noms"]
    t = X["classement"].sort_values("club")
    o = Sortie()
    o.add('<div style="height: 24px"></div>' + kick("Les 12 clubs de D1"))
    lst = list(t.itertuples())
    for k in range(0, len(lst), 4):
        o.rangee([(f'<div style="height: 100%; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 22px 10px; '
                   f'background: {PAPER}; border: 1.5px solid {INK}; border-radius: 12px">{ui.logo_or_badge(r.club, 64, 15)}'
                   f'<span style="font-family: {SERIF}; font-size: 24px; text-align: center">{e(N[r.club])}</span>'
                   f'<span style="font-family: {COND}; font-size: 13px; color: {MUTED}">{r.Rg}e · {r.Pts} pts · {r.BP}-{r.BC}</span>'
                   f'<span style="display: inline-flex; gap: 3px">{"".join(ui.form_chip(x, 20) for x in r.forme)}</span></div>', "club", {"id": r.club})
                  for r in lst[k:k + 4]], style="dgrid")
    o.fin()
    pied()


def pitch(club):
    """Compo type sur un terrain (vide tant que la fiche n'est pas remplie)."""
    comp = X["base"].compos
    comp = comp[comp.club_court == club] if len(comp) else comp
    jref = X["jref"]
    pos = {"GB": (8, 50), "Fixo": (30, 50), "Ailier G": (55, 18), "Ailier D": (55, 82), "Pivot": (82, 50)}
    h = (f'<div style="position: relative; width: 100%; height: 240px; background: {INK}; border-radius: 12px; overflow: hidden">'
         f'<div style="position: absolute; inset: 12px; border: 1.5px solid #5A5A5A"></div><div style="position: absolute; left: 50%; top: 12px; bottom: 12px; width: 1.5px; background: #5A5A5A"></div>')
    for p, (x, y) in pos.items():
        i = None
        if len(comp):
            r = comp[comp.poste_terrain == p]
            i = r.id_joueur.iloc[0] if len(r) and isinstance(r.id_joueur.iloc[0], str) else None
        nom = jref.nom_affiche.get(i, "") if i else ""
        court = nom.split()[-1] if nom else p
        h += (f'<div style="position: absolute; left: calc({x}% - 45px); top: calc({y}% - 26px); width: 90px; display: flex; flex-direction: column; align-items: center; gap: 4px">'
              f'<div style="width: 34px; height: 34px; border-radius: 50%; background: {CR}; border: 2px solid {RED if p == "Pivot" else "#fff"}"></div>'
              f'<span style="font-family: {COND}; font-weight: 700; font-size: 11px; color: #fff; letter-spacing: 0.04em; text-align: center">{e(court).upper()}</span></div>')
    vide = "" if (len(comp) and comp.id_joueur.notna().any()) else f'<div style="font-size: 12px; color: {MUTED}; margin-top: 6px">Compo type à renseigner dans la fiche club.</div>'
    return h + "</div>" + vide


def page_club():
    entete_site("clubs")
    base, N = X["base"], X["noms"]
    club = st.query_params.get("id")
    if club not in N:
        st.html(ui.empty("Club introuvable.")); return
    s = base.stats_club(club)
    cl = s["classement"]
    info = base.clubs.set_index("club_court").loc[club]
    meta = " · ".join(x for x in [info.get("salle"), f"Coach {info.get('coach')}" if isinstance(info.get("coach"), str) else None, info.get("site_web")] if isinstance(x, str) and x)
    tuile = lambda v, l, rouge=False: (f'<div style="{"background: " + RED if rouge else "border: 1.5px solid #fff"}; border-radius: 10px; padding: 12px 18px; text-align: center">'
                                       f'<div style="font-family: {SERIF}; font-size: 40px; line-height: 1">{v}</div><div style="font-family: {COND}; font-size: 11px; letter-spacing: 0.1em; color: #E9E2D5">{l}</div></div>')
    st.html(f'<div style="height: 18px"></div><section style="background: {INK}; color: #fff; border-radius: 14px; padding: 26px 32px; display: flex; align-items: center; gap: 24px">'
            f'{ui.logo_or_badge(club, 96, 18, False)}<div style="flex: 1"><div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.14em; color: #F2B8C0">CLUB</div>'
            f'<div style="font-family: {SERIF}; font-size: 48px; line-height: 1; margin-top: 6px">{e(N[club])}</div>'
            + (f'<div style="color: #D9D2C6; margin-top: 8px">{e(meta)}</div>' if meta else "")
            + f'</div><div style="display: flex; gap: 10px">{tuile(str(cl["Rg"]) + "<sup style=\"font-size: 16px\">e</sup>", "RANG")}{tuile(cl["Pts"], "POINTS")}'
            f'{tuile(cl["BP"], "MARQUÉS")}{tuile(cl["BC"], "ENCAISSÉS", True)}</div></section><div style="height: 26px"></div>')
    g, d = st.columns([1.5, 1], gap="large")
    lig = base.stats_ligue(); nb_club = max(sum(s["origines"].values()), 1)
    with g:
        st.html(kick("Marqués / encaissés par tranche de 5 min") + '<div style="height: 12px"></div>'
                + card(bars_groupees(s["tranches_marques"], s["tranches_encaisses"]), 14))
        cmp = ""
        for k in ["attaque placée", "transition off", "attaque rapide", "corner", "touche off", "power play", "coup franc"]:
            a = round(100 * s["origines"].get(k, 0) / nb_club); bl = round(100 * lig["origines"].get(k, 0) / max(lig["nb_buts"], 1))
            cmp += (f'<div style="display: grid; grid-template-columns: 130px minmax(0,1fr) 96px; gap: 10px; align-items: center"><span style="font-size: 13px">{X["orig"][k]}</span>'
                    f'<div style="position: relative; height: 18px; background: {SOFT}; border-radius: 3px"><div style="position: absolute; left: 0; top: 0; bottom: 0; width: {min(a * 2, 100)}%; background: {INK}; border-radius: 3px"></div>'
                    f'<div style="position: absolute; top: -3px; bottom: -3px; left: {min(bl * 2, 99)}%; width: 3px; background: {RED}"></div></div>'
                    f'<span style="font-family: {COND}; font-size: 13px"><b>{a} %</b> <span style="color: {MUTED}">/ {bl} %</span></span></div>')
        st.html(kick(f"Profil offensif : {N[club]} vs moyenne D1", mt=28) + sous_titre("Barre noire : part des buts du club. Trait rouge : moyenne de la ligue.")
                + card(f'<div style="display: flex; flex-direction: column; gap: 12px">{cmp}</div>', 18))
        st_ = X["stats"].set_index("id_joueur")
        eff = X["joueurs"][X["joueurs"].club_court == club]
        tpl = "grid-template-columns: 44px minmax(0,1fr) 110px 54px 54px 54px 60px"
        cols = [("N°", "left"), ("Joueur", "left"), ("Poste", "left"), ("Buts", "center"), ("Passes", "center"), ("B+P", "center"), ("% club", "right")]
        rows, ids = [], []
        for r in eff.itertuples():
            bt, pa = int(st_.Buts.get(r.id_joueur, 0)), int(st_.Passes.get(r.id_joueur, 0))
            num = str(r.numero).replace(".0", "") if pd.notna(getattr(r, "numero", None)) else ""
            rows.append((bt + pa, bt, [cond(num, MUTED), f'<span style="font-weight: 600">{e(r.nom_affiche)}</span>', cond(r.poste if isinstance(getattr(r, "poste", None), str) else "", MUTED),
                                       chiffre(bt), chiffre(pa, 17, MUTED), cond(bt + pa), cond(f"{int(st_.Pct_buts_club.get(r.id_joueur, 0))} %")]))
            ids.append(r.id_joueur)
        ordre = sorted(range(len(rows)), key=lambda i: (-rows[i][0], -rows[i][1]))
        head, lignes = tableau_html(cols, [rows[i][2] for i in ordre], tpl)
        o = Sortie(); o.add(kick("Effectif et production", mt=28) + '<div style="height: 8px"></div>' + head)
        for i, l in zip(ordre, lignes):
            o.lien(l, "joueur", id=ids[i])
        o.fin()
    with d:
        st.html(kick("Forme") + f'<div style="display: flex; gap: 6px; margin-top: 12px">{"".join(ui.form_chip(x, 32) for x in cl["forme"])}</div>'
                + kick("Compo type", mt=28) + '<div style="height: 12px"></div>' + pitch(club))
        o = Sortie(); o.add(kick("Matchs", mt=28))
        for r in s["matchs"].itertuples():
            home = r.dom == club; f_, a_ = (r.bd, r.be) if home else (r.be, r.bd); opp = r.ext if home else r.dom
            res = "V" if f_ > a_ else ("N" if f_ == a_ else "D")
            o.lien(f'<div style="display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid {LINE}">'
                   f'<span style="font-family: {COND}; font-weight: 700; color: {MUTED}; width: 28px">J{r.journee}</span><span style="font-family: {COND}; font-size: 12px; color: {MUTED}; width: 30px">{"DOM" if home else "EXT"}</span>'
                   f'{ui.logo_or_badge(opp, 26, 8)}<span style="flex: 1; font-weight: 600">{e(N[opp])}</span>{ui.BADGE_ANALYSE if (r.journee, r.dom) in X["rapports"] else ""}'
                   f'{chiffre(f"{f_}-{a_}", 20)}{ui.form_chip(res, 22)}</div>', "match", j=r.journee, dom=r.dom)
        o.fin()
        oe = s["origines_encaisses"]
        st.html(kick("Comment le club encaisse", mt=28) + '<div style="height: 12px"></div>'
                + card(ui.hbars([(X["orig"].get(k, k), v, RED if i == 0 else INK) for i, (k, v) in enumerate(oe.items())], max(oe.values()) if oe else 1), 16))
    pied()


# ================================================================== JOUEUR
def page_joueur():
    entete_site("stats")
    base, N = X["base"], X["noms"]
    i = st.query_params.get("id")
    jref = X["jref"]
    if i not in jref.index:
        st.html(ui.empty("Joueur introuvable.")); return
    j = jref.loc[i]; club = j.club_court
    S = X["stats"]
    s = S.set_index("id_joueur").loc[i] if i in set(S.id_joueur) else None
    bj = base.buts[base.buts.id_buteur == i].sort_values(["journee", "minute"])
    pj = base.buts[base.buts.id_passeur == i].sort_values(["journee", "minute"])
    nb, npas = len(bj), len(pj)
    mj = int(X["classement"].set_index("club").J.get(club, 0))
    rang = int((S.Buts > nb).sum()) + 1
    sur = " · ".join(x for x in [f"N° {int(j.numero)}" if pd.notna(j.get("numero")) else None, j.get("poste") if isinstance(j.get("poste"), str) else None,
                                 j.get("nationalite") if isinstance(j.get("nationalite"), str) else None] if x)
    st.html('<div style="height: 26px"></div>')
    g, d = st.columns([1, 1.25], gap="large")
    with g:
        o = Sortie()
        o.add(card(f'<div style="display: flex; gap: 18px; align-items: center">{ui.photo(i, 120, 146)}<div style="min-width: 0">'
                   + (f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.12em; color: {RED}">{e(sur)}</div>' if sur else "")
                   + f'<div style="font-family: {SERIF}; font-size: 38px; line-height: 1.02; margin-top: 6px">{e(j.nom_affiche)}</div></div></div>', 18))
        o.lien(f'<div style="display: flex; align-items: center; gap: 10px; padding: 12px 0; font-weight: 600; border-bottom: 1px solid {LINE}">{ui.logo_or_badge(club, 28, 9)}'
               f'{e(N.get(club, club))}<span style="margin-left: auto; font-family: {COND}; font-size: 12px; letter-spacing: 0.08em; color: {RED}">FICHE CLUB</span></div>', "club", id=club)
        o.add(f'<div style="display: flex; align-items: flex-end; gap: 16px; margin-top: 20px"><div style="font-family: {SERIF}; font-size: 110px; line-height: 0.85; color: {RED}">{nb}</div>'
              f'<div style="padding-bottom: 8px"><div style="font-family: {COND}; font-weight: 700; font-size: 18px; letter-spacing: 0.1em">BUT{"S" if nb > 1 else ""}</div>'
              f'<div style="font-size: 14px; color: {MUTED}">{"Meilleur buteur de D1" if rang == 1 and nb else (f"{rang}e buteur de D1" if nb else "Pas encore buteur")}</div></div></div>'
              + ui.tiles(ui.tile(npas, "passes déc.", "dark"), ui.tile(nb + npas, "buts + passes"), ui.tile(fr(nb / mj, 2) if mj else "-", "buts / match"), mt=16)
              + ui.tiles(ui.tile(int(s.Pct_buts_club) if s is not None else 0, "% buts du club"), ui.tile(int(bj.ouverture.sum()), "buts d’ouverture"),
                         ui.tile(f"{int((bj.periode == 1).sum())}/{int((bj.periode == 2).sum())}", "1re / 2e MT"), mt=8))
        o.fin()
    with d:
        h = ""
        if nb:
            og = bj.origine_but.value_counts()
            h += (kick("Quand il marque") + '<div style="height: 10px"></div>' + card(ui.frise([(r.minute, f"{r.minute}’") for r in bj.itertuples()]), 14)
                  + kick("Comment il marque", mt=26) + '<div style="height: 12px"></div>'
                  + card(ui.hbars([(X["orig"].get(k, k), int(v), RED if n == 0 else INK) for n, (k, v) in enumerate(og.items())], int(og.max())), 16))
        if npas:
            c = pj.groupby("buteur").size().sort_values(ascending=False)
            h += kick("Ses passes décisives pour", mt=26 if nb else 0) + '<div style="height: 12px"></div>' + card(ui.hbars([(k, int(v), INK) for k, v in c.items()], int(c.max()), 190), 16)
        if not h:
            h = ui.empty("Aucun but ni passe décisive pour l’instant.")
        st.html(h)
        oa = Sortie()
        X["section_analyses"](oa, i, club, mj)
        oa.fin()
    st.html('<div style="height: 26px"></div>')
    g2, d2 = st.columns(2, gap="large")
    for col, df, titre, mode in [(g2, bj, f"{nb} but{'s' if nb > 1 else ''}", "buts"), (d2, pj, f"{npas} passe{'s' if npas > 1 else ''} décisive{'s' if npas > 1 else ''}", "passes")]:
        with col:
            tpl = "grid-template-columns: 36px 44px minmax(0,1fr) 130px 56px"
            cols = [("J", "left"), ("Min.", "left"), ("Adversaire", "left"), ("Passeur" if mode == "buts" else "Buteur", "left"), ("Score", "right")]
            rows = []
            for r in df.itertuples():
                opp = r.club_ext if r.club_marque == r.club_dom else r.club_dom
                autre = (r.passeur if isinstance(r.passeur, str) else "sans passe") if mode == "buts" else r.buteur
                rows.append([cond(f"J{r.journee}", MUTED), f'<span style="font-family: {COND}; font-weight: 700; color: {RED}">{r.minute}’</span>',
                             f'<span><b>{e(N[opp])}</b><br><span style="font-size: 12px; color: {MUTED}">{e(X["orig"].get(r.origine_but, str(r.origine_but)))}</span></span>',
                             f'<span style="font-size: 13px">{e(autre)}</span>', chiffre(f"{r.score_dom_apres}-{r.score_ext_apres}", 18)])
            head, lignes = tableau_html(cols, rows, tpl)
            o = Sortie(); o.add(kick(titre) + '<div style="height: 8px"></div>' + (head if rows else ui.empty("Rien pour l’instant.")))
            for r, l in zip(df.itertuples(), lignes):
                o.lien(l, "match", j=r.journee, dom=r.club_dom)
            o.fin()
    pied()


# ================================================================== MÉTHODOLOGIE
def page_methodo():
    entete_site("methodo")
    lig = X["base"].stats_ligue()
    p = lambda t: f'<p style="font-size: 16px; line-height: 1.6; max-width: 760px">{t}</p>'
    st.html('<div style="height: 26px"></div>' + kick("Méthodologie et sources")
            + f'<h1 style="font-family: {SERIF}; font-weight: 400; font-size: 44px; margin: 14px 0">Comment sont faites ces données</h1>'
            + p("Toutes les données sont collectées à la main par Victor Geoffroy à partir des matchs de D1 Futsal. Elles ne sont pas officielles. "
                "Chaque but est saisi avec sa minute, son score, son buteur, son passeur et la phase de jeu qui l’a amené.")
            + p("Avant chaque mise en ligne, des contrôles automatiques vérifient l’enchaînement des scores, la cohérence buteur/passeur et le rattachement "
                "de chaque joueur à un seul club. Si un contrôle échoue, rien n’est publié.")
            + p("Le match diffusé de chaque journée fait l’objet d’un rapport d’analyse détaillé (tirs, duels, pertes, gardiens), à retrouver dans l’onglet Analyse de la fiche du match, avec le PDF complet en téléchargement.")
            + p(f"Classement : 3 points la victoire, 1 le nul. Départage par différence de buts puis buts marqués. Les {C.NB_PLAYOFFS} premiers sont qualifiés "
                f"pour les play-offs, les {C.NB_DESCENTE} derniers descendent en D2.")
            + p("Crédits : clubs, joueurs, FFF. Photos et logos avec l’accord de leurs auteurs.")
            + '<div style="max-width: 760px">' + ui.tiles(ui.tile(lig["nb_buts"], "buts saisis", "red", 40), ui.tile(lig["nb_matchs"], "matchs", numsize=40),
                                                          ui.tile(f'{lig["part_avec_passe"]} %', "avec passeur", numsize=40), ui.tile(len(X["rapports"]), "matchs analysés", "dark", 40)) + "</div>")
    pied()


PAGES_ORDI = {"une": page_une, "matchs": page_matchs, "match": page_match, "classements": page_classements, "clubs": page_clubs,
              "club": page_club, "joueurs": page_joueurs, "joueur": page_joueur, "methodo": page_methodo}
