"""Genera el CSS del tema visual. El tema se guarda como una página en borrador (slug «tema-visual»),
así no hace falta cambiar las tablas de la base. El CSS sólo puede contener valores validados:
la usuaria elige modo, atmósfera, tipografías y escala, nunca escribe CSS.

El CSS trae DOS paletas: la del modo elegido en `:root` y la contraria en `:root[data-mode=...]`.
Así el lector puede alternar claro/oscuro sin pedir nada al servidor."""
import json

from ..models.schemas import ThemeIn

THEME_SLUG = "tema-visual"

HEAD = {  # tipografías de títulos (lista cerrada)
    "editorial-serif": "'Playfair Display','Newsreader',Georgia,serif",
    "modern-sans": "'Plus Jakarta Sans','Inter',system-ui,sans-serif",
    "humanist-serif": "'Lora','Fraunces',Georgia,serif",
    "script-accent": "'Dancing Script','Caveat','Segoe Script',cursive",
}
BODY = {  # tipografías de lectura
    "reading-serif": "'Source Serif 4',Georgia,serif",
    "clean-sans": "'Inter',system-ui,-apple-system,'Segoe UI',sans-serif",
    "humanist-sans": "'Atkinson Hyperlegible','DM Sans',system-ui,sans-serif",
}
MONO = {  # código y etiquetas
    "jetbrains": "'JetBrains Mono',ui-monospace,Consolas,monospace",
    "fira": "'Fira Code',ui-monospace,Consolas,monospace",
}
LEGACY_FONT = {"manuscrita": "script-accent", "clasica": "editorial-serif", "moderna": "modern-sans"}  # valores del tema antiguo
SCALES = {"compact": (16, 1.20), "editorial": (18, 1.25), "spacious": (20, 1.333)}   # (px base, razón)

DARK_SCENES = ("noche", "atardecer", "amanecer")
LIGHT_SCENES = ("papel", "pastel", "menta")
DEFAULT_SCENE = {"dark": "noche", "light": "papel"}

SCENES = {  # paleta de cada atmósfera: cielo, luna, montañas, árboles, casas, campo, acento y colores de interfaz
    "noche": dict(bg="#070d2b", bg2="#0e1b4d", sky1="#050a24", sky2="#10265e", sky3="#4d86a8", moon="#f8e7a0", mtn1="#1d3b52", mtn2="#11261f",
                  tree="#0b1c15", house="#141a33", window="#ffd166", ground1="#1d3b22", ground2="#0b1d12", glow="#f5d36b", accent="#f5c451", paper="#fbf1d3", text="#eef1ff",
                  surface="rgba(255,255,255,.06)", border="rgba(255,255,255,.14)", muted="#aeb9e6", hero="#ffffff"),
    "atardecer": dict(bg="#1b1140", bg2="#3a1d5a", sky1="#1b1140", sky2="#7a3a86", sky3="#ff9a5c", moon="#fff0c4", mtn1="#5a3270", mtn2="#2a1738",
                      tree="#170d22", house="#1d1230", window="#ffd89a", ground1="#34402a", ground2="#171d17", glow="#ffc58a", accent="#ffb36b", paper="#ffe9d2", text="#fff3ea",
                      surface="rgba(255,255,255,.06)", border="rgba(255,255,255,.14)", muted="#d9c3dc", hero="#ffffff"),
    "amanecer": dict(bg="#1a2a5a", bg2="#3b3f7a", sky1="#1a2a5a", sky2="#c46a9a", sky3="#ffc9a3", moon="#fff7e0", mtn1="#51628f", mtn2="#2f4a4a",
                     tree="#1a2f2f", house="#243a4d", window="#fff0b8", ground1="#3f6b4a", ground2="#1f3a2a", glow="#ffe1b8", accent="#ff8fa3", paper="#ffe3ea", text="#fff6f2",
                     surface="rgba(255,255,255,.06)", border="rgba(255,255,255,.14)", muted="#cdd3f0", hero="#ffffff"),
    # --- modo claro ---
    "papel": dict(bg="#fbf8f1", bg2="#f1ebdd", sky1="#e9e2d0", sky2="#f3d9b8", sky3="#fbe9d2", moon="#fff6dc", mtn1="#c9b99a", mtn2="#a8b79a",
                  tree="#5f7d5a", house="#8a7b6a", window="#ffe08a", ground1="#a9c18f", ground2="#7f9f6a", glow="#f6d58a", accent="#8f5a00", paper="#fff3d6", text="#1d1b16",
                  surface="rgba(0,0,0,.035)", border="rgba(0,0,0,.13)", muted="#5b5548", hero="#1d1b16"),
    "pastel": dict(bg="#fdf4f8", bg2="#f6e6f0", sky1="#f3dcec", sky2="#e3d4f7", sky3="#fde1d3", moon="#fff7e8", mtn1="#c8b6e2", mtn2="#a9c6c0",
                   tree="#6e9b8a", house="#9a88b8", window="#ffe7a1", ground1="#b9d8b0", ground2="#8fbf9d", glow="#ffd9e8", accent="#a3246a", paper="#ffeaf3", text="#2a1b30",
                   surface="rgba(80,20,80,.04)", border="rgba(60,20,70,.14)", muted="#65506c", hero="#2a1b30"),
    "menta": dict(bg="#f2f9f4", bg2="#e0f0e6", sky1="#d4ecdf", sky2="#cfe8f0", sky3="#f1f8e6", moon="#fffbe6", mtn1="#9fc7b0", mtn2="#7fae98",
                  tree="#3f7a5e", house="#7d9a8c", window="#fff0a8", ground1="#a8d4a0", ground2="#6fb086", glow="#e6f5c8", accent="#1c6b4a", paper="#e8f6dc", text="#13281d",
                  surface="rgba(10,60,30,.045)", border="rgba(10,60,30,.15)", muted="#44594c", hero="#13281d"),
}


# ---------------------------------------------------------------- contraste WCAG
def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def _lum(hex_: str) -> float:
    def chan(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(v) for v in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """Razón de contraste WCAG entre dos colores #rrggbb (1 a 21)."""
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ensure_contrast(fg: str, bg: str, minimum: float = 4.5) -> str:
    """Si `fg` no alcanza el contraste mínimo sobre `bg`, lo acerca a blanco o negro (el que mejor contraste dé) hasta lograrlo."""
    if contrast(fg, bg) >= minimum:
        return fg
    target = (255, 255, 255) if contrast("#ffffff", bg) >= contrast("#000000", bg) else (0, 0, 0)
    base = _rgb(fg)
    for i in range(1, 21):
        t = i / 20
        cand = _hex(tuple(b + (g - b) * t for b, g in zip(base, target)))
        if contrast(cand, bg) >= minimum:
            return cand
    return _hex(target)


def on_color(bg: str) -> str:
    """Color de texto (casi negro o blanco) con mejor contraste sobre `bg` (botones de acento)."""
    return "#14193a" if contrast("#14193a", bg) >= contrast("#ffffff", bg) else "#ffffff"


# ---------------------------------------------------------------- paletas y CSS
def parse_theme(content: str | None) -> ThemeIn:
    try:
        return ThemeIn.model_validate(json.loads(content or "{}"))
    except Exception:  # noqa: BLE001  (contenido dañado o de una versión anterior → tema por defecto)
        return ThemeIn()


def scene_for(mode: str, scene: str) -> str:
    """La atmósfera que de verdad se usa: si no cuadra con el modo (p. ej. «noche» en modo claro) se toma la de por defecto de ese modo."""
    allowed = DARK_SCENES if mode == "dark" else LIGHT_SCENES
    return scene if scene in allowed else DEFAULT_SCENE[mode]


def palette(mode: str, scene: str, accent: str | None) -> dict:
    """Paleta completa de un modo, con el contraste mínimo WCAG AA (4,5:1) ya garantizado."""
    pal = dict(SCENES[scene_for(mode, scene)])
    if accent:
        pal["accent"] = accent
    pal["text"] = ensure_contrast(pal["text"], pal["bg"])           # texto sobre fondo
    pal["muted"] = ensure_contrast(pal["muted"], pal["bg"])         # texto secundario sobre fondo
    pal["accent"] = ensure_contrast(pal["accent"], pal["bg"], 3.0)  # el acento se usa en enlaces y detalles grandes: 3:1 mínimo
    pal["accent_text"] = ensure_contrast(pal["accent"], pal["bg"])  # el acento cuando es texto pequeño: 4,5:1
    pal["on_accent"] = on_color(pal["accent"])
    r, g, b = _rgb(pal["bg"])
    pal["dock"] = f"rgba({r},{g},{b},.9)"                           # barra inferior y paneles flotantes
    dark = mode == "dark"
    pal["hero_shadow"] = "rgba(0,0,0,.5)" if dark else "rgba(255,255,255,.7)"
    pal["code_bg"] = "rgba(0,0,0,.38)" if dark else "rgba(0,0,0,.045)"
    return pal


# nombre de la variable CSS -> clave de la paleta
_VARS = [("bg", "bg"), ("bg2", "bg2"), ("surface", "surface"), ("text", "text"), ("text-muted", "muted"), ("accent", "accent"), ("accent-text", "accent_text"),
         ("on-accent", "on_accent"), ("border", "border"), ("hero", "hero"), ("sky1", "sky1"), ("sky2", "sky2"), ("sky3", "sky3"), ("moon", "moon"),
         ("mtn1", "mtn1"), ("mtn2", "mtn2"), ("tree", "tree"), ("house", "house"), ("window", "window"), ("ground1", "ground1"), ("ground2", "ground2"),
         ("glow", "glow"), ("paper", "paper"), ("dock", "dock"), ("hero-shadow", "hero_shadow"), ("code-bg", "code_bg")]


def _block(selector: str, pal: dict, extra: str = "") -> str:
    vars_ = ";".join(f"--{name}:{pal[key]}" for name, key in _VARS)
    return f"{selector}{{{vars_}{extra}}}"


def fonts_of(theme: ThemeIn) -> tuple[str, str, str]:
    head_key = LEGACY_FONT.get(theme.font or "", theme.font_head)
    return HEAD[head_key], BODY[theme.font_body], MONO[theme.font_mono]


def scale_vars(scale: str) -> str:
    """Escala modular: `--text-base` y `--scale-ratio` más los pasos ya calculados (--step-0 … --step-5, en px)."""
    base, ratio = SCALES[scale]
    steps = ";".join(f"--step-{i}:{base * ratio ** i:.2f}px" for i in range(0, 6))
    return f"--text-base:{base}px;--scale-ratio:{ratio};{steps}"


def theme_css(theme: ThemeIn) -> str:
    head, body, mono = fonts_of(theme)
    mode, other = theme.mode, ("light" if theme.mode == "dark" else "dark")
    common = f";--font-head:{head};--font-body:{body};--font-mono:{mono};{scale_vars(theme.font_scale)}"
    main = _block(":root", palette(mode, theme.scene, theme.accent), common)
    alt = _block(f":root[data-mode={other}]", palette(other, theme.scene, theme.accent))
    return main + alt


# Google Fonts: sólo se descargan las tres familias elegidas (más rápido y más privado que cargarlas todas)
GOOGLE = {"editorial-serif": "Playfair+Display:wght@600;700", "modern-sans": "Plus+Jakarta+Sans:wght@600;700", "humanist-serif": "Lora:wght@600;700",
          "script-accent": "Dancing+Script:wght@600;700", "reading-serif": "Source+Serif+4:wght@400;600", "clean-sans": "Inter:wght@400;600",
          "humanist-sans": "Atkinson+Hyperlegible:wght@400;700", "jetbrains": "JetBrains+Mono:wght@400;600", "fira": "Fira+Code:wght@400;600"}


def fonts_url(theme: ThemeIn) -> str:
    keys = [LEGACY_FONT.get(theme.font or "", theme.font_head), theme.font_body, theme.font_mono]
    fams = list(dict.fromkeys(GOOGLE[k] for k in keys))
    return "https://fonts.googleapis.com/css2?" + "&".join(f"family={f}" for f in fams) + "&display=swap"
