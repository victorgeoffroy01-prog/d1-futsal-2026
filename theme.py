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
  height: 44px; padding: 0 16px; font-family: {SANS}; font-size: 15px; color: {INK} !important; -webkit-text-fill-color: {INK} !important; caret-color: {INK}; }}
[data-testid="stTextInput"] input::placeholder {{ color: {MUTED} !important; -webkit-text-fill-color: {MUTED} !important; }}
[data-testid="stTextInput"] div {{ background: transparent !important; border-color: transparent !important; overflow: visible !important; height: auto !important; }}
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

# lien de bascule mobile / ordinateur, en bas de page
CSS += """
<style>
.st-key-bascule { padding: 0 16px 16px; }
.st-key-bascule button p { font-size: 12px !important; color: #5E574C; text-decoration: underline; }
</style>
"""

CSS += """
<style>
.st-key-rapport-m { padding: 0 16px 8px; }
</style>
"""

CSS += """
<style>
.st-key-editeur { padding: 0 16px 16px; }
.st-key-editeur [data-testid="stSelectbox"], .st-key-editeur [data-testid="stDownloadButton"] { padding: 0; }
</style>
"""

# page contrôle : cases de saisie toujours lisibles, quel que soit le thème du navigateur
CSS += """
<style>
.st-key-editeur textarea, .st-key-editeur [data-baseweb="select"] > div { background: #FBF8F2 !important; color: #111 !important;
  -webkit-text-fill-color: #111 !important; border: 1.5px solid #111 !important; border-radius: 8px !important; font-size: 15px !important; }
.st-key-editeur [data-baseweb="select"] svg { fill: #111 !important; }
.st-key-editeur p, .st-key-editeur label, .st-key-editeur summary, .st-key-editeur [data-testid="stText"],
.st-key-editeur [data-testid="stCaptionContainer"] { color: #111 !important; }
.st-key-editeur [data-testid="stExpander"] details { background: #FBF8F2 !important; border: 1px solid #D6CDBD !important; }
.st-key-editeur [data-testid="stCheckbox"] span:first-child { border-color: #111 !important; }
.st-key-editeur [data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF55; border-color: #111 !important; }
</style>
"""

CSS += """
<style>
[data-testid="InputInstructions"] { display: none !important; }
</style>
"""
