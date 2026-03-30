import math
from pathlib import Path
import cairosvg


def generate_forecast_radar(
    scores,
    output_svg="forecast_radar.svg",
    output_png="forecast_radar.png",
):
    order = [
        "Continuous Succession",
        "Shared Language",
        "Daily Coaching",
        "Trusted Conversations",
        "Guided Growth",
    ]

    if len(scores) != 5:
        raise ValueError("scores must contain exactly 5 numbers")

    if any((s < 0 or s > 15) for s in scores):
        raise ValueError("all scores must be between 0 and 15")

    W, H = 900, 650
    cx, cy = 450, 290
    outer_r = 178.5
    rings = 15
    ring_step = outer_r / rings

    angles = [-54, 18, 90, 162, 234]
    boundaries = [-90, -18, 54, 126, 198, 270]

    navy = "#2d2243"
    grey = "#c8c0ba"
    green = "#8faf7e"
    yellow = "#ea951d"
    text_col = "#918680"

    highest = max(scores)
    lowest = min(scores)
    lowest_index = next(i for i, s in enumerate(scores) if s == lowest)

    def pol(r, deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    def wedge(a1, a2, r):
        x1, y1 = pol(r, a1)
        x2, y2 = pol(r, a2)
        large = 1 if ((a2 - a1) % 360) > 180 else 0
        return (
            f"M {cx} {cy} "
            f"L {x1:.2f} {y1:.2f} "
            f"A {r:.2f} {r:.2f} 0 {large} 1 {x2:.2f} {y2:.2f} Z"
        )

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">']

    for i in range(5):
        r = outer_r * scores[i] / 15
        fill = green if scores[i] == highest else yellow if i == lowest_index else grey
        svg.append(f'<path d="{wedge(boundaries[i], boundaries[i+1], r)}" fill="{fill}"/>')

    for i in range(1, rings):
        svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{ring_step*i:.2f}" '
            f'fill="none" stroke="#948782" stroke-width="1.2"/>'
        )

    svg.append(
        f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" '
        f'fill="none" stroke="{navy}" stroke-width="3"/>'
    )

    for d in [-90, -18, 54, 126, 198]:
        x, y = pol(outer_r, d)
        svg.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" '
            f'stroke="{navy}" stroke-width="1.5"/>'
        )

    base_cx, base_cy = 322.18, 193.02
    tx = cx - base_cx
    ty = cy - base_cy
    rotation = angles[lowest_index] - 18

    svg.append(f"""
<g transform="translate({tx},{ty}) rotate({rotation} {base_cx} {base_cy})">
  <path fill="#000031" d="M329.11,193.01c0,.31-.02.61-.07.91l-.96,2.71-.13.35-.07-.05-11.4-7.84-.07-.05.27-.23,2.2-1.89s.01-.01.02-.01c.98-.53,2.09-.83,3.28-.83,3.82,0,6.93,3.11,6.93,6.93Z"/>
  <path fill="{navy}" d="M356.81,206.19l-30.32-6.65c2.71-1.39,4.18-4.56,3.33-7.61-.09-.34-.21-.67-.36-.99l27.34,15.25Z"/>
  <path fill="#f78f00" d="M329.61,193.01c0,4.11-3.33,7.43-7.43,7.43s-7.43-3.32-7.43-7.43c0-3.38,2.27-6.24,5.36-7.14l-1.21,1.04c.98-.53,2.09-.83,3.28-.83,3.82,0,6.93,3.11,6.93,6.93Z"/>
</g>
""")

    svg.append(
        f'<circle cx="{cx}" cy="{cy}" r="9.5" fill="{yellow}" stroke="white" stroke-width="2"/>'
    )

    gap_by_label = {
        "Continuous Succession": 64,
        "Shared Language": 64,
        "Daily Coaching": 62,
        "Trusted Conversations": 76,
        "Guided Growth": 64,
    }

    y_adjust = {
        "Continuous Succession": -6,
        "Shared Language": 0,
        "Daily Coaching": -8,
        "Trusted Conversations": -6,
        "Guided Growth": -6,
    }

    for i, name in enumerate(order):
        x, y = pol(outer_r + gap_by_label[name], angles[i])
        y += y_adjust[name]
        svg.append(f'''
<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle"
      font-family="Arial, Helvetica, sans-serif" fill="{text_col}">
  <tspan font-size="14">{name}</tspan>
  <tspan x="{x:.2f}" dy="18" font-size="13">{scores[i]}/15</tspan>
</text>
''')

    svg.append("</svg>")
    svg_str = "\n".join(svg)

    Path(output_svg).write_text(svg_str, encoding="utf-8")

    cairosvg.svg2png(
        bytestring=svg_str.encode("utf-8"),
        write_to=output_png,
        output_width=W * 4,
        output_height=H * 4,
    )

    return output_svg, output_png


def get_bar_label(score: float) -> str:
    if 15 <= score <= 39:
        return "Fragile"
    elif 40 <= score <= 57:
        return "Vulnerable"
    elif 58 <= score <= 75:
        return "Future-Proof"
    return ""


def generate_forecast_bar(
    total_score,
    output_svg="forecast_bar.svg",
    output_png="forecast_bar.png",
    total=75,
    png_scale=4.0,
):
    """
    Locked forecast bar template.

    Uses approved design:
    - 516.87 x 72.56 viewBox
    - gradient bar
    - vertical marker line behind bar
    - marker dot above
    - auto top labels: score/total and Fragile/Vulnerable/Future-Proof
    """

    W, H = 516.87, 72.56
    X_START, X_END = 6.5, 510.37
    Y_BAR = 66.06
    Y_LINE_TOP = 47.61
    Y_DOT = 44.04
    DOT_R = 3.5

    if total <= 0:
        raise ValueError("total must be greater than 0")

    score = max(0, min(float(total_score), float(total)))
    x = X_START + (score / total) * (X_END - X_START)
    label = get_bar_label(score)
    top_text = f"{int(score)}/{int(total)}"

    label_tspan = f'<tspan x="{x:.2f}" y="24.52">{label}</tspan>' if label else ""

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bar-gradient" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ff3800"/>
      <stop offset=".5" stop-color="#f78f00"/>
      <stop offset="1" stop-color="#8faf7e"/>
    </linearGradient>
  </defs>

  <line x1="{x:.2f}" y1="{Y_LINE_TOP}" x2="{x:.2f}" y2="{Y_BAR}"
        stroke="#918680" stroke-width=".75" stroke-linecap="round"/>

  <line x1="{X_START}" y1="{Y_BAR}" x2="{X_END}" y2="{Y_BAR}"
        stroke="url(#bar-gradient)" stroke-width="13" stroke-linecap="round"/>

  <circle cx="{x:.2f}" cy="{Y_DOT}" r="{DOT_R}"
          fill="#918680" stroke="#918680" stroke-width=".75"/>

  <text x="{x:.2f}" y="10.12" text-anchor="middle"
        font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#918680">
    <tspan x="{x:.2f}" y="10.12">{top_text}</tspan>
    {label_tspan}
  </text>
</svg>'''

    Path(output_svg).write_text(svg, encoding="utf-8")

    if output_png:
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=output_png,
            scale=png_scale,
        )

    return output_svg, output_png
