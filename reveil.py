"""Ouvre l'appli comme un visiteur et la réveille si Streamlit l'a mise en veille."""
import os
import sys
from playwright.sync_api import sync_playwright

# L'adresse du site se règle dans .github/workflows/reveil.yml (ligne APP_URL), pas ici.
URL = os.environ.get("APP_URL", "").strip()
if not URL:
    sys.exit("APP_URL manquante")

with sync_playwright() as p:
    nav = p.chromium.launch()
    page = nav.new_page()
    page.goto(URL, timeout=120_000)
    page.wait_for_timeout(8_000)
    bouton = page.get_by_role("button", name="Yes, get this app back up!")
    if bouton.count():
        print("Appli en veille : réveil en cours")
        bouton.click()
        page.wait_for_timeout(90_000)
    else:
        print("Appli déjà éveillée")
    nav.close()

