"""
Briques visuelles de l'appli (HTML/SVG en Python).
Chaque fonction renvoie une chaîne HTML ; les pages les assemblent puis appellent ui.show().
Les liens internes sont des URL à paramètres (?page=...) : chaque fiche a donc une adresse partageable.
"""
from __future__ import annotations
import base64
import html as _html
from pathlib import Path

import streamlit as st

import config as C
from theme import CR, PAPER, INK, RED, MUTED, LINE, SOFT, SERIF, SANS, COND

e = _html.escape


def svg_img(svg: str, w=None, h=None, alt="") -> str:
    """st.html nettoie les balises <svg> : on les passe en image data-URI."""
    if 'xmlns=' not in svg:
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    src = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    size = (f'width="{w}" ' if w else "") + (f'height="{h}" ' if h else "")
    style = "display: block; max-width: 100%;" + ("" if w else " width: 100%; height: auto;")
    return f'<img src="{src}" {size}alt="{e(alt)}" style="{style}">'


def show(h: str):
    """Affiche un bloc HTML dans la page (sans iframe)."""
    st.html(h)


def fr(x, d=1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


# ------------------------------------------------------------- icônes
ICON = {
    "une": '<path d="M4 5h13v14H6a2 2 0 0 1-2-2z"/><path d="M17 8h3v9a2 2 0 0 1-2 2"/><path d="M7 9h7M7 13h7M7 16h4"/>',
    "match": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5l3.2 2.3-1.2 3.8h-4l-1.2-3.8z"/>',
    "class": '<path d="M5 20V10M12 20V4M19 20v-6"/>',
    "club": '<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z"/>',
    "joueur": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1-4 4-6 7-6s6 2 7 6"/>',
    "back": '<path d="M15 5l-7 7 7 7"/>',
    "chev": '<path d="M9 6l6 6-6 6"/>',
}


def icon(n, s=22, c=INK, sw=1.8):
    return svg_img(f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="{sw}" '
                   f'stroke-linecap="round" stroke-linejoin="round">{ICON[n]}</svg>', s, s)


# ------------------------------------------------------------- images (logos, photos)
@st.cache_data(show_spinner=False)
def _data_uri(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def logo_or_badge(club: str, size=28, fs=10, dark=True) -> str:
    """Logo du club s'il existe dans assets/clubs, sinon pastille avec l'abréviation."""
    src = _data_uri(str(C.ASSETS_DIR / "clubs" / f"{club}.png"))
    if src:
        return f'<img src="{src}" alt="" width="{size}" height="{size}" style="width: {size}px; height: {size}px; object-fit: contain; flex-shrink: 0">'
    bg, fg = (INK, "#fff") if dark else (PAPER, INK)
    return (f'<span style="display: inline-flex; align-items: center; justify-content: center; width: {size}px; height: {size}px; '
            f'flex-shrink: 0; border-radius: 50%; background: {bg}; color: {fg}; border: 1.5px solid {INK}; font-family: {COND}; '
            f'font-weight: 700; font-size: {fs}px">{C.ABREV_CLUBS.get(club, club[:3])}</span>')


def photo(id_joueur: str, w=96, h=116) -> str:
    for ext in ("jpg", "png", "jpeg"):
        src = _data_uri(str(C.ASSETS_DIR / "joueurs" / f"{id_joueur}.{ext}"))
        if src:
            return f'<img src="{src}" alt="" style="width: {w}px; height: {h}px; object-fit: cover; border-radius: 10px; flex-shrink: 0">'
    return (f'<div style="width: {w}px; height: {h}px; flex-shrink: 0; border-radius: 10px; background: {SOFT}; display: flex; '
            f'align-items: flex-end; justify-content: center; overflow: hidden">'
            + svg_img(f'<svg width="{w*0.8:.0f}" height="{h*0.8:.0f}" viewBox="0 0 24 24" fill="{LINE}">'
                      f'<circle cx="12" cy="8" r="4.5"/><path d="M2 24c1-6 5-9 10-9s9 3 10 9z"/></svg>', int(w*0.8), int(h*0.8)) + '</div>')


# ------------------------------------------------------------- blocs texte
def kicker(txt, mt=0, color=RED):
    return (f'<div style="margin-top: {mt}px; display: flex; flex-direction: column; gap: 6px">'
            f'<div style="font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: {color}">{e(txt)}</div>'
            f'<div style="height: 2px; background: {INK}"></div></div>')


def section(inner, pad="22px 16px 0"):
    return f'<section style="padding: {pad}">{inner}</section>'


def tile(num, label, style="paper", numsize=34):
    bg, fg, lc, bd = {
        "paper": (PAPER, INK, MUTED, f"1.5px solid {INK}"),
        "dark": (INK, "#fff", "#E9E2D5", "none"),
        "red": (RED, "#fff", "#fff", "none"),
    }[style]
    return (f'<div style="flex: 1; min-width: 0; background: {bg}; color: {fg}; border: {bd}; border-radius: 10px; padding: 12px 12px 10px; '
            f'display: flex; flex-direction: column; gap: 4px"><div style="font-family: {SERIF}; font-size: {numsize}px; line-height: 1">{num}</div>'
            f'<div style="font-family: {COND}; font-weight: 600; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: {lc}">{label}</div></div>')


def tiles(*t, mt=12):
    return f'<div style="display: flex; gap: 8px; margin-top: {mt}px">{"".join(t)}</div>'


def form_chip(r, s=20):
    base = (f"display: inline-flex; width: {s}px; height: {s}px; align-items: center; justify-content: center; "
            f"font-family: {COND}; font-weight: 700; font-size: 11px; border-radius: 3px; box-sizing: border-box")
    if r == "V":
        return f'<span title="Victoire" style="{base}; background: {INK}; color: #fff">V</span>'
    if r == "D":
        return f'<span title="Défaite" style="{base}; background: {RED}; color: #fff">D</span>'
    return f'<span title="Nul" style="{base}; background: {PAPER}; border: 1.5px solid {INK}; color: {INK}">N</span>'


def empty(msg):
    return (f'<div style="margin-top: 12px; padding: 14px; border: 1.5px dashed {LINE}; border-radius: 10px; '
            f'font-size: 13px; color: {MUTED}">{msg}</div>')


# ------------------------------------------------------------- navigation (contenu des zones cliquables, voir nav.py)
def titre_bar(title, sub=None):
    s = (f'<div style="font-family: {COND}; font-weight: 600; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; '
         f'color: {RED}; margin-top: 4px">{e(sub)}</div>') if sub else ""
    return f'<div style="min-width: 0"><div style="font-family: {SERIF}; font-size: 26px; line-height: 1.05">{e(title)}</div>{s}</div>'


def back_btn():
    return f'<div style="display: flex; width: 40px; height: 44px; align-items: center; margin-left: -8px">{icon("back", 24)}</div>'


def tab_item(lab, on):
    st_ = (f"border-bottom: 3px solid {RED}; color: {INK}; font-weight: 700" if on
           else f"border-bottom: 3px solid transparent; color: {MUTED}; font-weight: 600")
    return (f'<div style="{st_}; padding: 13px 2px 9px; font-family: {COND}; font-size: 14px; letter-spacing: 0.05em; '
            f'text-transform: uppercase; white-space: nowrap">{e(lab)}</div>')


def pill_item(lab, on):
    s = (f"background: {INK}; color: #fff; border: 1.5px solid {INK}" if on else f"background: {PAPER}; color: {INK}; border: 1.5px solid {INK}")
    return (f'<div style="{s}; border-radius: 999px; min-width: 48px; height: 36px; padding: 0 14px; box-sizing: border-box; display: flex; '
            f'align-items: center; justify-content: center; font-family: {COND}; font-weight: 700; font-size: 14px; white-space: nowrap">{e(lab)}</div>')


def seg_item(lab, on):
    return (f'<div style="height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; '
            f'background: {INK if on else "transparent"}; color: {"#fff" if on else INK}; font-family: {COND}; font-weight: 700; font-size: 13px">{e(lab)}</div>')


def nav_item(k, lab, on):
    c = RED if on else INK
    return (f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; height: 54px; '
            f'color: {c}; font-family: {COND}; font-weight: {700 if on else 600}; font-size: 10.5px; letter-spacing: 0.03em; '
            f'text-transform: uppercase; border-bottom: 3px solid {RED if on else "transparent"}; box-sizing: border-box">{icon(k, 20, c)}<span>{lab}</span></div>')


def footer():
    return (f'<div style="padding: 28px 16px 8px; font-size: 11px; color: {MUTED}; line-height: 1.5">'
            f'Données collectées par Victor Geoffroy, non officielles. Crédits : clubs, joueurs, FFF.</div>')


# ------------------------------------------------------------- lignes de listes
BADGE_ANALYSE = (f'<span title="Match analysé : rapport disponible" style="display: inline-block; background: {RED}; color: #fff; border-radius: 3px; '
                 f'padding: 2px 5px; font-family: {COND}; font-weight: 700; font-size: 9px; letter-spacing: 0.06em">ANALYSÉ</span>')


def match_row(m, noms, analyse=False):
    wd, we = m.bd > m.be, m.be > m.bd

    def side(club, s, win):
        return (f'<div style="display: flex; align-items: center; gap: 10px">{logo_or_badge(club, 26, 9)}'
                f'<span style="flex: 1; font-weight: {700 if win else 500}; font-size: 15px">{e(noms[club])}</span>'
                f'<span style="font-family: {SERIF}; font-size: 20px; line-height: 1; color: {INK if win or not (wd or we) else MUTED}">{s}</span></div>')
    return (f'<div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; '
            f'border-bottom: 1px solid {LINE}; background: {PAPER}"><div style="width: 58px; display: flex; flex-direction: column; align-items: flex-start; gap: 5px; font-family: {COND}; font-weight: 700; '
            f'font-size: 11px; color: {MUTED}">TER{BADGE_ANALYSE if analyse else ""}</div><div style="flex: 1; display: flex; flex-direction: column; gap: 8px">'
            f'{side(m.dom, m.bd, wd)}{side(m.ext, m.be, we)}</div>{icon("chev", 18, MUTED)}</div>')


def rank_row(rang, titre, sous, valeur, highlight=False, pad="10px 16px"):
    return (f'<div style="display: grid; grid-template-columns: 22px minmax(0,1fr) 40px; gap: 10px; align-items: center; '
            f'padding: {pad}; border-bottom: 1px solid {LINE}; background: {PAPER}">'
            f'<span style="font-family: {COND}; font-weight: 700; color: {RED if highlight else MUTED}">{rang}</span>'
            f'<span style="min-width: 0"><span style="display: block; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(titre)}</span>'
            f'<span style="display: block; font-size: 12px; color: {MUTED}">{e(sous)}</span></span>'
            f'<span style="font-family: {SERIF}; font-size: 20px; text-align: right">{valeur}</span></div>')


# ------------------------------------------------------------- graphiques SVG
def hbars(items, maxv, label_w=130, bh=14, fs=12):
    """items = [(libellé, valeur, couleur)]"""
    out = ""
    for lab, v, col in items:
        w = 0 if not maxv else max(2, round(100 * v / maxv))
        out += (f'<div style="display: grid; grid-template-columns: {label_w}px minmax(0,1fr); gap: 8px; align-items: center">'
                f'<div style="font-size: {fs}px">{e(lab)}</div><div style="display: flex; align-items: center; gap: 6px">'
                f'<div style="width: calc({w}% - 30px); min-width: 2px; height: {bh}px; background: {col}; border-radius: 2px"></div>'
                f'<div style="font-family: {COND}; font-weight: 700; font-size: {fs+1}px">{v}</div></div></div>')
    return f'<div style="display: flex; flex-direction: column; gap: 10px">{out}</div>'


def mirror(rows, left_label, right_label, unit=20, mid_w=112):
    """Barres face à face : rows = [(libellé, gauche, droite)]."""
    out = (f'<div style="display: flex; justify-content: space-between; font-family: {COND}; font-weight: 700; font-size: 12px; '
           f'letter-spacing: 0.06em; text-transform: uppercase"><span>{e(left_label)}</span><span style="color: {RED}">{e(right_label)}</span></div>')
    out += '<div style="display: flex; flex-direction: column; gap: 10px; margin-top: 8px">'
    mx = max([max(a, b) for _, a, b in rows] + [1])
    for lab, a, b in rows:
        out += (f'<div style="display: grid; grid-template-columns: 24px minmax(0,1fr) {mid_w}px minmax(0,1fr) 24px; align-items: center; gap: 6px">'
                f'<span style="font-family: {SERIF}; font-size: 16px; text-align: right">{a}</span>'
                f'<div style="display: flex; justify-content: flex-end"><div style="height: 12px; width: {100*a/mx:.0f}%; background: {INK}; border-radius: 2px"></div></div>'
                f'<span style="text-align: center; font-size: 12px">{e(lab)}</span>'
                f'<div><div style="height: 12px; width: {100*b/mx:.0f}%; background: {RED}; border-radius: 2px"></div></div>'
                f'<span style="font-family: {SERIF}; font-size: 16px">{b}</span></div>')
    return out + "</div>"


def score_progressif(buts, dom, ext, noms):
    """Courbe en escalier du score sur 40 minutes."""
    W, H, PL, PB = 358, 170, 26, 24
    mx = max(int(buts.score_dom_apres.max() or 0), int(buts.score_ext_apres.max() or 0), 2)
    xs = lambda m: PL + (W - PL - 8) * m / C.DUREE_MATCH
    ys = lambda v: 10 + (H - PB - 10) * (1 - v / mx)

    def path(club):
        d, v = f"M{xs(0):.1f},{ys(0):.1f}", 0
        for r in buts.itertuples():
            if r.club_marque == club:
                v += 1
                d += f" H{xs(r.minute):.1f} V{ys(v):.1f}"
        return d + f" H{xs(C.DUREE_MATCH):.1f}"
    step = 1 if mx <= 6 else 2
    grid = "".join(f'<line x1="{PL}" x2="{W-8}" y1="{ys(v):.1f}" y2="{ys(v):.1f}" stroke="{LINE}"/>'
                   f'<text x="{PL-6}" y="{ys(v)+4:.1f}" font-size="10" text-anchor="end" fill="{MUTED}" font-family="Archivo">{v}</text>'
                   for v in range(0, mx + 1, step))
    xt = "".join(f'<text x="{xs(m):.1f}" y="{H-6}" font-size="10" text-anchor="middle" fill="{MUTED}" font-family="Archivo">{m}\u2019</text>'
                 for m in (0, 10, 20, 30, 40))
    legend = (f'<div style="display: flex; gap: 14px; font-size: 12px; margin-bottom: 4px"><span style="display: inline-flex; align-items: center; gap: 6px">'
              f'<span style="width: 18px; height: 3px; background: {INK}"></span>{e(noms[dom])}</span><span style="display: inline-flex; align-items: center; gap: 6px">'
              f'<span style="width: 18px; height: 3px; background: {RED}"></span>{e(noms[ext])}</span></div>')
    return legend + svg_img(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                     f'<rect x="{xs(20):.1f}" y="10" width="1" height="{H-PB-10}" fill="{INK}"/>{grid}{xt}'
                     f'<path d="{path(dom)}" fill="none" stroke="{INK}" stroke-width="3"/>'
                     f'<path d="{path(ext)}" fill="none" stroke="{RED}" stroke-width="3"/></svg>', alt="Score minute par minute")


def frise(minutes_labels):
    """Frise 40' avec un point par but : [(minute, libellé sous le point)]."""
    W = 358
    dots = ""
    for m, lab in minutes_labels:
        x = 14 + (W - 28) * m / C.DUREE_MATCH
        dots += (f'<circle cx="{x:.1f}" cy="34" r="8" fill="{RED}" stroke="{CR}" stroke-width="2"/>'
                 f'<text x="{x:.1f}" y="60" font-size="10" text-anchor="middle" fill="{INK}" font-family="Archivo" font-weight="700">{e(lab)}</text>')
    return svg_img(f'<svg width="{W}" height="70" viewBox="0 0 {W} 70"><rect x="14" y="31" width="{W-28}" height="6" rx="3" fill="{SOFT}"/>'
            f'<line x1="{W/2}" x2="{W/2}" y1="18" y2="48" stroke="{INK}" stroke-width="1.5"/>'
            f'<text x="{W/2}" y="12" font-size="9" text-anchor="middle" fill="{MUTED}" font-family="Archivo Narrow" letter-spacing="1">MI-TEMPS</text>'
            f'<text x="14" y="12" font-size="9" fill="{MUTED}" font-family="Archivo">0\u2019</text>'
            f'<text x="{W-14}" y="12" font-size="9" text-anchor="end" fill="{MUTED}" font-family="Archivo">40\u2019</text>{dots}</svg>', alt="Minutes des buts")


def tranches_miroir(marques: dict, encaisses: dict):
    mx = max(list(marques.values()) + list(encaisses.values()) + [1])
    out = (f'<div style="display: flex; justify-content: space-between; font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.08em">'
           f'<span>MARQUÉS</span><span style="color: {RED}">ENCAISSÉS</span></div><div style="display: flex; flex-direction: column; gap: 6px; margin-top: 8px">')
    for k in marques:
        a, b = marques[k], encaisses.get(k, 0)
        out += (f'<div style="display: grid; grid-template-columns: minmax(0,1fr) 52px minmax(0,1fr); align-items: center; gap: 6px">'
                f'<div style="display: flex; justify-content: flex-end; align-items: center; gap: 6px"><span style="font-family: {COND}; font-weight: 700; font-size: 12px">{a or ""}</span>'
                f'<div style="height: 14px; width: {80*a/mx:.0f}%; background: {INK}; border-radius: 2px"></div></div>'
                f'<span style="text-align: center; font-family: {COND}; font-size: 11px; color: {MUTED}">{k}\u2019</span>'
                f'<div style="display: flex; align-items: center; gap: 6px"><div style="height: 14px; width: {80*b/mx:.0f}%; background: {RED}; border-radius: 2px"></div>'
                f'<span style="font-family: {COND}; font-weight: 700; font-size: 12px">{b or ""}</span></div></div>')
    return out + "</div>"
