"""Romanian text normalisation shared by every rivernet stage.

Pure functions, standard library only.

* ``fix_diacritics`` — keep case, repair legacy orthography for DISPLAY
  (cedilla ``ş ţ`` -> comma-below ``ș ț``, mis-rendered ``å`` -> ``â``).
* ``fold`` — aggressive key form: diacritics stripped, lower-case, punctuation
  removed (hyphens kept), whitespace collapsed.
* ``river_keys`` / ``river_key`` — match keys for a river's name, most specific
  first, with generic prefixes (``Râul``, ``Pârâul``...) and sector qualifiers
  (``Inferior``, ``II``...) removed.
"""

from __future__ import annotations

import re
import unicodedata

# Legacy / mis-encoded characters seen in the ANPA lists and old OSM names.
_DIACRITIC_FIXES = str.maketrans(
    {
        "ş": "ș",
        "ţ": "ț",
        "Ş": "Ș",
        "Ţ": "Ț",
        "å": "â",
        "Å": "Â",
    }
)

# Leading generic words (already folded). "valea" is handled separately.
_GENERIC_PREFIXES = frozenset(
    {
        "raul",
        "rau",
        "paraul",
        "parau",
        "piriul",  # old orthography: pîrîul
        "piriu",
        "pr",
        "r",
        "fluviul",
        "canalul",
        "vl",
    }
)

# Trailing sector / position qualifiers (already folded).
_TRAILING_QUALIFIERS = frozenset(
    {"superior", "mijlociu", "inferior", "amonte", "aval", "i", "ii", "iii", "iv"}
)

# A qualifier phrase that starts a free-text tail: "Olt sector Făgăraș" -> "olt".
_TAIL_MARKERS = frozenset({"sector", "zona"})

# "Jiul de Vest" has the shorter alias "Jiul".
_CARDINALS = frozenset({"est", "vest", "nord", "sud"})

_PUNCT_RE = re.compile(r"[^\w\s-]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")


def fix_diacritics(text: str | None) -> str:
    """Repair legacy diacritics for display; case and punctuation are kept."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text).translate(_DIACRITIC_FIXES)


def fold(text: str | None) -> str:
    """Lower-case, diacritic-free, punctuation-free (hyphens kept) key form.

    Non-Latin scripts (e.g. Cyrillic border-river names) are lower-cased and
    passed through unchanged.
    """
    if not text:
        return ""
    s = fix_diacritics(text).lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("_", " ")
    s = _PUNCT_RE.sub(" ", s)
    return _SPACE_RE.sub(" ", s).strip()


def river_keys(name: str | None) -> list[str]:
    """Match keys for a river name, most specific first, without duplicates.

    >>> river_keys("Râul Geoagiu Inferior")
    ['geoagiu']
    >>> river_keys("Valea Iadului")
    ['valea iadului', 'iadului']
    >>> river_keys("Jiul de Vest")
    ['jiul de vest', 'jiul']
    """
    folded = fold(name)
    if not folded:
        return []
    tokens = folded.split(" ")

    # 1. strip leading generic words ("Râul", "Pârâul", "Pr.", ...)
    start = 0
    while start < len(tokens) - 1 and tokens[start] in _GENERIC_PREFIXES:
        start += 1
    tokens = tokens[start:]

    # 2. cut free-text tails ("sector ...", "zona ...") that don't start the name
    for i in range(1, len(tokens)):
        if tokens[i] in _TAIL_MARKERS:
            tokens = tokens[:i]
            break

    # 3. strip trailing qualifiers ("Inferior", "II", ...)
    end = len(tokens)
    while end > 1 and tokens[end - 1] in _TRAILING_QUALIFIERS:
        end -= 1
    tokens = tokens[:end]

    # 4. "valea X": keep both "valea x" and "x" unless x is itself generic
    candidates: list[list[str]] = []
    if tokens[0] == "valea" and len(tokens) > 1:
        rest = tokens[1:]
        while len(rest) > 1 and rest[0] in _GENERIC_PREFIXES:
            rest = rest[1:]
        if rest[0] in _GENERIC_PREFIXES:
            candidates.append(rest)
        else:
            candidates.append(["valea", *rest])
            candidates.append(rest)
    else:
        candidates.append(tokens)

    # 5. "<name> de est|vest|nord|sud" also answers to the shorter "<name>"
    expanded: list[list[str]] = []
    for cand in candidates:
        expanded.append(cand)
        if len(cand) >= 3 and cand[-2] == "de" and cand[-1] in _CARDINALS:
            expanded.append(cand[:-2])

    keys: list[str] = []
    for cand in expanded:
        key = " ".join(cand)
        if key and key not in keys:
            keys.append(key)
    return keys


def river_key(name: str | None) -> str:
    """The most specific match key for a river name ('' if there is none)."""
    keys = river_keys(name)
    return keys[0] if keys else ""


# ISO-style county codes used in ANPA texts ("Limita jud. HD") -> display name.
COUNTY_CODES: dict[str, str] = {
    "AB": "Alba", "AR": "Arad", "AG": "Argeș", "BC": "Bacău", "BH": "Bihor",
    "BN": "Bistrița-Năsăud", "BT": "Botoșani", "BV": "Brașov", "BR": "Brăila",
    "BZ": "Buzău", "CS": "Caraș-Severin", "CL": "Călărași", "CJ": "Cluj",
    "CT": "Constanța", "CV": "Covasna", "DB": "Dâmbovița", "DJ": "Dolj",
    "GL": "Galați", "GR": "Giurgiu", "GJ": "Gorj", "HR": "Harghita",
    "HD": "Hunedoara", "IL": "Ialomița", "IS": "Iași", "IF": "Ilfov",
    "MM": "Maramureș", "MH": "Mehedinți", "MS": "Mureș", "NT": "Neamț",
    "OT": "Olt", "PH": "Prahova", "SM": "Satu Mare", "SJ": "Sălaj",
    "SB": "Sibiu", "SV": "Suceava", "TR": "Teleorman", "TM": "Timiș",
    "TL": "Tulcea", "VS": "Vaslui", "VL": "Vâlcea", "VN": "Vrancea",
    "B": "București",
}


def county_names_folded() -> dict[str, str]:
    """folded county name -> display name (also folded code -> display name)."""
    out = {fold(name): name for name in COUNTY_CODES.values()}
    out.update({code.lower(): name for code, name in COUNTY_CODES.items() if len(code) > 1})
    return out
