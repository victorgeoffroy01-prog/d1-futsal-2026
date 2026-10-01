"""Charte graphique D1 Futsal (reprise des rapports de match) et CSS global de l'appli mobile."""
CR = "#F4EFE6"      # fond crème
PAPER = "#FBF8F2"   # cartes
INK = "#111111"     # encre
RED = "#C8102E"     # rouge dépêche
MUTED = "#5E574C"   # texte secondaire
LINE = "#D6CDBD"    # filets
SOFT = "#E9E2D5"    # fonds discrets

SERIF = "'DM Serif Display', Georgia, serif"
SANS = "'Archivo', 'Helvetica Neue', Arial, sans-serif"
COND = "'Archivo Narrow', 'Archivo', Arial, sans-serif"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Narrow:wght@500;600;700&family=Archivo:wght@400;500;600;700;800&family=DM+Serif+Display&display=swap');
/* --- on efface l'habillage Streamlit --- */
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
.stApp {{ background: {CR}; }}
.block-container, [data-testid="stMainBlockContainer"] {{
  max-width: 480px !important; padding: 0 0 96px 0 !important; margin: 0 auto;
}}
[data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
[data-testid="stElementContainer"], .element-container {{ margin: 0 !important; }}
html, body, .stApp, .stMarkdown, .stHtml {{ font-family: {SANS}; color: {INK}; }}
a {{ color: {INK}; text-decoration: none; }}
a:focus-visible, button:focus-visible {{ outline: 3px solid {RED}; outline-offset: 2px; }}
/* champ de recherche */
[data-testid="stTextInput"] {{ padding: 12px 16px 4px; }}
[data-testid="stTextInput"] input {{ background: {PAPER}; border: 1.5px solid {INK}; border-radius: 999px;
  height: 44px; padding: 0 16px; font-family: {SANS}; font-size: 15px; }}
[data-testid="stTextInput"] label {{ display: none; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
"""

# espace pour la barre de navigation fixe en haut et le badge Streamlit en bas
CSS += """
<style>
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 58px !important; padding-bottom: 110px !important; }
.st-key-scorebox { background: #FBF8F2; border-bottom: 1px solid #D6CDBD; }
.st-key-scorebox [class*="st-key-rw-cards"] { padding: 0 16px; }
[class*="st-key-pad-"] { padding: 0 16px; }
[data-testid="stSelectbox"], [data-testid="stDownloadButton"] { padding: 4px 16px; }
</style>
"""
