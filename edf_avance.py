"""
Stats avancées de l'Équipe de France (lot D), calculées à partir des .json du générateur de rapports.

Chaque action du .json a : équipe (e), type (a), position (x : couloir 0-20 vu par l'équipe, y : 0 = son but, 40 = but adverse),
mi-temps (mt) et minute de jeu (min, 0-40). Rien n'est saisi en plus : tout vient du tag Nacsport et de l'appli temps de jeu.

- Pressing efficace : ballon gagné (récupération, interception) dans le camp adverse, suivi d'un tir de la même équipe en 10 s.
- Pertes dangereuses : ballon perdu (perte de balle, passe loupée) suivi d'un tir adverse en 10 s.
- Zones de tir : 9 zones du demi-terrain offensif (3 distances x 3 couloirs).
- Duos : +/- des paires de joueurs de champ présents ensemble sur le terrain aux buts.
- Présences : temps de jeu cumulé et durée moyenne d'une présence sur le terrain.
"""
from __future__ import annotations
import difflib
import itertools
import math

import analyse
import components as ui
from components import e
from theme import PAPER, INK, RED, MUTED, LINE, SOFT, SERIF, COND

FRANCE = "FRANCE"
DELAI = 10 / 60                       # 10 secondes, en minutes de jeu
TIRS = {"Tir cadré", "Tir contré", "Tir hors cadre", "Poteau", "But"}
GAINS = {"Récupération", "Interception"}
PERTES = {"Perte de balle", "Passe loupée"}
DISTANCES = [("Moins de 6 m", 0, 6), ("6 à 10 m", 6, 10), ("Plus de 10 m", 10, 99)]
COULOIRS = ["Gauche", "Axe", "Droite"]


def _mm(minute) -> str:
    """Minute de jeu affichée comme sur le reste du site : 0,3 -> 1'."""
    return f"{max(1, math.ceil(minute))}'"


def _actions(d):
    return sorted(d.get("actions", []), key=lambda a: (a["mt"], a["min"]))


def _adversaire(d):
    return next((x for x in d.get("equipes", []) if x != FRANCE), None)


# ------------------------------------------------------------------ enchaînements en 10 secondes
def _suivi_de_tir(acts, i, equipe_tir):
    """Vrai si un tir de `equipe_tir` suit l'action i dans les 10 s, même mi-temps."""
    a = acts[i]
    for b in acts[i + 1:]:
        if b["mt"] != a["mt"] or b["min"] - a["min"] > DELAI:
            return False
        if b["e"] == equipe_tir and b["a"] in TIRS:
            return True
    return False


def pressing(d, eq):
    """Ballons gagnés dans le camp adverse par `eq`, et ceux suivis d'un tir de `eq` en 10 s."""
    acts = _actions(d)
    hauts = [i for i, a in enumerate(acts) if a["e"] == eq and a["a"] in GAINS and a["y"] >= 20]
    suivis = [acts[i] for i in hauts if _suivi_de_tir(acts, i, eq)]
    return dict(gains_hauts=len(hauts), suivis=len(suivis), minutes=[_mm(a["min"]) for a in suivis])


def pertes_dangereuses(d, eq):
    """Ballons perdus par `eq`, et ceux suivis d'un tir adverse en 10 s."""
    acts = _actions(d)
    adv = next((x for x in d.get("equipes", []) if x != eq), None)
    pertes = [i for i, a in enumerate(acts) if a["e"] == eq and a["a"] in PERTES]
    dang = [acts[i] for i in pertes if _suivi_de_tir(acts, i, adv)]
    return dict(pertes=len(pertes), dangereuses=len(dang), dans_son_camp=sum(1 for a in dang if a["y"] < 20),
                minutes=[_mm(a["min"]) for a in dang])


# ------------------------------------------------------------------ zones de tir
def _zone(a):
    """(ligne distance, colonne couloir) d'un tir, vu par l'équipe qui tire."""
    dist = math.hypot(a["x"] - 10, 40 - a["y"])
    i = next(k for k, (_, lo, hi) in enumerate(DISTANCES) if lo <= dist < hi)
    j = 0 if a["x"] < 7 else (1 if a["x"] <= 13 else 2)
    return i, j


def zones_tir(donnees, eq):
    """Grille 3 x 3 : [{tirs, buts}] sur un ou plusieurs matchs."""
    g = [[dict(tirs=0, buts=0) for _ in COULOIRS] for _ in DISTANCES]
    for d in donnees:
        for a in d.get("actions", []):
            if a["e"] == eq and a["a"] in TIRS:
                i, j = _zone(a)
                g[i][j]["tirs"] += 1
                g[i][j]["buts"] += a["a"] == "But"
    return g


def zones_svg(g, couleur=INK, mobile=False) -> str:
    """Demi-terrain vu de face (but en haut), 9 zones colorées selon le nombre de tirs."""
    w, h = 300, 260
    mx = max([c["tirs"] for r in g for c in r] + [1])
    # Bandes de distance dessinées du but (haut) vers le milieu (bas) : hauteurs 6 m, 4 m, 10 m sur 20 m
    hauteurs = [6, 4, 10]
    ys = [0]
    for hh in hauteurs:
        ys.append(ys[-1] + hh * h / 20)
    xs = [0, 7 * w / 20, 13 * w / 20, w]
    s = ""
    for i in range(3):
        for j in range(3):
            c = g[i][j]
            op = 0.08 + 0.75 * c["tirs"] / mx if c["tirs"] else 0
            x0, x1, y0, y1 = xs[j], xs[j + 1], ys[i], ys[i + 1]
            s += f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="{couleur}" fill-opacity="{op:.2f}" stroke="#fff" stroke-width="2"/>'
            if c["tirs"]:
                fonce = op > 0.45
                tc = "#fff" if fonce else INK
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 5
                s += (f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" font-family="DM Serif Display, Georgia, serif" font-size="24" fill="{tc}">{c["tirs"]}</text>'
                      f'<text x="{cx:.1f}" y="{cy + 16:.1f}" text-anchor="middle" font-family="Archivo Narrow, Arial, sans-serif" font-size="11" '
                      f'font-weight="700" fill="{tc}">{c["buts"]} BUT{"S" if c["buts"] > 1 else ""}</text>')
    # but, repères de distance (à gauche de chaque bande) et cadre
    s += f'<rect x="{w / 2 - 22:.1f}" y="-6" width="44" height="6" fill="{INK}"/>'
    for i, (lab, _, _) in enumerate(DISTANCES):
        s += (f'<text x="5" y="{ys[i] + 12:.1f}" font-family="Archivo Narrow, Arial, sans-serif" font-size="9" font-weight="700" '
              f'fill="{MUTED}" letter-spacing="0.5">{lab.upper()}</text>')
    s += f'<rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
    svg = (f'<svg width="{w}" height="{h + 8}" viewBox="0 -8 {w} {h + 8}" xmlns="http://www.w3.org/2000/svg">'
           f'<rect x="0" y="0" width="{w}" height="{h}" fill="#EFE8DA"/>{s}</svg>')
    return ui.svg_img(svg, alt="Zones de tir : nombre de tirs et de buts par zone")


def zones_note() -> str:
    return (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 8px; line-height: 1.5">Vue de face, but en haut. '
            f'Chiffre : tirs tentés depuis la zone (buts compris). Plus la case est foncée, plus on y a tiré. Distance mesurée jusqu\'au centre du but.</div>')


# ------------------------------------------------------------------ duos et présences (France)
def _cle(nom, connus):
    """Regroupe les petites différences d'écriture d'un match à l'autre (GUEDDOURA / GUEDDOURRA)."""
    n = analyse.nom_rapport(nom)
    for k in connus:
        if difflib.SequenceMatcher(None, analyse._sa(n), analyse._sa(k)).ratio() >= 0.9:
            return k
    connus.append(n)
    return n


def _gardiens(d):
    g = set(analyse._sa(x) for x in d.get("terrain", {}).get("gardiens", []))
    g |= {analyse._sa(j["nom"]) for j in d.get("compo", {}).get(FRANCE, []) if j.get("gardien")}
    return g


def duos(donnees, connus=None, mini=2):
    """Paires de joueurs de champ français présents ensemble aux buts : [(j1, j2, pour, contre)], meilleurs d'abord."""
    connus = [] if connus is None else connus
    tab = {}
    for d in donnees:
        gb = _gardiens(d)
        for b in d.get("terrain", {}).get("buts", []):
            champ = sorted({_cle(n, connus) for n in b.get("presents", {}).get(FRANCE, []) if analyse._sa(n) not in gb})
            for p in itertools.combinations(champ, 2):
                t = tab.setdefault(p, [0, 0])
                t[0 if b["equipe"] == FRANCE else 1] += 1
    out = [(a, b, p, c) for (a, b), (p, c) in tab.items() if p + c >= mini]
    return sorted(out, key=lambda x: (-(x[2] - x[3]), -x[2], x[0], x[1]))


def presences(donnees, connus=None):
    """Cumul de l'appli temps de jeu : {nom: dict(matchs, total (s), entrees)} pour les joueurs de champ français."""
    connus = [] if connus is None else connus
    out = {}
    for d in donnees:
        tj = d.get("temps_jeu") or {}
        if str(tj.get("equipe", "")).upper() != FRANCE:
            continue
        for j in tj.get("joueurs", []):
            if j.get("gardien") or not j.get("total"):
                continue
            k = _cle(j["nom"], connus)
            t = out.setdefault(k, dict(matchs=0, total=0, entrees=0))
            t["matchs"] += 1
            t["total"] += j["total"]
            t["entrees"] += j.get("entrees") or 0
    return out


def _mmss(s) -> str:
    s = int(round(s))
    return f"{s // 60}:{s % 60:02d}"


# ------------------------------------------------------------------ blocs HTML
def _tuile(n, lab, sous=None, fond=PAPER, coul=INK):
    return (f'<div style="flex: 1; min-width: 130px; background: {fond}; border: 1.5px solid {INK}; border-radius: 10px; padding: 12px 14px">'
            f'<div style="font-family: {SERIF}; font-size: 34px; line-height: 1; color: {coul}">{n}</div>'
            f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 6px">{e(lab)}</div>'
            + (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 4px">{e(sous)}</div>' if sous else "") + '</div>')


def tuiles_enchainements(d_list, eq_fr=FRANCE, adv=None) -> str:
    """Pressing efficace et pertes dangereuses, France puis adversaire (un match) ou France seule (cumul)."""
    def somme(fn, eq, cles):
        t = {k: 0 for k in cles}
        mins = []
        for d in d_list:
            eqd = eq if eq != "ADV" else _adversaire(d)
            if eqd is None:
                continue
            r = fn(d, eqd)
            for k in cles:
                t[k] += r[k]
            mins += r["minutes"]
        return t, mins
    pr, pr_m = somme(pressing, eq_fr, ["gains_hauts", "suivis"])
    pe, pe_m = somme(pertes_dangereuses, eq_fr, ["pertes", "dangereuses", "dans_son_camp"])
    t = [_tuile(pr["suivis"], "Pressing qui finit en tir", f"sur {pr['gains_hauts']} ballons gagnés dans le camp adverse"
                + (f" · {', '.join(pr_m)}" if len(d_list) == 1 and pr_m else ""), coul=ui.BLEU_FR),
         _tuile(pe["dangereuses"], "Pertes punies d'un tir", f"sur {pe['pertes']} ballons perdus, dont {pe['dans_son_camp']} dans son camp"
                + (f" · {', '.join(pe_m)}" if len(d_list) == 1 and pe_m else ""), coul=RED)]
    if adv:
        pa, _ = somme(pressing, "ADV", ["gains_hauts", "suivis"])
        pea, _ = somme(pertes_dangereuses, "ADV", ["pertes", "dangereuses", "dans_son_camp"])
        t += [_tuile(pa["suivis"], f"Pressing {adv}", f"sur {pa['gains_hauts']} ballons gagnés hauts"),
              _tuile(pea["dangereuses"], f"Pertes punies {adv}", f"sur {pea['pertes']} ballons perdus")]
    return f'<div style="display: flex; flex-wrap: wrap; gap: 10px">{"".join(t)}</div>'


def note_enchainements() -> str:
    return (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 8px; line-height: 1.5">Pressing qui finit en tir : ballon récupéré ou intercepté '
            f'dans le camp adverse, puis tir de la même équipe dans les 10 secondes. Perte punie : ballon perdu (perte, passe ratée) '
            f'puis tir adverse dans les 10 secondes.</div>')


def duos_html(liste, n=6) -> str:
    if not liste:
        return f'<div style="font-size: 13px; color: {MUTED}">Pas encore assez de buts pour comparer les duos.</div>'
    lignes = ""
    for a, b, p, c in liste[:n]:
        diff = p - c
        lignes += (f'<div style="display: flex; align-items: center; gap: 10px; padding: 9px 2px; border-bottom: 1px solid {LINE}">'
                   f'<span style="flex: 1; font-weight: 600; min-width: 0">{e(a)} <span style="color: {MUTED}">+</span> {e(b)}</span>'
                   f'<span style="font-family: {COND}; font-size: 13px; color: {MUTED}; white-space: nowrap">{p} pour · {c} contre</span>'
                   f'<span style="font-family: {SERIF}; font-size: 22px; width: 44px; text-align: right; color: {ui.BLEU_FR if diff > 0 else (RED if diff < 0 else INK)}">'
                   f'{diff:+d}</span></div>')
    return lignes + (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 8px; line-height: 1.5">Joueurs de champ présents ensemble sur le terrain '
                     f'au moment des buts. Le duo le plus utile en tête.</div>')


def presences_html(tab, n=12, mobile=False) -> str:
    if not tab:
        return f'<div style="font-size: 13px; color: {MUTED}">Pas encore de temps de jeu relevé.</div>'
    tpl = "grid-template-columns: minmax(0,1fr) 34px 58px 58px" if mobile else "grid-template-columns: minmax(0,1fr) 60px 80px 70px 110px"
    head = (f'<div style="display: grid; {tpl}; gap: 6px; padding: 8px 2px; border-bottom: 2px solid {INK}; font-family: {COND}; font-weight: 700; '
            f'font-size: 11px; letter-spacing: 0.06em; color: {MUTED}"><span>JOUEUR</span><span style="text-align: right">M.</span>'
            f'<span style="text-align: right">TEMPS</span>' + ("" if mobile else '<span style="text-align: right">ENTRÉES</span>')
            + '<span style="text-align: right">PAR PRÉSENCE</span></div>')
    rows = ""
    for nom, t in sorted(tab.items(), key=lambda x: -x[1]["total"])[:n]:
        par = _mmss(t["total"] / t["entrees"]) if t["entrees"] else "-"
        rows += (f'<div style="display: grid; {tpl}; gap: 6px; padding: 8px 2px; border-bottom: 1px solid {LINE}; align-items: center">'
                 f'<span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(nom)}</span>'
                 f'<span style="font-family: {COND}; text-align: right">{t["matchs"]}</span>'
                 f'<span style="font-family: {SERIF}; font-size: 18px; text-align: right">{_mmss(t["total"])}</span>'
                 + ("" if mobile else f'<span style="font-family: {COND}; text-align: right">{t["entrees"]}</span>')
                 + f'<span style="font-family: {COND}; font-weight: 700; text-align: right; color: {ui.BLEU_FR}">{par}</span></div>')
    return head + rows + (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 8px; line-height: 1.5">Joueurs de champ. Par présence : '
                          f'durée moyenne d\'un passage sur le terrain, entre une entrée et la sortie suivante (chrono arrêté).</div>')
