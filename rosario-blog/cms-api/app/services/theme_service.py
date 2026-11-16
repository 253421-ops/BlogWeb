"""Genera el CSS del tema visual. El tema se guarda como una página en borrador (slug «tema-visual»),
así no hace falta cambiar las tablas de la base. El CSS sólo puede contener valores validados:
la usuaria elige una plantilla y un color, nunca escribe CSS."""
import json

from ..models.schemas import ThemeIn

THEME_SLUG = "tema-visual"
FONTS = {  # lista cerrada de tipografías
    "manuscrita": ("'Dancing Script','Segoe Script',cursive", "'Montserrat',system-ui,sans-serif"),
    "clasica": ("'Playfair Display',Georgia,serif", "Georgia,'Times New Roman',serif"),
    "moderna": ("'Montserrat',system-ui,sans-serif", "'Montserrat',system-ui,sans-serif"),
}
SCENES = {  # paleta de cada plantilla: cielo, luna, montañas, árboles, casas, campo, acento
    "noche": dict(bg="#070d2b", bg2="#0e1b4d", sky1="#050a24", sky2="#10265e", sky3="#4d86a8", moon="#f8e7a0", mtn1="#1d3b52", mtn2="#11261f",
                  tree="#0b1c15", house="#141a33", window="#ffd166", ground1="#1d3b22", ground2="#0b1d12", glow="#f5d36b", accent="#f5c451", paper="#fbf1d3", text="#eef1ff"),
    "atardecer": dict(bg="#1b1140", bg2="#3a1d5a", sky1="#1b1140", sky2="#7a3a86", sky3="#ff9a5c", moon="#fff0c4", mtn1="#5a3270", mtn2="#2a1738",
                      tree="#170d22", house="#1d1230", window="#ffd89a", ground1="#34402a", ground2="#171d17", glow="#ffc58a", accent="#ffb36b", paper="#ffe9d2", text="#fff3ea"),
    "amanecer": dict(bg="#1a2a5a", bg2="#3b3f7a", sky1="#1a2a5a", sky2="#c46a9a", sky3="#ffc9a3", moon="#fff7e0", mtn1="#51628f", mtn2="#2f4a4a",
                     tree="#1a2f2f", house="#243a4d", window="#fff0b8", ground1="#3f6b4a", ground2="#1f3a2a", glow="#ffe1b8", accent="#ff8fa3", paper="#ffe3ea", text="#fff6f2"),
}


def parse_theme(content: str | None) -> ThemeIn:
    try:
        return ThemeIn.model_validate(json.loads(content or "{}"))
    except Exception:  # noqa: BLE001  (contenido dañado o de una versión anterior → tema por defecto)
        return ThemeIn()


def theme_css(theme: ThemeIn) -> str:
    pal = dict(SCENES[theme.scene])
    if theme.accent:
        pal["accent"] = theme.accent
    head, body = FONTS[theme.font]
    vars_ = ";".join(f"--{k}:{v}" for k, v in pal.items())
    return f":root{{{vars_};--font-head:{head};--font-body:{body}}}"
