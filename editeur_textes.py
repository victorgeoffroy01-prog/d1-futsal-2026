"""
Validation des textes directement dans la page contrôle, sans passer par Excel.

- Les textes s'éditent et se cochent dans la page. « Enregistrer » écrit textes_journee.xlsx
  dans le dépôt GitHub (secret GITHUB_TOKEN). Sans ce secret, le fichier est proposé en téléchargement.
- Chaque texte est contrôlé : un score, un chiffre ou un nom absent des données du match est signalé.
Rien n'est publié sans la case « Publier » cochée par Victor.
"""
from __future__ import annotations
import base64
import re
import unicodedata
from io import BytesIO

import requests
import streamlit as st

import config as C
import generer_textes as G

DEPOT = "victorgeoffroy01-prog/d1-futsal-2026"
BRANCHE = "main"
ORDINAUX = {1: "1er", 2: "2e", 3: "3e", 4: "4e", 5: "5e", 6: "6e", 7: "7e", 8: "8e", 9: "9e", 10: "10e", 11: "11e", 12: "12e"}


def _secret(nom):
    try:
        return st.secrets[nom]
    except Exception:
        return None


def _sa(t):
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()


# ------------------------------------------------------------------ faits donnés à l'IA
def faits_match(base, m, classement) -> str:
    """Tout ce que l'IA a le droit d'utiliser sur un match, en clair."""
    nom = lambda c: G._nom(base, c)
    rg = classement.set_index("club")
    L = [f"{nom(m.dom)} (domicile) {m.bd}-{m.be} {nom(m.ext)} (extérieur). Mi-temps : {m.mt_d}-{m.mt_e}."]
    for c in (m.dom, m.ext):
        if c in rg.index:
            r = rg.loc[c]
            L.append(f"{nom(c)} : {ORDINAUX.get(int(r.Rg), r.Rg)} au classement après cette journée, {int(r.Pts)} points, "
                     f"{int(r.G)} victoires, {int(r.N)} nuls, {int(r.P)} défaites, série {r.forme}.")
    L.append("Buts dans l'ordre :")
    for b in base.match(m.journee, m.dom).itertuples():
        qui = "contre son camp" if b.est_csc else str(b.buteur)
        passe = f", passe de {b.passeur}" if isinstance(b.passeur, str) else ""
        L.append(f"- {b.minute}{'re' if b.minute == 1 else 'e'} minute, {b.score_dom_apres}-{b.score_ext_apres} : {qui} ({nom(b.club_marque)}){passe}, {b.origine_but}.")
    return "\n".join(L)


# ------------------------------------------------------------------ contrôle d'un texte
def verifier(texte: str, faits: str) -> list[str]:
    """Chiffres et noms du texte absents des faits : à relire avant de publier."""
    f = _sa(faits)
    nombres_faits = set(re.findall(r"\d+", f))
    lettres = {"deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9", "dix": "10"}
    alertes = []
    for sc in re.findall(r"\b\d+\s?[-à]\s?\d+\b", texte):       # un score doit exister tel quel dans les faits
        a, b = re.findall(r"\d+", sc)
        if f"{a}-{b}" not in f and f"{b}-{a}" not in f:
            alertes.append(f"score {sc}")
    for n in re.findall(r"\d+", texte):
        if n not in nombres_faits:
            alertes.append(f"chiffre {n}")
    # noms propres : mots avec majuscule ailleurs qu'en début de phrase
    for mot in re.findall(r"(?<![.!?]\s)(?<!^)\b[A-ZÀ-Ý][\wÀ-ÿ'’-]{2,}", texte):
        if _sa(mot) not in f and _sa(mot) not in ("d1", "une"):
            alertes.append(f"nom « {mot} »")
    # score écrit en lettres, doublé / triplé : rappel de vérification
    for mot, n in lettres.items():
        if re.search(rf"\b{mot}\b", _sa(texte)) and n not in nombres_faits:
            alertes.append(f"« {mot} »")
    return sorted(set(alertes))


# ------------------------------------------------------------------ enregistrement
def enregistrer_github(contenu: bytes, token: str, message: str, depot: str = DEPOT) -> None:
    url = f"https://api.github.com/repos/{depot}/contents/{C.FICHIER_TEXTES.name}"
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    actuel = requests.get(url, headers=h, params={"ref": BRANCHE}, timeout=30)
    corps = {"message": message, "branch": BRANCHE, "content": base64.b64encode(contenu).decode()}
    if actuel.status_code == 200:
        corps["sha"] = actuel.json()["sha"]
    elif actuel.status_code != 404:
        raise RuntimeError(f"GitHub a refusé la lecture ({actuel.status_code}). Vérifie le jeton GITHUB_TOKEN.")
    r = requests.put(url, headers=h, json=corps, timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub a refusé l'enregistrement ({r.status_code}). Vérifie que le jeton a le droit d'écrire dans le dépôt.")


# ------------------------------------------------------------------ interface (page contrôle)
def editeur(base, classement_a) -> None:
    """classement_a(j) -> classement après la journée j."""
    token = _secret("GITHUB_TOKEN")
    j = st.selectbox("Journée", base.journees[::-1], format_func=lambda x: f"J{x}", key="ed-j")
    tout = G.fusionner(G.lire_existant(), G.propositions(base, j))
    lignes = tout[tout.journee == j].sort_values(["type", "cible"], ascending=[False, True])
    cl = classement_a(j)
    faits = {}
    for m in base.matchs[base.matchs.journee == j].itertuples():
        faits[f"match:J{j}:{m.dom}"] = faits_match(base, m, cl)
    top = G.match_une(base, j)
    faits[f"une:J{j}"] = faits.get(f"match:J{j}:{top.dom}", "")

    def cle_txt(c):
        return f"ed-tx-{c}"

    for r in lignes.itertuples():      # valeur de départ : texte validé, sinon proposition
        if cle_txt(r.cible) not in st.session_state:
            st.session_state[cle_txt(r.cible)] = str(r.texte_valide).strip() or str(r.texte_propose).strip()
        if f"ed-ok-{r.cible}" not in st.session_state:
            st.session_state[f"ed-ok-{r.cible}"] = str(r.statut).strip().upper() == "OK"

    for r in lignes.itertuples():
        with st.container(border=True):
            st.markdown(f"**{r.type}** · {r.match}")
            st.text_area("Texte", key=cle_txt(r.cible), height=90 if r.type.startswith("Essentiel") else 68, label_visibility="collapsed")
            txt = st.session_state[cle_txt(r.cible)]
            pb = verifier(txt, faits.get(r.cible, ""))
            if pb:
                st.warning("À vérifier, absent des données du match : " + ", ".join(pb))
            g, d = st.columns([1, 2])
            g.checkbox("Publier", key=f"ed-ok-{r.cible}")
            d.caption(f"{len(txt)} caractères")
            with st.expander("Faits du match"):
                st.text(faits.get(r.cible, ""))

    def fichier() -> bytes:
        df = tout.copy()
        for r in lignes.itertuples():
            i = df.index[df.cible == r.cible][0]
            df.at[i, "texte_valide"] = st.session_state[cle_txt(r.cible)].strip()
            df.at[i, "statut"] = "OK" if st.session_state[f"ed-ok-{r.cible}"] else ""
        buf = BytesIO()
        G.ecrire(df, buf)
        return buf.getvalue()

    n = sum(st.session_state[f"ed-ok-{r.cible}"] for r in lignes.itertuples())
    if token:
        if st.button(f"Enregistrer et publier ({n} texte(s) coché(s))", type="primary", key="ed-save"):
            try:
                contenu = fichier()
                enregistrer_github(contenu, token, f"Textes J{j} validés depuis la page contrôle", _secret("GITHUB_DEPOT") or DEPOT)
                C.FICHIER_TEXTES.write_bytes(contenu)      # visible tout de suite, sans attendre le redéploiement
                st.success("Enregistré. Les textes cochés sont en ligne.")
            except Exception as err:
                st.error(str(err))
    else:
        st.caption("Enregistrement direct non activé (secret GITHUB_TOKEN absent) : télécharge le fichier et dépose-le dans ton dossier.")
        st.download_button("Télécharger textes_journee.xlsx", fichier(), file_name="textes_journee.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
