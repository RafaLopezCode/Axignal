import hashlib
import json
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

root = Path(__file__).resolve().parents[1]
# The canonical catalog and authored UI define the public six-language repertoire.
# Keep ASCII, all their Latin characters, punctuation and combining marks. Other
# scripts remain eligible for the original full face outside this unicode-range.
copy = json.dumps(
    json.loads((root / "lib/translations.json").read_text(encoding="utf-8")), ensure_ascii=False
)
for folder in (root / "lib", root / "components", root / "app"):
    for source in folder.rglob("*.ts*"):
        copy += source.read_text(encoding="utf-8")
points = set(range(0x80)) | {
    ord(char)
    for char in copy
    if ord(char) <= 0x24F
    or 0x300 <= ord(char) <= 0x36F
    or 0x2000 <= ord(char) <= 0x206F
    or 0x20A0 <= ord(char) <= 0x20CF
    or 0x2190 <= ord(char) <= 0x21FF
    or ord(char) in (0x2212, 0x221E)
}


def unicode_ranges(values):
    groups = []
    for point in sorted(values):
        if groups and point == groups[-1][-1] + 1:
            groups[-1].append(point)
        else:
            groups.append([point])
    return ",".join(
        f"U+{group[0]:X}-{group[-1]:X}" if len(group) > 1 else f"U+{group[0]:X}" for group in groups
    )


# Handwriting is used only for these four authored annotations. Keep every
# character in all six canonical versions, with all OpenType alternate glyphs.
notes = ""
for source, keys in [
    ("lib/landing-lab-copy.ts", ("heroNote", "closingNote", "methodTitle")),
    ("lib/landing-lab-experience-copy.ts", ("trustNote",)),
]:
    text = (root / source).read_text(encoding="utf-8")
    for key in keys:
        call = re.search(r"\b" + key + r":\s*(?:w|words)\(([\s\S]*?)\n\s*\),", text)
        assert call, (source, key)
        literals = re.findall(r'"(?:[^"\\]|\\.)*"', call.group(1))
        assert len(literals) == 6, (source, key, len(literals))
        notes += "".join(json.loads(value) for value in literals)
# The zero glyph supplies ch-based annotation widths, even without a visible digit.
note_points = {ord(char) for char in notes} | {0x20, 0x30, 0xA0}
editorial_points = {
    ord(char)
    for char in json.loads((root / "lib/landing-lab-repertoire.json").read_text(encoding="utf-8"))[
        "characters"
    ]
} | {0x20, 0x30, 0xA0}

items = []
glyph_maps = []
for family, name, weight in [
    ("Manrope", "manrope-full.15e95cd6.woff2", "200 800"),
    ("Fraunces", "font-01.woff2", "300 600"),
    ("Bic Notes Lab", "caveat-latin.15bf208d.woff2", "400 700"),
    ("IBM Plex Mono", "font-04.woff2", "400"),
]:
    original = root / "public/fonts" / name
    font = TTFont(original, recalcTimestamp=False)
    if family == "Bic Notes Lab" and "fvar" in font:
        font = instantiateVariableFont(font, {"wght": 400}, inplace=True)
        weight = "400"
    face_points = {"Bic Notes Lab": note_points, "Fraunces": editorial_points}.get(family, points)
    face_range = unicode_ranges(face_points)
    expected = set(font.getBestCmap()) & face_points
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.notdef_outline = True
    opts.recalc_timestamp = False
    # Preserve every OpenType feature, including required variation substitutions.
    opts.layout_features = ["*"]
    if family in ("Fraunces", "Bic Notes Lab"):
        opts.hinting = False
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=face_points)
    sub.subset(font)
    temporary = root / "public/fonts" / ("lab-" + name)
    font.flavor = "woff2"
    original_names = list(font.getGlyphOrder())
    font.save(temporary)
    check = TTFont(temporary)
    glyph_maps.append(
        dict(family=family, pairs=list(zip(original_names, check.getGlyphOrder(), strict=True)))
    )
    if "GSUB" in TTFont(original):
        original_features = {
            entry.FeatureTag for entry in TTFont(original)["GSUB"].table.FeatureList.FeatureRecord
        }
        delivered_features = (
            {entry.FeatureTag for entry in check["GSUB"].table.FeatureList.FeatureRecord}
            if "GSUB" in check
            else set()
        )
        assert "rvrn" not in original_features or "rvrn" in delivered_features, (
            "Required variation feature must survive"
        )

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
            unicodeRange=face_range,
            glyphCoverage=len(expected),
        )
    )

manifest = root / "lib/landing-lab-fonts.json"
manifest.write_text(
    json.dumps(
        dict(
            note="Official fonts: glyph coverage and layout features retained. Manrope keeps variable weights; Fraunces retains its original 300-600 range and optical axes; notes use their exact 400 weight and the complete six-language annotation repertoire. Original font licenses remain in public/fonts. Non-Latin characters use the original face outside unicode-range.",
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
        + i["unicodeRange"]
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
