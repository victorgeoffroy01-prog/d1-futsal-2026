"""
Blocs HTML des nouvelles stats (lots A et C du 12/11/2026), communs au mobile et à l'ordinateur.
Les calculs sont dans contexte.py ; ici, seulement la mise en forme (même DA que le reste du site).
"""
from __future__ import annotations

import components as ui
import config as C
from components import e, fr
from theme import PAPER, INK, RED, MUTED, LINE, SOFT, SERIF, COND


def _pl(n, mot, pluriel=None):
    return f"{n} {mot if n in (0, 1) else (pluriel or mot + 's')}"


def _note(txt, mt=10):
    return f'<div style="font-size: 12px; color: {MUTED}; line-height: 1.5; margin-top: {mt}px">{txt}</div>'


# ================================================================== joueur
def detail_decisifs(liste, noms) -> str:
    """Détail des buts décisifs et passes décisives décisives d'un joueur (liste = contexte.liste_decisifs)."""
    if liste is None or not len(liste):
        return ""
    lignes = ""
    for r in liste.itertuples():
        adv = r.club_ext if r.club_marque == r.club_dom else r.club_dom
        nature = "but de la victoire" if r.dec_victoire else "but du nul"
        qui = "But" if r.role == "but" else f"Passe pour {e(r.buteur)}"
        lignes += (f'<div style="display: grid; grid-template-columns: 34px 44px minmax(0,1fr); gap: 8px; align-items: baseline; padding: 7px 0; border-bottom: 1px solid {LINE}; font-size: 13px">'
                   f'<span style="font-family: {COND}; font-weight: 700">J{r.journee}</span>'
                   f'<span style="font-family: {SERIF}; font-size: 17px; color: {RED}">{r.minute}’</span>'
                   f'<span><b>{qui}</b> contre {e(noms.get(adv, adv))} · {r.score_dom_apres}-{r.score_ext_apres} '
                   f'<span style="color: {MUTED}">({e(noms.get(r.club_dom, r.club_dom))}-{e(noms.get(r.club_ext, r.club_ext))}, {nature})</span></span></div>')
    return f'<div style="margin-top: 14px; border-top: 1px solid {LINE}">{lignes}</div>'


def buts_qui_comptent(s, nb_ouverture: int, mt1: int, mt2: int, numsize=30, liste=None, noms=None) -> str:
    """Tuiles « Buts qui comptent » + répartition selon le score de la fiche joueur (s = ligne de stats_joueurs)."""
    t = lambda v, l, st="paper": ui.tile(v, l, st, numsize)
    total = max(int(s.Mene + s.Egal + s.Devant), 1)
    seg = lambda v, c, fg: (f'<div style="flex: {int(v)} 1 0; min-width: {24 if v else 0}px; background: {c}; color: {fg}; display: {"flex" if v else "none"}; '
                            f'align-items: center; justify-content: center; font-family: {COND}; font-weight: 700; font-size: 12px">{int(v)}</div>')
    barre = (f'<div style="display: flex; height: 24px; border-radius: 4px; overflow: hidden; border: 1.5px solid {INK}; margin-top: 8px">'
             f'{seg(s.Mene, RED, "#fff")}{seg(s.Egal, SOFT, INK)}{seg(s.Devant, INK, "#fff")}</div>'
             f'<div style="display: flex; justify-content: space-between; font-family: {COND}; font-size: 11px; letter-spacing: 0.06em; color: {MUTED}; margin-top: 4px">'
             f'<span>ÉQUIPE MENÉE {round(100 * s.Mene / total)} %</span><span>ÉGALITÉ {round(100 * s.Egal / total)} %</span><span>ÉQUIPE DEVANT {round(100 * s.Devant / total)} %</span></div>')
    details = " · ".join([f"1re / 2e MT : {mt1}/{mt2}", f"minute moyenne : {fr(s.Minute_moy)}’",
                          _pl(int(s.Doubles), "match à 2 buts ou plus", "matchs à 2 buts ou plus")]
                         + ([_pl(int(s.Triples), "triplé")] if s.Triples else []))
    return (ui.kicker("Buts qui comptent", mt=4)
            + ui.tiles(t(int(s.Decisifs), "buts décisifs", "red"), t(int(s.Vainqueurs), "buts vainqueurs", "dark"), t(int(s.Egalisateurs), "égalisateurs"))
            + (f'<div style="font-size: 12px; color: {MUTED}; margin-top: 8px">Buts décisifs : {int(s.Dec_V)} de la victoire, {int(s.Dec_N)} du nul'
               + (f' · {_pl(int(s.PD_dec), "passe décisive", "passes décisives")} sur un but décisif' if s.PD_dec else "") + "</div>")
            + detail_decisifs(liste, noms or {})
            + ui.tiles(t(nb_ouverture, "ouvrent le score"), t(int(s.Avantage), "donnent l’avantage"), t(int(s.Fin_match), "buts 36’-40’"), mt=8)
            + f'<div style="margin-top: 16px; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em">SES BUTS SELON LE SCORE</div>' + barre
            + _note(e(details))
            + _note("But décisif : le dernier but du vainqueur dans un match gagné d’un seul but, ou le dernier but d’un match nul. "
                    "Buts vainqueurs : le but après lequel l’équipe ne sera plus rejointe, quel que soit l’écart final. "
                    "Donnent l’avantage : buts qui font passer de l’égalité à devant, hors 1er but du match.", 6))


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
    return (f'<div style="background: {PAPER}; border: 1.5px solid {INK}; border-radius: 12px; overflow: hidden; margin-top: 12px">'
            f'<div style="padding: 12px 14px; background: {RED}; color: #fff; font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em">'
            f'CUMUL SUR SES {n} MATCHS ANALYSÉS</div>'
            f'<div style="display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1px; background: {LINE}">{"".join(cases)}</div></div>')


# ================================================================== club
# ================================================================== survol (souris) / toucher (téléphone)
# Les graphiques restent des images (st.html n'accepte pas le SVG direct) ; on pose par-dessus des points HTML
# qui affichent une bulle au survol, ou au toucher sur téléphone (tabindex = le point prend le focus).
SURVOL_CSS = f"""<style>
.d1-graph {{ position: relative; }}
.d1-graph img {{ display: block; width: 100%; height: auto; }}
.d1-pt {{ position: absolute; transform: translate(-50%, -50%); outline: none; cursor: pointer; z-index: 2; }}
.d1-pt:hover, .d1-pt:focus {{ z-index: 5; }}
.d1-bulle {{ position: absolute; left: 50%; transform: translateX(-50%); width: max-content; max-width: 220px; background: {INK}; color: #fff;
  font-family: Archivo, Arial, sans-serif; font-size: 12px; line-height: 1.35; padding: 7px 9px; border-radius: 6px; text-align: left;
  opacity: 0; visibility: hidden; transition: opacity .12s; pointer-events: none; box-shadow: 0 4px 12px rgba(0,0,0,.18); }}
.d1-bulle b {{ font-weight: 700; }}
.d1-bulle.haut {{ bottom: calc(100% + 8px); }}
.d1-bulle.bas {{ top: calc(100% + 8px); }}
.d1-bulle.g {{ left: 0; transform: none; }}
.d1-bulle.d {{ left: auto; right: 0; transform: none; }}
.d1-zone {{ position: absolute; top: 0; bottom: 18px; outline: none; cursor: pointer; border-radius: 4px; }}
.d1-zone:hover, .d1-zone:focus {{ background: rgba(17,17,17,.06); z-index: 5; }}
.d1-zone .d1-bulle {{ top: 4px; }}
.d1-ligne {{ position: relative; outline: none; cursor: pointer; }}
.d1-ligne:hover, .d1-ligne:focus {{ z-index: 5; }}
.d1-pt:hover .d1-bulle, .d1-pt:focus .d1-bulle, .d1-zone:hover .d1-bulle, .d1-zone:focus .d1-bulle,
.d1-ligne:hover .d1-bulle, .d1-ligne:focus .d1-bulle {{ opacity: 1; visibility: visible; }}
</style>"""


def _point(x_pct, y_pct, rond, bulle, sens="haut"):
    """Un point survolable : rond = HTML du marqueur, bulle = HTML de la bulle. Près des bords, la bulle s'aligne pour ne pas sortir."""
    cote = " g" if x_pct < 18 else (" d" if x_pct > 82 else "")
    return (f'<div class="d1-pt" tabindex="0" style="left: {x_pct:.2f}%; top: {y_pct:.2f}%">{rond}'
            f'<div class="d1-bulle {sens}{cote}">{bulle}</div></div>')


def courbe_rangs(points, nb_clubs: int, w=420, h=170, playoffs=4, descente=2, details=None) -> str:
    """Évolution au classement journée par journée (1er en haut). points = [(journee, rang, points)].
    Survol d'un point : journée, rang, points et résultat du match (details = {journee: texte})."""
    if len(points) < 2:
        return ""
    details = details or {}
    pg, pd_, ph, pb = 34, 14, 14, 26
    xs = lambda i: pg + i * (w - pg - pd_) / (len(points) - 1)
    ys = lambda r: ph + (r - 1) * (h - ph - pb) / max(nb_clubs - 1, 1)
    zone = (f'<rect x="{pg}" y="{ph - 6}" width="{w - pg - pd_}" height="{ys(playoffs) - ph + 6 + 6}" fill="{RED}" opacity="0.08"/>'
            f'<rect x="{pg}" y="{ys(nb_clubs - descente + 1) - 6}" width="{w - pg - pd_}" height="{h - pb - ys(nb_clubs - descente + 1) + 12}" fill="{INK}" opacity="0.07"/>')
    grille = "".join(f'<text x="{pg - 8}" y="{ys(r) + 4}" text-anchor="end" font-family="Archivo Narrow, Arial" font-size="11" fill="{MUTED}">{r}e</text>'
                     for r in (1, playoffs, nb_clubs))
    axe = "".join(f'<text x="{xs(i)}" y="{h - 6}" text-anchor="middle" font-family="Archivo Narrow, Arial" font-size="11" fill="{MUTED}">J{p[0]}</text>'
                  for i, p in enumerate(points))
    ligne = " ".join(f"{xs(i):.1f},{ys(p[1]):.1f}" for i, p in enumerate(points))
    fin = points[-1][1]
    lab = f'<text x="{xs(len(points) - 1) - 9:.1f}" y="{ys(fin) + (16 if fin < 3 else -9):.1f}" text-anchor="end" font-family="DM Serif Display, Georgia" font-size="15" fill="{RED}">{fin}e</text>'
    svg = (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
           f'{zone}{grille}{axe}<polyline points="{ligne}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>{lab}</svg>')
    pts = ""
    for i, p in enumerate(points):
        j, r = p[0], p[1]
        dernier = i == len(points) - 1
        rond = (f'<div style="width: {12 if dernier else 10}px; height: {12 if dernier else 10}px; border-radius: 50%; background: {RED if dernier else INK}; '
                f'border: 2px solid {PAPER}; box-sizing: content-box"></div>')
        bulle = (f'<b>J{j} · {r}e</b>' + (f' · {p[2]} pts' if len(p) > 2 else "")
                 + (f'<br>{e(details[j])}' if j in details else ""))
        pts += _point(100 * xs(i) / w, 100 * ys(r) / h, rond, bulle, "haut" if r > 3 else "bas")
    return (SURVOL_CSS + f'<div class="d1-graph">{ui.svg_img(svg, alt="Évolution au classement journée par journée")}{pts}</div>'
            + _note(f'Zone rouge : top {playoffs}, play-offs. Zone grise : les {descente} places de descente. Survolez ou touchez un point pour le détail.', 4))


def fil_du_match(buts, dom, ext, noms, orig=None, W=720, H=210, cols=None) -> str:
    """Fil du match : buts du domicile au-dessus de la ligne du temps, de l'extérieur en dessous,
    bande centrale = écart au score (noir quand le domicile mène, rouge quand l'extérieur mène).
    Survol / toucher d'un but : buteur, passeur, score, origine."""
    orig = orig or {}
    (fd, bd), (fe, be) = cols or ((INK, PAPER), (RED, PAPER))
    # couleur d'une équipe sur fond crème : son fond, ou son bord si le fond est trop clair (blanc)
    vis = lambda f, b_: b_ if ui.proches(f, PAPER) else f
    cd_, ce_ = vis(fd, bd), vis(fe, be)
    b = buts.assign(_t=buts.score_dom_apres + buts.score_ext_apres).sort_values(["periode", "minute", "_t"])
    PL, PR = 14, 14
    axe = H / 2
    xs = lambda m: PL + (W - PL - PR) * m / C.DUREE_MATCH
    # bande de l'écart : hauteur proportionnelle à l'écart, plafonnée
    ecarts = (b.score_dom_apres - b.score_ext_apres).tolist()
    k = min(14.0, (H * 0.22) / max([abs(x) for x in ecarts] + [1]))
    seg, t0, ec = [], 0.0, 0
    for r, e2 in zip(b.itertuples(), ecarts):
        t = r.minute - 0.5
        seg.append((t0, t, ec)); t0, ec = t, e2
    seg.append((t0, C.DUREE_MATCH, ec))
    bande = ""
    for a, z, v in seg:
        if v and z > a:
            y, hh = (axe - v * k, v * k) if v > 0 else (axe, -v * k)
            bande += f'<rect x="{xs(a):.1f}" y="{y:.1f}" width="{xs(z) - xs(a):.1f}" height="{hh:.1f}" fill="{cd_ if v > 0 else ce_}" opacity="0.18"/>'
    mi = xs(C.DUREE_MATCH / 2)
    graduations = "".join(f'<line x1="{xs(m):.1f}" x2="{xs(m):.1f}" y1="{axe - 4}" y2="{axe + 4}" stroke="{MUTED}"/>'
                          f'<text x="{xs(m):.1f}" y="{axe + 18}" text-anchor="middle" font-family="Archivo, Arial" font-size="10" fill="{MUTED}">{m}’</text>'
                          for m in (0, 5, 10, 15, 25, 30, 35, 40))
    svg = (f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">{bande}'
           f'<line x1="{xs(0)}" x2="{xs(C.DUREE_MATCH)}" y1="{axe}" y2="{axe}" stroke="{INK}" stroke-width="1.5"/>{graduations}'
           f'<line x1="{mi:.1f}" x2="{mi:.1f}" y1="8" y2="{H - 8}" stroke="{INK}" stroke-dasharray="3 3"/>'
           f'<text x="{mi + 5:.1f}" y="16" font-family="Archivo Narrow, Arial" font-size="10" fill="{MUTED}" letter-spacing="1">MI-TEMPS</text></svg>')
    # marqueurs : décalés vers l'extérieur quand deux buts du même camp sont trop proches
    pts, etages = "", {dom: {}, ext: {}}       # par camp : {étage: [x des buts déjà placés]}
    for r in b.itertuples():
        haut = r.club_marque == dom
        x = xs(r.minute)
        etage = 0                                 # premier étage sans but trop proche (34 unités = largeur d'un marqueur + marge)
        while any(abs(xp - x) < 34 for xp in etages[r.club_marque].get(etage, [])):
            etage += 1
        etages[r.club_marque].setdefault(etage, []).append(x)
        y = axe - 46 - 30 * etage if haut else axe + 46 + 30 * etage
        y = max(14, min(H - 14, y))
        csc = bool(r.est_csc)
        fond, bord = (fd, bd) if haut else (fe, be)
        texte = ui.texte_sur(fond)
        trait = vis(fond, bord)
        rond = (f'<div style="min-width: 30px; height: 26px; padding: 0 4px; box-sizing: border-box; border-radius: 13px; display: flex; align-items: center; '
                f'justify-content: center; font-family: Archivo Narrow, Arial, sans-serif; font-weight: 700; font-size: 12px; '
                + (f'background: {PAPER}; color: {trait}; border: 2px dashed {trait}' if csc else f'background: {fond}; color: {texte}; border: 2px solid {bord}')
                + f'">{r.minute}’</div>')
        tige = f'<div style="position: absolute; left: 50%; width: 1px; background: {trait}; opacity: .5; {"top: 100%" if haut else "bottom: 100%"}; height: {abs(y - axe) - 13:.0f}px"></div>'
        bulle = (f'<b>{r.minute}’ · {e(noms[r.club_marque])} {r.score_dom_apres}-{r.score_ext_apres}</b><br>'
                 + ("But contre son camp" if csc else f'{e(r.buteur or "")}' + (f'<br>Passe : {e(r.passeur)}' if r.passeur and r.passeur == r.passeur else ""))
                 + (f'<br><span style="color: #D9D2C6">{e(orig.get(r.origine_but, r.origine_but))}</span>' if r.origine_but and r.origine_but == r.origine_but else ""))
        pts += _point(100 * x / W, 100 * y / H, f'<div style="position: relative">{tige}{rond}</div>', bulle, "haut" if haut else "bas")
    legende = (f'<div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px">'
               f'<span style="display: inline-flex; align-items: center; gap: 6px">{ui.pastille_club((fd, bd))}{e(noms[dom])} (dom.)</span>'
               f'<span style="display: inline-flex; align-items: center; gap: 6px">{ui.pastille_club((fe, be))}{e(noms[ext])} (ext.)</span></div>')
    return (SURVOL_CSS + legende + f'<div class="d1-graph">{ui.svg_img(svg, alt="Fil du match")}{pts}</div>'
            + _note("Bande au-dessus de la ligne : le domicile mène, en dessous : l'extérieur mène (plus elle est haute, plus l'écart est grand), aux couleurs de chaque club. Pointillés : but contre son camp. "
                    "Survolez ou touchez un but pour le détail.", 6))


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
    return (f'<div style="display: flex; height: 26px; border-radius: 4px; overflow: hidden; border: 1.5px solid {INK}">'
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
    "Buts décisifs : dans un match gagné d’un seul but, le dernier but du vainqueur (but de la victoire) ; dans un match nul, le dernier but du match (but du nul). "
    "Les passes décisives décisives sont les passes saisies sur ces buts.",
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
    return (f'<div style="padding: {pad}"><div style="background: {PAPER}; border: 1.5px solid {INK}; border-radius: 10px; padding: 10px 12px">'
            f'<div style="font-family: {COND}; font-weight: 700; font-size: 11px; letter-spacing: 0.1em; color: {MUTED}; margin-bottom: 6px">SÉRIES EN COURS</div>'
            f'<div style="display: flex; flex-direction: column; gap: 6px">{items}</div></div></div>')


# ================================================================== survols : barres par tranche, pastilles de forme, frise du joueur
def zones_barres(img_html, W, x0, bw, bulles) -> str:
    """Pose une zone survolable sur chaque barre (ou groupe de barres) d'un graphique image.
    x0 = début de la 1re zone, bw = largeur d'une zone (unités du SVG, W = largeur du SVG)."""
    n = len(bulles)
    z = "".join(f'<div class="d1-zone" tabindex="0" style="left: {100 * (x0 + i * bw) / W:.2f}%; width: {100 * bw / W:.2f}%">'
                f'<div class="d1-bulle bas{" g" if i < 2 else (" d" if i > n - 3 else "")}">{b}</div></div>' for i, b in enumerate(bulles))
    return SURVOL_CSS + f'<div class="d1-graph">{img_html}{z}</div>'


def _tranche(m):
    a = (int(m) - 1) // 5 * 5
    return f"{a + 1}-{a + 5}"


def bulles_tranches(b, orig, club=None, noms=None) -> list:
    """Texte de la bulle de chaque tranche de 5 min. club=None : toute la D1 ; sinon marqués / encaissés du club."""
    out = []
    t = b.assign(_tr=b.minute.map(_tranche))
    total = max(len(t), 1)
    for a in C.TRANCHES[:-1]:
        k = f"{a + 1}-{a + 5}"
        g = t[t._tr == k]
        if club is None:
            org = g.origine_but.value_counts().head(2)
            txt = f"<b>{k}’ : {len(g)} buts</b> ({round(100 * len(g) / total)} % du total)"
            if len(org):
                txt += "<br>" + " · ".join(f"{e(orig.get(o, o))} : {n}" for o, n in org.items())
        else:
            mq, enc = g[g.club_marque == club], g[g.club_encaisse == club]
            txt = f"<b>{k}’</b> : {len(mq)} marqué{'s' if len(mq) > 1 else ''}, {len(enc)} encaissé{'s' if len(enc) > 1 else ''}"
            buteurs = mq[mq.buteur.notna()].groupby("buteur").size().sort_values(ascending=False).head(3)
            if len(buteurs):
                txt += "<br>" + ", ".join(f"{e(n)}{' x' + str(v) if v > 1 else ''}" for n, v in buteurs.items())
        out.append(txt)
    return out


def forme_survol(forme: str, details: dict, s=20) -> str:
    """Pastilles V/N/D avec, au survol ou au toucher, le match correspondant. details = contexte.matchs_du_club(...)."""
    js = sorted(details)[-len(forme):] if forme else []
    out = []
    for i, (x, j) in enumerate(zip(forme, js)):
        cote = " g" if i == 0 else (" d" if i == len(forme) - 1 else "")
        out.append(f'<span class="d1-ligne" tabindex="0" style="display: inline-flex">{ui.form_chip(x, s)}'
                   f'<span class="d1-bulle bas{cote}"><b>J{j}</b> · {e(details[j])}</span></span>')
    return SURVOL_CSS + "".join(out)


def frise_buts(bj, noms, orig, W=358) -> str:
    """Frise 0-40' des buts d'un joueur ; survol / toucher d'un but : journée, adversaire, score, passeur, origine.
    Deux buts trop proches s'étagent vers le bas (la hauteur s'adapte)."""
    b = bj.sort_values(["minute", "journee"])
    xs = lambda m: 14 + (W - 28) * m / C.DUREE_MATCH
    axe = 30
    places, etages = [], {}
    for r in b.itertuples():
        x = xs(r.minute)
        et = 0
        while any(abs(xp - x) < 22 for xp in etages.get(et, [])):
            et += 1
        etages.setdefault(et, []).append(x)
        places.append((r, x, et))
    H = axe + 26 * len(etages) + 18
    svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
           f'<rect x="14" y="{axe - 3}" width="{W - 28}" height="6" rx="3" fill="{SOFT}"/>'
           f'<line x1="{W / 2}" x2="{W / 2}" y1="{axe - 14}" y2="{axe + 14}" stroke="{INK}" stroke-width="1.5"/>'
           f'<text x="{W / 2}" y="10" font-size="9" text-anchor="middle" fill="{MUTED}" font-family="Archivo Narrow, Arial" letter-spacing="1">MI-TEMPS</text>'
           f'<text x="14" y="10" font-size="9" fill="{MUTED}" font-family="Archivo, Arial">0’</text>'
           f'<text x="{W - 14}" y="10" font-size="9" text-anchor="end" fill="{MUTED}" font-family="Archivo, Arial">40’</text></svg>')
    pts = ""
    for r, x, et in places:
        y = axe + 26 * et
        adv = r.club_ext if r.club_marque == r.club_dom else r.club_dom
        rond = (f'<div style="display: flex; flex-direction: column; align-items: center; gap: 1px; padding-top: 12px">'
                f'<div style="width: 14px; height: 14px; border-radius: 50%; background: {RED}; border: 2px solid {PAPER}"></div>'
                f'<div style="font-family: Archivo Narrow, Arial, sans-serif; font-weight: 700; font-size: 10px; line-height: 1">{r.minute}’</div></div>')
        bulle = (f'<b>J{r.journee} · {r.minute}’ contre {e(noms.get(adv, adv))}</b><br>'
                 f'{e(noms.get(r.club_dom, r.club_dom))} {r.score_dom_apres}-{r.score_ext_apres} {e(noms.get(r.club_ext, r.club_ext))}'
                 + (f'<br>Passe : {e(r.passeur)}' if isinstance(r.passeur, str) and r.passeur else "")
                 + (f'<br><span style="color: #D9D2C6">{e(orig.get(r.origine_but, r.origine_but))}</span>' if isinstance(r.origine_but, str) else ""))
        pts += _point(100 * x / W, 100 * (y + 6) / H, rond, bulle, "haut" if et == 0 else "bas")
    return (SURVOL_CSS + f'<div class="d1-graph">{ui.svg_img(svg, alt="Minutes de ses buts")}{pts}</div>'
            + _note("Survolez ou touchez un but pour le détail.", 4))
