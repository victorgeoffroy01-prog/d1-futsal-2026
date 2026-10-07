"""
Champ de recherche joueur : liste déroulante de suggestions pendant la frappe + bouton loupe.

Usage :
    q = recherche.champ([(nom affiché, club affiché, texte cherché), ...], key="rech-stats")
    if q:
        d = d[[recherche.correspond(q, t) for t in d.texte]]

La recherche ignore les majuscules, les accents et les tirets (RIAÑO = riano, EL-FENNI = el fenni).
Le texte n'est validé qu'au clic sur la loupe, sur Entrée ou au choix d'une suggestion.
Composant Streamlit natif (st.components.v2) : aucune dépendance en plus.
"""
from __future__ import annotations
import re
import unicodedata

import streamlit as st

from theme import PAPER, INK, RED, MUTED, LINE, SOFT, SANS, COND

NB_SUGGESTIONS = 8


def norm(t) -> str:
    """Minuscules, sans accents, tout ce qui n'est pas lettre ou chiffre devient un espace."""
    t = unicodedata.normalize("NFD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def correspond(q: str, texte) -> bool:
    """Vrai si le texte contient ce qui est tapé, ou si chaque mot tapé commence un mot du texte
    (« bakkali bilal » trouve Bilal Bakkali). Même règle que les suggestions."""
    cle, tape = norm(texte), norm(q)
    if not tape:
        return False
    return tape in cle or all((" " + m) in (" " + cle) for m in tape.split())


_HTML = """
<div class="rech">
  <div class="lab"></div>
  <div class="boite">
    <input type="text" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="Rechercher un joueur">
    <button class="vider" type="button" aria-label="Effacer la recherche" hidden>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    <button class="loupe" type="button" aria-label="Lancer la recherche">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/></svg>
    </button>
    <div class="liste" role="listbox" hidden></div>
  </div>
</div>
"""

_CSS = f"""
.rech {{ font-family: {SANS}; color: {INK}; }}
.lab {{ font-family: {COND}; font-weight: 700; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: {MUTED}; margin-bottom: 6px; }}
.lab:empty {{ display: none; }}
.boite {{ position: relative; }}
input {{ box-sizing: border-box; width: 100%; height: 44px; padding: 0 84px 0 16px; background: {PAPER}; color: {INK};
  border: 1.5px solid {INK}; border-radius: 22px; font-family: {SANS}; font-size: 15px; outline: none; -webkit-appearance: none; }}
input::placeholder {{ color: {MUTED}; opacity: 1; }}
input:focus {{ box-shadow: 0 0 0 2px {RED}; }}
button {{ position: absolute; top: 4px; border: 0; padding: 0; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
button[hidden] {{ display: none; }}
.loupe {{ right: 4px; width: 36px; height: 36px; border-radius: 50%; background: {INK}; color: #fff; }}
.loupe:hover, .loupe:focus-visible {{ background: {RED}; outline: none; }}
.vider {{ right: 46px; top: 8px; width: 28px; height: 28px; border-radius: 50%; background: transparent; color: {MUTED}; }}
.vider:hover, .vider:focus-visible {{ background: {SOFT}; color: {INK}; outline: none; }}
.liste {{ position: absolute; left: 0; right: 0; top: 50px; z-index: 50; background: {PAPER}; border: 1.5px solid {INK}; border-radius: 12px;
  overflow: hidden; box-shadow: 0 8px 20px rgba(17, 17, 17, 0.18); }}
.liste[hidden] {{ display: none; }}
.item {{ display: flex; align-items: baseline; gap: 10px; padding: 10px 14px; cursor: pointer; border-bottom: 1px solid {LINE}; }}
.item:last-child {{ border-bottom: 0; }}
.item.on, .item:hover {{ background: {SOFT}; }}
.item .n {{ font-weight: 600; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.item .c {{ margin-left: auto; font-family: {COND}; font-size: 12px; color: {MUTED}; white-space: nowrap; }}
.vide {{ padding: 10px 14px; font-size: 13px; color: {MUTED}; }}
"""

_JS = """
const norm = (t) => String(t).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
  .replace(/[^a-z0-9]+/g, ' ').trim();

export default function (component) {
  const { parentElement, data, setStateValue } = component;
  const root = parentElement.querySelector('.rech');
  const input = root.querySelector('input');
  const liste = root.querySelector('.liste');
  const vider = root.querySelector('.vider');
  const joueurs = data.joueurs || [];
  const max = data.max || 8;
  let actif = -1;
  let visibles = [];

  root.querySelector('.lab').textContent = data.label || '';
  input.placeholder = data.ph || '';
  if (!root.dataset.pret) {            // premier affichage : on remet le texte déjà validé
    root.dataset.pret = '1';
    input.value = data.q || '';
  }
  vider.hidden = !input.value;

  const fermer = () => { liste.hidden = true; actif = -1; };

  const valider = (texte) => {
    input.value = texte;
    vider.hidden = !texte;
    fermer();
    setStateValue('q', texte.trim());
  };

  const dessiner = () => {
    liste.replaceChildren();
    visibles.forEach((j, i) => {
      const d = document.createElement('div');
      d.className = 'item' + (i === actif ? ' on' : '');
      d.setAttribute('role', 'option');
      const n = document.createElement('span'); n.className = 'n'; n.textContent = j.n;
      const c = document.createElement('span'); c.className = 'c'; c.textContent = j.c;
      d.append(n, c);
      d.onmousedown = (ev) => { ev.preventDefault(); valider(j.n); };
      liste.append(d);
    });
    if (!visibles.length) {
      const v = document.createElement('div'); v.className = 'vide'; v.textContent = 'Aucun joueur trouvé';
      liste.append(v);
    }
    liste.hidden = false;
  };

  const proposer = () => {
    const mots = norm(input.value).split(' ').filter(Boolean);
    vider.hidden = !input.value;
    actif = -1;
    if (!mots.length) { visibles = []; fermer(); return; }
    const tape = mots.join(' ');
    const ok = joueurs.filter((j) => j.k.includes(tape) || mots.every((m) => (' ' + j.k).includes(' ' + m)));
    // d'abord les noms dont un mot commence par ce qui est tapé
    const debut = (j) => (' ' + j.k).includes(' ' + mots[0]) ? 0 : 1;
    visibles = ok.map((j, i) => [debut(j), i, j]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).slice(0, max).map((x) => x[2]);
    dessiner();
  };

  input.oninput = proposer;
  input.onfocus = () => { if (input.value && liste.hidden) proposer(); };
  input.onblur = fermer;
  input.onkeydown = (ev) => {
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      if (liste.hidden || !visibles.length) return;
      ev.preventDefault();
      const n = visibles.length;
      actif = ev.key === 'ArrowDown' ? (actif + 1) % n : (actif - 1 + n) % n;
      dessiner();
    } else if (ev.key === 'Enter') {
      ev.preventDefault();
      valider(actif >= 0 && visibles[actif] ? visibles[actif].n : input.value);
    } else if (ev.key === 'Escape') {
      fermer();
    }
  };
  root.querySelector('.loupe').onclick = () => valider(input.value);
  vider.onmousedown = (ev) => ev.preventDefault();
  vider.onclick = () => { valider(''); input.focus(); };
}
"""

_COMPOSANT = st.components.v2.component("recherche_joueur", html=_HTML, css=_CSS, js=_JS)


def champ(joueurs, key: str, label: str | None = None, placeholder: str = "Nom, prénom ou surnom…") -> str:
    """joueurs = [(nom affiché, club affiché, texte cherché)], du plus décisif au moins décisif.
    Renvoie le texte validé (loupe, Entrée ou suggestion), '' sinon."""
    etat = st.session_state.get(key)
    try:
        actuel = (etat or {}).get("q") or ""
    except AttributeError:
        actuel = ""
    donnees = {"joueurs": [{"n": str(n), "c": str(c), "k": norm(t)} for n, c, t in joueurs],
               "label": label or "", "ph": placeholder, "q": actuel, "max": NB_SUGGESTIONS}
    res = _COMPOSANT(key=key, data=donnees, default={"q": ""}, on_q_change=lambda: None)
    return str(res.q or "").strip()
