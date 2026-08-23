"""
Builds dark_mode.svg and light_mode.svg — a neofetch-style terminal
profile card for github.com/JosephNjorog/JosephNjorog.

Static structure (labels, layout, photo) lives here.
Live numbers are written into the tspans with id="..." by today.py
on every GitHub Actions run — this script only needs to be re-run if
you want to change the design itself.
"""

with open("portrait_b64.txt") as f:
    PORTRAIT_B64 = f.read().strip()

WIDTH, HEIGHT = 950, 640

WHOAMI_ROWS = [
    ("OS", "Kenya Linux (Nairobi Build)"),
    ("Host", "Elom Labs / MentalSynch / AutoPayKe"),
    ("Role", "Full Stack + Blockchain Engineer"),
    ("Shell", "TypeScript / Solidity"),
    ("Editor", "VS Code"),
    ("Building", "AutoPayKe . Elom Labs . MentalSynch"),
    ("LinkedIn", "josephmwangi-fullstackdev-mentalsynch"),
    ("X", "@code_mwangi"),
]

# (label, tspan id) -- values filled in live by today.py
STATS_ROWS = [
    ("Repos", "repo_data"),
    ("Contributed To", "contrib_data"),
    ("Stars", "star_data"),
    ("Commits (2026)", "commit_data"),
    ("Lines of Code", "loc_data"),
    ("Followers", "follower_data"),
]

COLOR_SWATCHES = [
    "#0D1117", "#3EDDFE", "#96EBFF", "#5A5A6E",
    "#FFFFFF", "#1F2937", "#3EDDFE", "#0D1117",
]


def theme_colors(dark: bool):
    if dark:
        return dict(
            bg="#0D1117",
            panel="#0B0F16",
            border="#1F2937",
            accent="#3EDDFE",
            text="#FFFFFF",
            dim="#8B96A5",
            titlebar="#161B22",
        )
    return dict(
        bg="#F6F8FA",
        panel="#FFFFFF",
        border="#D0D7DE",
        accent="#0D6E8F",
        text="#0D1117",
        dim="#57606A",
        titlebar="#EAEEF2",
    )


def build(dark: bool) -> str:
    c = theme_colors(dark)
    photo_x, photo_y, photo_w, photo_h = 34, 78, 300, 500
    right_x = 366
    right_w = WIDTH - right_x - 34

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="\'JetBrains Mono\', \'Fira Code\', \'Cascadia Code\', monospace">'
    )

    # ---- defs: clip path for the portrait ----
    parts.append(
        f'<defs><clipPath id="portraitClip"><rect x="{photo_x}" y="{photo_y}" '
        f'width="{photo_w}" height="{photo_h}" rx="10"/></clipPath></defs>'
    )

    # ---- background + outer window ----
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="{c["bg"]}"/>')
    parts.append(
        f'<rect x="1" y="1" width="{WIDTH-2}" height="{HEIGHT-2}" rx="13" '
        f'fill="none" stroke="{c["border"]}" stroke-width="1.5"/>'
    )

    # ---- title bar ----
    parts.append(f'<rect x="1" y="1" width="{WIDTH-2}" height="40" rx="13" fill="{c["titlebar"]}"/>')
    parts.append(f'<rect x="1" y="28" width="{WIDTH-2}" height="14" fill="{c["titlebar"]}"/>')
    for i, col in enumerate(["#FF5F56", "#FFBD2E", "#27C93F"]):
        parts.append(f'<circle cx="{28 + i*22}" cy="21" r="6" fill="{col}"/>')
    parts.append(
        f'<text x="{WIDTH/2}" y="26" text-anchor="middle" fill="{c["dim"]}" '
        f'font-size="13">joseph@nairobi — zsh</text>'
    )

    # ---- portrait panel ----
    parts.append(
        f'<image x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" '
        f'clip-path="url(#portraitClip)" preserveAspectRatio="xMidYMid slice" '
        f'href="data:image/png;base64,{PORTRAIT_B64}"/>'
    )
    parts.append(
        f'<rect x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" rx="10" '
        f'fill="none" stroke="{c["accent"]}" stroke-width="1.5" opacity="0.55"/>'
    )
    parts.append(
        f'<text x="{photo_x + photo_w/2}" y="{photo_y + photo_h + 34}" text-anchor="middle" '
        f'fill="{c["text"]}" font-size="20" font-weight="700">Joseph Njoroge Mwangi</text>'
    )
    parts.append(
        f'<text x="{photo_x + photo_w/2}" y="{photo_y + photo_h + 58}" text-anchor="middle" '
        f'fill="{c["accent"]}" font-size="13.5">@JosephNjorog</text>'
    )

    # ---- right column: whoami block ----
    ry = 78
    parts.append(f'<text x="{right_x}" y="{ry}" fill="{c["accent"]}" font-size="15" font-weight="700">$ whoami</text>')
    ry += 12
    parts.append(f'<line x1="{right_x}" y1="{ry}" x2="{right_x+right_w}" y2="{ry}" stroke="{c["border"]}" stroke-width="1"/>')
    ry += 24

    for label, value in WHOAMI_ROWS:
        parts.append(f'<text x="{right_x}" y="{ry}" fill="{c["dim"]}" font-size="13.5">{label}</text>')
        parts.append(
            f'<text x="{right_x+right_w}" y="{ry}" text-anchor="end" fill="{c["text"]}" '
            f'font-size="13.5">{value}</text>'
        )
        ry += 24

    # ---- right column: github stats block ----
    ry += 12
    parts.append(f'<text x="{right_x}" y="{ry}" fill="{c["accent"]}" font-size="15" font-weight="700">$ github --stats</text>')
    ry += 12
    parts.append(f'<line x1="{right_x}" y1="{ry}" x2="{right_x+right_w}" y2="{ry}" stroke="{c["border"]}" stroke-width="1"/>')
    ry += 24

    for label, val_id in STATS_ROWS:
        parts.append(f'<text x="{right_x}" y="{ry}" fill="{c["dim"]}" font-size="13.5">{label}</text>')
        parts.append(
            f'<text x="{right_x+right_w}" y="{ry}" text-anchor="end" fill="{c["text"]}" '
            f'font-size="13.5" id="{val_id}">0</text>'
        )
        ry += 24

    ry += 10
    parts.append(f'<text x="{right_x}" y="{ry}" fill="{c["dim"]}" font-size="11.5">Last synced <tspan id="sync_date">—</tspan></text>')

    # ---- color swatches (neofetch flourish) ----
    swatch_y = HEIGHT - 34
    for i, col in enumerate(COLOR_SWATCHES):
        parts.append(f'<rect x="{right_x + i*22}" y="{swatch_y}" width="16" height="16" rx="3" fill="{col}" stroke="{c["border"]}" stroke-width="0.5"/>')

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    with open("dark_mode.svg", "w") as f:
        f.write(build(dark=True))
    with open("light_mode.svg", "w") as f:
        f.write(build(dark=False))
    print("wrote dark_mode.svg and light_mode.svg")
