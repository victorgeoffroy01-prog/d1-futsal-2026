"""
Navigation sans rechargement.
Un lien HTML recharge toute l'appli (écran noir d'une seconde). Ici, chaque zone cliquable
est un bloc HTML recouvert d'un st.page_link invisible : Streamlit change de page dans la
même session, l'adresse reste partageable (/joueur?id=...).

Usage dans une page :
    o = Sortie()
    o.add("<html statique>")
    o.lien("<carte>", "joueur", id="bilal-bakkali")
    o.rangee([("J1", "une", {"j": 1}), ...], style="pills")
    o.fin()
"""
from __future__ import annotations
import streamlit as st

PAGES: dict = {}          # rempli par app_mobile.py : nom -> st.Page
_COMPTEUR = [0]           # numérote les zones cliquables, unique sur toute la page


def reset():
    """À appeler au début de chaque exécution du script."""
    _COMPTEUR[0] = 0

CSS_NAV = """
<style>
/* zone cliquable : le lien Streamlit recouvre tout le bloc, invisible */
[class*="st-key-lk-"] { position: relative; }
[class*="st-key-lk-"] > .stElementContainer:has(.stPageLink) {
  position: absolute !important; inset: 0; width: 100% !important; height: 100% !important; z-index: 3; margin: 0 !important; }
[class*="st-key-lk-"] .stPageLink, [class*="st-key-lk-"] .stPageLink > div { width: 100%; height: 100%; }
[class*="st-key-lk-"] a[data-testid="stPageLink-NavLink"] { display: block; width: 100%; height: 100%; opacity: 0;
  padding: 0; margin: 0; border-radius: 0; }
[class*="st-key-lk-"] > .stElementContainer:has(.stHtml) { width: 100% !important; }
/* rangées horizontales */
[class*="st-key-rw-"] { flex-wrap: nowrap !important; align-items: stretch !important; }
[class*="st-key-rw-pills"] { gap: 8px !important; padding: 12px 16px; overflow-x: auto; }
[class*="st-key-rw-tabs"] { gap: 20px !important; padding: 0 16px; border-bottom: 1px solid #D6CDBD; overflow-x: auto; }
[class*="st-key-rw-seg"] { gap: 4px !important; margin: 12px 16px 0; padding: 4px; background: #E9E2D5; border-radius: 10px; }
[class*="st-key-rw-cards"] { gap: 8px !important; }
[class*="st-key-rw-grid"] { gap: 10px !important; padding: 0 16px 10px; }
[class*="st-key-rw-bar"] { gap: 0 !important; align-items: center !important; background: #F4EFE6; border-bottom: 2px solid #111; padding: 14px 16px 12px; }
/* barre de navigation fixe en haut (le bas est masqué par le badge Streamlit) */
.st-key-topnav { position: fixed !important; top: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 480px;
  z-index: 1000; background: #FBF8F2; border-bottom: 2px solid #111; gap: 0 !important; flex-wrap: nowrap !important;
  padding: 0 4px; box-sizing: border-box; }
</style>
"""


class Sortie:
    """Accumule le HTML statique et insère les zones cliquables au bon endroit."""

    def __init__(self):
        self.buf: list[str] = []

    def _cle(self, prefixe):
        _COMPTEUR[0] += 1
        return f"{prefixe}-{_COMPTEUR[0]}"

    def add(self, h: str):
        self.buf.append(h)

    def flush(self):
        if self.buf:
            st.html("".join(self.buf))
            self.buf = []

    def _bloc(self, inner, cible, params, width="stretch"):
        if cible is None:
            with st.container(key=self._cle("st"), width=width):
                st.html(inner)
            return
        with st.container(key=self._cle("lk"), width=width):
            st.html(inner)
            st.page_link(PAGES[cible], label="\u200b", query_params={k: str(v) for k, v in (params or {}).items()})

    def lien(self, inner: str, cible: str, **params):
        self.flush()
        self._bloc(inner, cible, params)

    def rangee(self, items, style="cards", width="stretch", key=None):
        """items = [(html, cible | None, params)] affichés côte à côte."""
        self.flush()
        with st.container(horizontal=True, key=key or self._cle(f"rw-{style}"), gap=None):
            for it in items:
                inner, cible, params = it[:3]
                w = it[3] if len(it) > 3 else width
                self._bloc(inner, cible, params, w)

    def fin(self):
        self.flush()
