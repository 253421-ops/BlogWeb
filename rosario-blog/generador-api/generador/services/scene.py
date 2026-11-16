"""Paisaje nocturno del sitio, dibujado como SVG. Los colores salen de variables CSS (--sky1, --mtn1…) que genera el CMS,
así cambiar de plantilla (noche, atardecer, amanecer) no requiere tocar este dibujo."""
import math
import random

W, H = 1600, 720


def _ridge(rng, base, amp, f1, f2, sharp=False):
    p1, p2, p3 = (rng.uniform(0, 6.3) for _ in range(3))
    pts = []
    for x in range(0, W + 41, 40):
        a = math.sin(x * f1 + p1) * amp + math.sin(x * f2 + p2) * amp * 0.45 + math.sin(x * f2 * 2.3 + p3) * amp * 0.15
        if sharp:
            a = -abs(a) * 1.15
        pts.append((x, round(base + a, 1)))
    return "M0,%d " % H + " ".join("L%d,%s" % p for p in pts) + " L%d,%d Z" % (W, H)


def _cypress(x, base, h, w):
    top = base - h
    body = (f'<path d="M{x},{top} C{x + w * .5},{top + h * .26} {x + w * .85},{top + h * .6} {x + w * .5},{base} '
            f'L{x - w * .5},{base} C{x - w * .85},{top + h * .6} {x - w * .5},{top + h * .26} {x},{top}Z" fill="var(--tree)"/>')
    swirl = "".join(f'<path d="M{x - w * .1},{base - h * k} q{w * .22},{-h * .06} {w * .12},{-h * .13}" stroke="var(--glow)" stroke-opacity=".10" stroke-width="2" fill="none"/>'
                    for k in (.15, .3, .45, .6, .75))
    return body + swirl


def _house(x, y, w, h, win):
    roof = f'<path d="M{x - 3},{y} L{x + w / 2},{y - h * .55} L{x + w + 3},{y}Z" fill="var(--house)"/>'
    body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="var(--house)"/>'
    light = "".join(f'<rect x="{x + 4 + i * (w / 2.2)}" y="{y + h * .3}" width="{w * .22}" height="{h * .32}" fill="var(--window)" opacity="{win[i % len(win)]}"/>' for i in range(2))
    return roof + body + light


def build_scene(seed: int = 7) -> str:
    rng = random.Random(seed)
    out = [f'<svg class="scenesvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" role="img" aria-label="Paisaje nocturno con luna, montañas, un pueblo y un campo de flores" xmlns="http://www.w3.org/2000/svg">']
    out.append('<defs>'
               '<linearGradient id="sky" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="560"><stop offset="0" stop-color="var(--sky1)"/><stop offset=".55" stop-color="var(--sky2)"/><stop offset="1" stop-color="var(--sky3)"/></linearGradient>'
               '<linearGradient id="gnd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--ground1)"/><stop offset="1" stop-color="var(--ground2)"/></linearGradient>'
               '<radialGradient id="halo"><stop offset="0" stop-color="var(--moon)" stop-opacity=".55"/><stop offset="1" stop-color="var(--moon)" stop-opacity="0"/></radialGradient>'
               '<radialGradient id="star"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".25" stop-color="var(--moon)" stop-opacity=".45"/><stop offset="1" stop-color="var(--moon)" stop-opacity="0"/></radialGradient>'
               '<radialGradient id="lamp"><stop offset="0" stop-color="var(--window)" stop-opacity=".8"/><stop offset="1" stop-color="var(--window)" stop-opacity="0"/></radialGradient>'
               '<filter id="neb" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.0045 0.012" numOctaves="5" seed="12" result="n"/>'
               '<feColorMatrix in="n" type="matrix" values="0 0 0 0 .78  0 0 0 0 .88  0 0 0 0 1  0 0 0 2.4 -.95"/></filter>'
               '<filter id="neb2" x="0" y="0" width="100%" height="100%"><feTurbulence type="turbulence" baseFrequency="0.003 0.02" numOctaves="3" seed="4" result="n"/>'
               '<feColorMatrix in="n" type="matrix" values="0 0 0 0 .45  0 0 0 0 .7  0 0 0 0 .95  0 0 0 2.1 -.7"/></filter>'
               '<filter id="soft"><feGaussianBlur stdDeviation="2.2"/></filter></defs>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    out.append(f'<rect width="{W}" height="520" filter="url(#neb2)" opacity=".38" style="mix-blend-mode:screen"/>')
    out.append(f'<rect width="{W}" height="520" filter="url(#neb)" opacity=".42" style="mix-blend-mode:screen"/>')
    stars = []
    for _ in range(230):
        x, y = rng.uniform(0, W), rng.uniform(0, 430) ** 1.0
        r = rng.choice([.8, .9, 1, 1.1, 1.3, 1.6, 2])
        stars.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{rng.uniform(.35, 1):.2f}"{" class=\"tw\"" if rng.random() < .22 else ""}/>')
    out.append('<g>' + "".join(stars) + '</g>')
    for bx, by, s in ((330, 120, 38), (760, 70, 30), (980, 220, 26), (140, 250, 24)):   # estrellas grandes con halo
        out.append(f'<circle cx="{bx}" cy="{by}" r="{s}" fill="url(#star)" class="tw"/><circle cx="{bx}" cy="{by}" r="2.6" fill="#fff"/>')
    out.append('<circle cx="1210" cy="160" r="150" fill="url(#halo)"/>'
               '<path d="M1226,110A50,50 0 1 0 1226,210A62,62 0 0 1 1226,110Z" fill="var(--moon)" transform="translate(-14 0)"/>')
    out.append(f'<path d="{_ridge(rng, 468, 34, .0042, .011, sharp=True)}" fill="var(--mtn1)" opacity=".85"/>')
    out.append(f'<rect y="430" width="{W}" height="120" fill="url(#sky)" opacity=".0"/>')
    out.append(f'<path d="{_ridge(rng, 520, 26, .006, .017)}" fill="var(--mtn2)"/>')
    # pueblo
    out.append('<g filter="url(#soft)" opacity=".95">')
    xs = 640
    for i in range(15):
        w, h = rng.randint(22, 38), rng.randint(16, 28)
        out.append(_house(xs, 548 - h + rng.randint(-3, 5), w, h, [rng.choice([.2, .9, 1]), rng.choice([.1, .85, 1])]))
        xs += w + rng.randint(2, 12)
    out.append(f'<path d="M780,540 L784,470 L788,540Z" fill="var(--house)"/><rect x="772" y="520" width="24" height="26" fill="var(--house)"/>')   # campanario
    out.append('</g>')
    out.append(f'<path d="{_ridge(rng, 580, 14, .004, .02)}" fill="var(--tree)" opacity=".9"/>')
    out.append(f'<path d="M0,600 C400,560 900,590 {W},570 L{W},{H} L0,{H}Z" fill="url(#gnd)"/>')
    # cipreses
    out.append('<g>' + _cypress(150, 610, 470, 120) + _cypress(250, 600, 330, 84) + _cypress(55, 620, 300, 78) + _cypress(1430, 600, 300, 82) + _cypress(1520, 610, 210, 60) + '</g>')
    # campo de flores
    fl = []
    for _ in range(520):
        y = rng.uniform(600, 716)
        t = (y - 600) / 116
        x = rng.uniform(0, W)
        rx = .8 + 3.4 * t
        c = rng.choices(["#f7d54a", "#f2b632", "#ffe27a", "#ff8fa3", "#fff3c4"], [5, 4, 3, 1, 1])[0]
        fl.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rx:.1f}" ry="{rx * .8:.1f}" fill="{c}" opacity="{.55 + .4 * t:.2f}"/>')
    out.append('<g>' + "".join(fl) + '</g>')
    out.append('<circle cx="1060" cy="668" r="46" fill="url(#lamp)"/><rect x="1056" y="656" width="8" height="12" rx="2" fill="var(--window)"/><rect x="1049" y="668" width="22" height="3" fill="var(--house)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#vig)" opacity="0"/>')
    out.append('</svg>')
    return "".join(out)
