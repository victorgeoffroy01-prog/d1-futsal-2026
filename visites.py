"""
Compteur de visites du site (demande de Victor du 18/11/2026). Gratuit, sans service extérieur hors GitHub.

- Chaque page vue est notée en mémoire : date et heure (Paris), page, fiche (id du club, du joueur, du match),
  appareil (mobile / ordi) et un identifiant de visiteur ANONYME : empreinte de l'adresse IP + navigateur + jour,
  brouillée avec un sel secret (impossible de retrouver l'IP ; change chaque jour, donc pas de suivi d'une personne).
- Les visites de Victor ne sont pas comptées : ouvrir la page contrôle avec la clé pose un cookie « d1_moi » sur l'appareil.
- Les robots (réveil automatique, moteurs de recherche) ne sont pas comptés.
- Toutes les 5 minutes (ou dès 30 visites), les lignes sont ajoutées au fichier stats/visites-AAAA-MM.csv
  de la branche « stats » du dépôt GitHub (pas la branche main : le site ne redémarre pas).
  Clé nécessaire dans les Secrets Streamlit : GITHUB_STATS_TOKEN (jeton GitHub avec droit d'écriture « Contents » sur le dépôt).
  Sans clé, les visites restent en mémoire et sont perdues au redémarrage (la page contrôle le signale).
"""
from __future__ import annotations

import base64
import hashlib
import io
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

DEPOT = "victorgeoffroy01-prog/d1-futsal-2026"
BRANCHE = "stats"
COOKIE_MOI = "d1_moi"
ENVOI_SECONDES = 300
ENVOI_LIGNES = 30
COLONNES = ["date", "heure", "visiteur", "page", "fiche", "appareil"]
ROBOTS = ("headless", "bot", "crawl", "spider", "slurp", "preview", "python-requests", "curl", "wget", "playwright", "lighthouse")
PARIS = ZoneInfo("Europe/Paris")
API = "https://api.github.com"


def _secret(nom):
    try:
        return st.secrets.get(nom)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _memoire():
    """Tampon partagé par tous les visiteurs (un seul serveur) : lignes pas encore envoyées à GitHub."""
    return {"lignes": [], "dernier_envoi": time.time(), "verrou": threading.Lock(), "erreur": None, "envoyees": 0}


def est_moi() -> bool:
    try:
        return st.context.cookies.get(COOKIE_MOI) == "1"
    except Exception:
        return False


def _visiteur(jour: str) -> str:
    h = st.context.headers
    ip = (h.get("X-Forwarded-For") or "").split(",")[0].strip() or (st.context.ip_address or "")
    sel = _secret("CLE_ADMIN") or "d1"
    return hashlib.sha256(f"{sel}|{jour}|{ip}|{h.get('User-Agent', '')}".encode()).hexdigest()[:12]


def noter(page: str, params: dict, ordi: bool) -> None:
    """Note une page vue (une seule fois par page et par fiche dans une même session de navigation)."""
    try:
        ua = (st.context.headers.get("User-Agent") or "").lower()
        if not ua or any(r in ua for r in ROBOTS) or est_moi():
            return
        fiche = str(params.get("id") or (f"J{params.get('j')}-{params.get('dom')}" if params.get("dom") else params.get("j") or ""))
        cle = (page, fiche)
        if st.session_state.get("_derniere_vue") == cle:       # simple rechargement de la même page (filtre, onglet)
            return
        st.session_state["_derniere_vue"] = cle
        maintenant = datetime.now(PARIS)
        jour = maintenant.strftime("%Y-%m-%d")
        ligne = [jour, maintenant.strftime("%H:%M"), _visiteur(jour), page, fiche, "ordi" if ordi else "mobile"]
        m = _memoire()
        with m["verrou"]:
            m["lignes"].append(ligne)
            pret = len(m["lignes"]) >= ENVOI_LIGNES or time.time() - m["dernier_envoi"] >= ENVOI_SECONDES
        if pret:
            threading.Thread(target=envoyer, daemon=True).start()   # en arrière-plan : la page n'attend pas
    except Exception:
        pass                                                         # le compteur ne doit jamais casser le site


# ------------------------------------------------------------------ GitHub (branche « stats »)
def _entetes(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def _creer_branche(token):
    r = requests.get(f"{API}/repos/{DEPOT}/git/ref/heads/{BRANCHE}", headers=_entetes(token), timeout=15)
    if r.status_code == 200:
        return
    sha = requests.get(f"{API}/repos/{DEPOT}/git/ref/heads/main", headers=_entetes(token), timeout=15).json()["object"]["sha"]
    requests.post(f"{API}/repos/{DEPOT}/git/refs", headers=_entetes(token), json={"ref": f"refs/heads/{BRANCHE}", "sha": sha}, timeout=15).raise_for_status()


def _chemin(mois):
    return f"stats/visites-{mois}.csv"


def envoyer() -> None:
    """Ajoute les lignes en attente au fichier du mois sur GitHub. En cas d'échec, les lignes restent en mémoire."""
    m = _memoire()
    token = _secret("GITHUB_STATS_TOKEN")
    if not token:
        m["erreur"] = "Pas de clé GITHUB_STATS_TOKEN : visites gardées en mémoire seulement."
        return
    with m["verrou"]:
        lignes, m["lignes"] = m["lignes"], []
        m["dernier_envoi"] = time.time()
    if not lignes:
        return
    try:
        _creer_branche(token)
        par_mois = {}
        for l in lignes:
            par_mois.setdefault(l[0][:7], []).append(l)
        for mois, ls in par_mois.items():
            url = f"{API}/repos/{DEPOT}/contents/{_chemin(mois)}"
            for essai in range(3):                                   # conflit possible si deux envois se croisent
                r = requests.get(url, headers=_entetes(token), params={"ref": BRANCHE}, timeout=15)
                ancien, sha = ("", None) if r.status_code == 404 else (base64.b64decode(r.json()["content"]).decode(), r.json()["sha"])
                if not ancien:
                    ancien = ",".join(COLONNES) + "\n"
                nouveau = ancien + "".join(",".join(x) + "\n" for x in ls)
                corps = {"message": f"visites {mois} (+{len(ls)})", "branch": BRANCHE,
                         "content": base64.b64encode(nouveau.encode()).decode()}
                if sha:
                    corps["sha"] = sha
                p = requests.put(url, headers=_entetes(token), json=corps, timeout=20)
                if p.status_code in (200, 201):
                    break
                if p.status_code != 409 or essai == 2:
                    p.raise_for_status()
        m["envoyees"] += len(lignes)
        m["erreur"] = None
    except Exception as ex:
        with m["verrou"]:
            m["lignes"] = lignes + m["lignes"]                       # on réessaiera au prochain envoi
        m["erreur"] = f"Envoi à GitHub impossible : {str(ex)[:160]}"


@st.cache_data(ttl=60, show_spinner=False)
def _lire_github(token: str) -> pd.DataFrame:
    r = requests.get(f"{API}/repos/{DEPOT}/contents/stats", headers=_entetes(token), params={"ref": BRANCHE}, timeout=15)
    if r.status_code != 200:
        return pd.DataFrame(columns=COLONNES)
    morceaux = []
    for f in r.json():
        if f["name"].startswith("visites-") and f["name"].endswith(".csv"):
            c = requests.get(f["download_url"], headers=_entetes(token), timeout=20)
            if c.ok:
                morceaux.append(pd.read_csv(io.StringIO(c.text), dtype=str))
    return pd.concat(morceaux, ignore_index=True) if morceaux else pd.DataFrame(columns=COLONNES)


def toutes() -> tuple[pd.DataFrame, str | None]:
    """Toutes les visites : fichiers GitHub + lignes encore en mémoire. Renvoie (tableau, message d'état ou None)."""
    m = _memoire()
    token = _secret("GITHUB_STATS_TOKEN")
    gh = pd.DataFrame(columns=COLONNES)
    if token:
        try:
            gh = _lire_github(token)
        except Exception as ex:
            m["erreur"] = f"Lecture GitHub impossible : {str(ex)[:160]}"
    with m["verrou"]:
        mem = pd.DataFrame(m["lignes"], columns=COLONNES)
    etat = m["erreur"] or (None if token else "Pas de clé GITHUB_STATS_TOKEN : visites gardées en mémoire seulement, perdues au redémarrage.")
    return pd.concat([gh, mem], ignore_index=True).fillna(""), etat


SCRIPT_MOI = (f'<script>document.cookie = "{COOKIE_MOI}=1; max-age=94608000; path=/; SameSite=Lax"'
              + ('; try { window.parent.document.cookie = "' + COOKIE_MOI + '=1; max-age=94608000; path=/; SameSite=Lax"; } catch (e) {}</script>'))
