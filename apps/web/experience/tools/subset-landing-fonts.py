import hashlib
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

root = Path(__file__).resolve().parents[1]
unicode_range = "U+0-24F,U+300-36F,U+2000-206F,U+20A0-20CF,U+2190-21FF,U+2212,U+221E"
points = (
    set(range(0x250))
    | set(range(0x300, 0x370))
    | set(range(0x2000, 0x2070))
    | set(range(0x20A0, 0x20D0))
    | set(range(0x2190, 0x2200))
    | {0x2212, 0x221E}
)
items = []
for family, name, weight in [
    ("Manrope", "manrope-full.15e95cd6.woff2", "200 800"),
    ("Fraunces", "font-01.woff2", "300 600"),
    ("Bic Notes Lab", "caveat-latin.15bf208d.woff2", "400 700"),
    ("IBM Plex Mono", "font-04.woff2", "400"),
]:
    original = root / "public/fonts" / name
    font = TTFont(original, recalcTimestamp=False)
    if family in ("Fraunces", "Bic Notes Lab") and "fvar" in font:
        font = instantiateVariableFont(font, {"wght": 400}, inplace=True)
        weight = "400"
    expected = set(font.getBestCmap()) & points
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.recalc_timestamp = False
    opts.layout_features = ["*"]
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=points)
    sub.subset(font)
    temporary = root / "public/fonts" / ("lab-" + name)
    font.flavor = "woff2"
    font.save(temporary)
    check = TTFont(temporary)
    assert expected <= set(check.getBestCmap()), (family, expected - set(check.getBestCmap()))
    data = temporary.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    output = "lab-" + family.lower().replace(" ", "-") + "." + digest[:12] + ".woff2"
    target = temporary.with_name(output)
    temporary.replace(target)
    items.append(
        dict(
            family=family,
            url="/fonts/" + output,
            source="/fonts/" + name,
            bytes=len(data),
            sourceBytes=original.stat().st_size,
            sha256=digest,
            weight=weight,
            unicodeRange=unicode_range,
            glyphCoverage=len(expected),
        )
    )

manifest = root / "lib/landing-lab-fonts.json"
manifest.write_text(
    json.dumps(
        dict(
            note="Official fonts: glyph coverage and layout features retained. Manrope keeps variable weights; Fraunces and notes use the exact 400 weight shown by this surface, retaining optical axes. Original font licenses remain in public/fonts. Non-Latin characters use the original face outside unicode-range.",
            fonts=items,
        ),
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
css = root / "components/landing-lab.css"
text = css.read_text(encoding="utf-8")
# Replace its two existing face rules; preserve every layout declaration below.
start = text.index(".landing-lab {")
faces = (
    "\n".join(
        "@font-face {\n  font-family: "
        + json.dumps(i["family"])
        + ';\n  src: url("'
        + i["url"]
        + '") format("woff2");\n  font-weight: '
        + i["weight"]
        + ";\n  font-display: swap;\n  unicode-range: "
        + unicode_range
        + ";\n}"
        for i in items
    )
    + "\n"
)
css.write_text(faces + text[start:], encoding="utf-8")
component = root / "components/landing-lab.tsx"
text = component.read_text(encoding="utf-8").replace(
    'import { PUBLIC_BODY_FONT, PUBLIC_DISPLAY_FONT } from "@/lib/marketing-media";',
    'import labFonts from "@/lib/landing-lab-fonts.json";',
)
text = text.replace("href={PUBLIC_DISPLAY_FONT}", "href={labFonts.fonts[1].url}").replace(
    "href={PUBLIC_BODY_FONT}", "href={labFonts.fonts[0].url}"
)
component.write_text(text, encoding="utf-8")
print(
    json.dumps(
        [dict(family=i["family"], before=i["sourceBytes"], after=i["bytes"]) for i in items],
        indent=2,
    )
)
