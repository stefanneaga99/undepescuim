"""Rule-based parser for the ANPA ``limite`` text of a river water (T3.1).

``parse_limits(text, water_name=...)`` is pure (no I/O) and turns strings like
``"Izvoare – conf. râul Olt"`` or ``"Baraj Baciu - Pod Stefan din loc.Slatina"``
into a ``LimitSpec`` with a ``from_`` / ``to`` ``EndpointSpec``. It never guesses
geography: resolving endpoints onto a river course is the resolvers' job (T3.3).

Matching runs on a *same-length folded* copy of the text (diacritics stripped,
lower-cased, one character in -> one character out) so match spans index
straight into the original-case string and ``target`` keeps its diacritics.

Deviations from the plan table, all conservative:

* a bare watercourse endpoint (``Râul Olt``, ``Valea Fetii``) is a CONFLUENCE
  (the plan would call it a LOCALITY);
* a bare lake endpoint is LAKE_DOWNSTREAM as the *from* end and LAKE_UPSTREAM as
  the *to* end (the river enters the lake at the end of a sector);
* a hyphen directly after ``izvoare`` always separates ("Izvoare-DN 67 D ...").
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

from .textnorm import COUNTY_CODES, county_names_folded, fix_diacritics

Kind = Literal[
    "SOURCE", "MOUTH", "CONFLUENCE", "DAM", "LAKE_UPSTREAM", "LAKE_DOWNSTREAM", "BRIDGE",
    "LOCALITY", "COUNTY_LIMIT", "BORDER", "WATERFALL", "ROAD", "UNKNOWN",
]
Qualifier = Literal["at", "upstream", "downstream"]
Scope = Literal["interval", "whole_county", "whole_course", "locality_list", "empty", "unparsed"]


@dataclass(frozen=True)
class EndpointSpec:
    kind: Kind
    target: str | None = None
    qualifier: Qualifier = "at"
    locality_hint: str | None = None
    road_ref: str | None = None
    raw: str = ""


@dataclass(frozen=True)
class LimitSpec:
    scope: Scope
    from_: EndpointSpec | None = None
    to: EndpointSpec | None = None
    localities: tuple[str, ...] = ()
    county: str | None = None
    includes_tributaries: bool = False
    raw: str = ""

    def to_dict(self) -> dict:
        def ep(e: EndpointSpec | None):
            return None if e is None else {
                "kind": e.kind, "target": e.target, "qualifier": e.qualifier,
                "locality_hint": e.locality_hint, "road_ref": e.road_ref, "raw": e.raw,
            }

        return {
            "scope": self.scope, "from": ep(self.from_), "to": ep(self.to),
            "localities": list(self.localities), "county": self.county,
            "includes_tributaries": self.includes_tributaries, "raw": self.raw,
        }


# --------------------------------------------------------------------- folding


def _fold_char(ch: str) -> str:
    d = unicodedata.normalize("NFKD", ch)
    base = "".join(c for c in d if not unicodedata.combining(c))
    return (base[:1] or ch).lower()


def _fl(s: str) -> str:
    """Same-length folded copy of ``s`` (one output char per input char)."""
    return "".join(_fold_char(c) for c in s)


def _clean_target(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip(" \t,.;:-–—\"'()")
    return s


def _prep(text: str) -> str:
    s = fix_diacritics(text or "").replace(" ", " ")
    s = s.strip().strip('"').strip()
    # "loc.Slatina" -> "loc. Slatina"; keeps "D.N." readable for the road rules
    s = re.sub(r"(?<=[A-Za-zĂÂÎȘȚăâîșț]{2})\.(?=[A-Za-zĂÂÎȘȚăâîșț])", ". ", s)
    return re.sub(r"\s+", " ", s)


# ------------------------------------------------------------------- patterns

_WC = r"(?:raul|paraul|parau|piriul|pirau|pr|r|fluviul|canalul)\b\.?\s*"  # generic watercourse words
_LOCPFX = r"(?:loc|localitatea|localitate|sat|satul|com|comuna|oras|orasul|mun|municipiul|zona|intravilan)\b\.?\s*"
_COUNTRIES = r"(?:ungaria|serbia|ucraina|moldova|bulgaria)"

RE_EMPTY = re.compile(r"^[\s\-–—]*$")
RE_WHOLE_COURSE = re.compile(r"\b(?:toata lungimea|integral)\b|^cursul principal$")
RE_TRIBS = re.compile(r"(?:\b(?:si|cu)\s+(?:toti\s+)?|\+\s*)afluent")
RE_LEAD_CONNECTOR = re.compile(r"^(?:de la|intre|pana la|pana in|pina la|la)\s+")

RE_SOURCE = re.compile(r"^(?:de la )?izvo(?:r|are|arele|rul|rului|arelor)\b")
RE_VARSARE = re.compile(r"^(?:la )?(?:varsare|varsarea|virsare)\b(?:[,\s]+(?:in|la)\b)?[,\s]*")
RE_CONF = re.compile(r"^(?:la )?(?:confluenta|confluent[ae]|confl|conf)\b\.?(?:\s+cu)?\s*")
RE_GURA = re.compile(r"^gura\b\s+")
RE_LAKE_UP = re.compile(
    r"^(?:coada|intrare(?: in)?|amonte(?: de)?)\s+(?:lacului|lacul|lacu|lac|acumularea|acumulare|barajul|baraj)\b\s*"
)
RE_LAKE_DOWN = re.compile(
    r"^(?:iesire(?: din)?|aval(?: de)?)\s+(?:lacul|lacu|lac|acumularea|acumulare|barajul|baraj)\b\s*"
)
RE_DAM = re.compile(r"^(?:limita\s+)?(?:barajul|baraj)\b\s*")
RE_LAKE = re.compile(r"^(?:lacul|lacu|lac|acumularea|acumulare)\b\s*")
RE_LAKE_NAME_PFX = re.compile(r"^(?:lacului|lacul|lacu|lac)\b\s*(?:de\s+)?(?:acumulare\s+)?|^acumularea?\s+")
RE_BRIDGE = re.compile(r"^(?:pod|podul|pud)\b\.?\s*")
RE_BRIDGE_DESC = re.compile(r"^(?:rutier|cfr|auto|feroviar|de fier|fier|de ciment|ciment|vechi|mare)\b\.?\s*")
RE_ROAD_REF = re.compile(r"^(d\.?\s?n|d\.?\s?j)\.?\s*(\d+)\s*([a-z])?\b\.?\s*")
RE_ROAD_BARE = re.compile(r"^(d\.?\s?n|d\.?\s?j)\b\.?\s*")
RE_DRUM = re.compile(r"^drum\b\.?\s*")
RE_COUNTY_LIMIT = re.compile(
    r"^(?:(?:limita|limit[aă])(?:\s+de)?(?:\s+cu)?|(?:intrare|iesire)(?:\s+(?:din|in))?)\s+(?:judetului|judetul|judet|jud)\b\.?\s*"
)
RE_BORDER = re.compile(rf"^(?:(?:frontiera|granita|hotar(?:ul)?)(?:\s+cu)?(?:\s+statul)?\s*)?({_COUNTRIES})?\s*$")
RE_BORDER_PFX = re.compile(r"^(?:frontiera|granita|hotar(?:ul)?)\b(?:\s+cu)?(?:\s+statul)?\s*")
RE_WATERFALL = re.compile(r"^cascada\b\s*")
RE_QUALIFIER = re.compile(r"^(aval|amonte)(?:\s+de)?\s+")
RE_ENTRY_EXIT = re.compile(r"^(intrare|iesire)(?:\s+(?:in|din))?\s+")
RE_WATERCOURSE = re.compile(rf"^(?:{_WC}|valea\b\.?\s*|vl\b\.?\s*)")
RE_LOCALITY_PFX = re.compile(rf"^{_LOCPFX}")
RE_ISOLATED_PAREN = re.compile(r"\(([^)]*)\)")

# keywords that allow a bare hyphen to act as the from/to separator
_SPLIT_KW = (
    "conf", "pod", "baraj", "izvo", "varsare", "limit", "iesire", "intrare", "loc", "sat",
    "com", "aval", "amonte", "lac", "frontier", "granit", "virsare", "gura", "dn", "dj", "drum", "cascad",
)


def _has_inner_separator(s: str) -> bool:
    """True if a side still contains something that separates two endpoints."""
    if re.search(r"[–—]|(?:^|\s)-|-(?:\s|$)", s):
        return True
    f = _fl(s)
    return bool(re.search(r"-\s*(?:confl?|confluenta|pod|podul|baraj|barajul|izvo\w*|varsare|limita|limit|iesire|intrare)\b", f))


def _is_toponym(s: str) -> bool:
    if not s or len(s) > 60:
        return False
    if re.search(r"\d|[–—]|(?:^|\s)-(?:\s|$)|[/+]", s):
        return False
    if re.search(r",\s*(?:conf|pod|baraj|izvo|varsare)", _fl(s)):
        return False
    words = s.split()
    return 1 <= len(words) <= 7 and any(len(w) >= 3 for w in words)


# -------------------------------------------------------------- county helpers


def _match_county(rest: str) -> tuple[str | None, str]:
    """Longest county name/code at the start of ``rest`` -> (display name, remainder)."""
    table = county_names_folded()
    f = _fl(rest)
    best: tuple[int, str] | None = None
    for key, display in table.items():
        if f.startswith(key) and (len(f) == len(key) or not f[len(key)].isalpha()):
            if best is None or len(key) > best[0]:
                best = (len(key), display)
    if best is None:
        return None, rest
    return best[1], rest[best[0]:]


# ------------------------------------------------------------ classification


def _endpoint(
    raw_side: str, role: Literal["from", "to"], qualifier: Qualifier = "at"
) -> EndpointSpec:
    side = re.sub(r"\s+", " ", raw_side).strip()
    paren = RE_ISOLATED_PAREN.findall(side)
    side_np = _clean_target(RE_ISOLATED_PAREN.sub(" ", side))
    # a trailing "și afluenții" phrase is a flag of the whole text, not part of the target
    tm = RE_TRIBS.search(_fl(side_np))
    if tm:
        side_np = _clean_target(side_np[: tm.start()])
    if _has_inner_separator(side_np):
        return EndpointSpec("UNKNOWN", raw=raw_side.strip(), qualifier=qualifier)
    f = _fl(side_np)
    f = RE_LEAD_CONNECTOR.sub("", f) if RE_LEAD_CONNECTOR.match(f) else f
    # keep original-case slice aligned with the folded string
    side_np = side_np[len(side_np) - len(f):] if len(f) <= len(side_np) else side_np

    def spec(kind: Kind, target: str | None = None, **kw) -> EndpointSpec:
        t = _clean_target(target) if target else None
        return EndpointSpec(kind=kind, target=t or None, raw=raw_side.strip(), qualifier=kw.pop("qualifier", qualifier), **kw)

    def rest_after(m: re.Match) -> str:
        return side_np[m.end():]

    if not f:
        return spec("UNKNOWN")

    # --- SOURCE
    m = RE_SOURCE.match(f)
    if m and not rest_after(m).lstrip().startswith("-"):
        rem = _clean_target(RE_LOCALITY_PFX.sub("", _clean_target(rest_after(m)), count=1))
        return spec("SOURCE", None, locality_hint=rem or None)

    # --- MOUTH / CONFLUENCE through "vărsare"
    m = RE_VARSARE.match(f)
    if m:
        rem = rest_after(m)
        return _confluence_or_lake(rem, spec, mouth_if_empty=True)

    # --- CONFLUENCE ("conf.", "confl.", "confluența")
    m = RE_CONF.match(f)
    if m:
        return _confluence_or_lake(rest_after(m), spec, mouth_if_empty=False)
    m = RE_GURA.match(f)
    if m:
        return _confluence_or_lake(rest_after(m), spec, mouth_if_empty=False)

    # --- lakes / dams
    m = RE_LAKE_UP.match(f)
    if m:
        return spec("LAKE_UPSTREAM", _lake_name(rest_after(m)))
    m = RE_LAKE_DOWN.match(f)
    if m:
        return spec("LAKE_DOWNSTREAM", _lake_name(rest_after(m)))
    m = RE_DAM.match(f)
    if m:
        return spec("DAM", rest_after(m))
    m = RE_LAKE.match(f)
    if m:
        kind: Kind = "LAKE_DOWNSTREAM" if role == "from" else "LAKE_UPSTREAM"
        name = _lake_name(side_np)
        return spec(kind, name)

    # --- bridges and roads
    m = RE_BRIDGE.match(f)
    if m:
        return _bridge(side_np, m.end(), spec)
    m = RE_ROAD_REF.match(f)
    if m:
        ref = f"{m.group(1).replace('.', '').replace(' ', '').upper()} {m.group(2)}{(m.group(3) or '').upper()}"
        return spec("ROAD", None, road_ref=ref, locality_hint=_clean_target(rest_after(m)) or None)
    m = RE_ROAD_BARE.match(f)
    if m:
        return spec("ROAD", None, road_ref=m.group(1).replace(".", "").replace(" ", "").upper(),
                    locality_hint=_clean_target(rest_after(m)) or None)
    m = RE_DRUM.match(f)
    if m:
        rem = _clean_target(rest_after(m))
        first = rem.split(" ")[0] if rem else ""
        if _fl(first) in {"forestier", "national", "comunal", "judetean", "agricol"} or not first:
            return spec("ROAD", None, locality_hint=_clean_target(" ".join(rem.split(" ")[1:])) or None)
        return spec("ROAD", None, road_ref=first.rstrip(",;"), locality_hint=_clean_target(" ".join(rem.split(" ")[1:])) or None)

    # --- county limit, border, waterfall
    m = RE_COUNTY_LIMIT.match(f)
    if m:
        rest = rest_after(m)
        county, remainder = _match_county(rest)
        if county is None and paren:
            for p in paren:
                pm = re.search(r"jud(?:etul)?\.?\s*(.+)$", _fl(p))
                if pm:
                    county, _ = _match_county(p[pm.start(1):])
        hint = _clean_target(RE_LOCALITY_PFX.sub("", _clean_target(remainder), count=1))
        return spec("COUNTY_LIMIT", county, locality_hint=hint or None)
    if RE_BORDER_PFX.match(f) or RE_BORDER.match(f):
        m2 = RE_BORDER_PFX.match(f)
        country = _clean_target(rest_after(m2)) if m2 else side_np
        return spec("BORDER", country or None)
    m = RE_WATERFALL.match(f)
    if m:
        return spec("WATERFALL", rest_after(m))

    # --- aval / amonte of something
    m = RE_QUALIFIER.match(f)
    if m:
        inner = _endpoint(side_np[m.end():], role, "downstream" if m.group(1) == "aval" else "upstream")
        return EndpointSpec(inner.kind, inner.target, inner.qualifier, inner.locality_hint, inner.road_ref, raw_side.strip())
    m = RE_ENTRY_EXIT.match(f)
    if m:
        rem = _clean_target(RE_LOCALITY_PFX.sub("", rest_after(m), count=1))
        if _is_toponym(rem):
            return spec("LOCALITY", rem, qualifier="upstream" if m.group(1) == "intrare" else "downstream")

    # --- bare watercourse is a confluence
    m = RE_WATERCOURSE.match(f)
    if m and not RE_LOCALITY_PFX.match(f):
        rem = _clean_target(rest_after(m))
        words = f[m.end():].split()
        if words:
            keep_valea = f.startswith(("valea", "vl"))
            target = side_np if keep_valea else rem
            return spec("CONFLUENCE", target)

    # --- locality
    m = RE_LOCALITY_PFX.match(f)
    rem = _clean_target(side_np[m.end():]) if m else side_np
    if _is_toponym(rem):
        return spec("LOCALITY", rem)
    return spec("UNKNOWN")


def _lake_name(rem: str) -> str | None:
    rem = _clean_target(rem)
    f = _fl(rem)
    m = RE_LAKE_NAME_PFX.match(f)
    if m:
        rem = rem[m.end():]
    # "baraj lac Zetea" -> "Zetea"
    f = _fl(rem)
    m = RE_LAKE_NAME_PFX.match(f)
    if m:
        rem = rem[m.end():]
    return _clean_target(rem) or None


def _confluence_or_lake(rem: str, spec, mouth_if_empty: bool) -> EndpointSpec:
    rem = _clean_target(rem)
    f = _fl(rem)
    if not f:
        return spec("MOUTH") if mouth_if_empty else spec("UNKNOWN")
    if RE_LAKE.match(f):
        return spec("LAKE_UPSTREAM", _lake_name(rem))
    md = RE_DAM.match(f)
    if md:  # "confluența Baraj X" = the reservoir behind the dam
        return spec("LAKE_UPSTREAM", _lake_name(rem[md.end():]))
    m = re.match(rf"^{_WC}", f)
    if m:
        rem = rem[m.end():]
    return spec("CONFLUENCE", rem) if _clean_target(rem) else spec("UNKNOWN")


def _bridge(side: str, start: int, spec) -> EndpointSpec:
    rem = side[start:]
    road_ref = None
    while True:
        f = _fl(rem)
        m = RE_BRIDGE_DESC.match(f)
        if m:
            if m.group(0).strip().startswith("cfr"):
                road_ref = "CFR"
            rem = rem[m.end():]
            continue
        m = RE_ROAD_REF.match(f)
        if m:
            road_ref = f"{m.group(1).replace('.', '').replace(' ', '').upper()} {m.group(2)}{(m.group(3) or '').upper()}"
            rem = rem[m.end():]
            continue
        m = RE_ROAD_BARE.match(f)
        if m and road_ref is None:
            road_ref = m.group(1).replace(".", "").replace(" ", "").upper()
            rem = rem[m.end():]
            continue
        break
    rem = _clean_target(rem)
    f = _fl(rem)
    lead = re.match(r"^(?:din|de la|la)\s+", f)
    if lead:
        rem, f = rem[lead.end():], f[lead.end():]
    name = None
    m = re.search(r"\s(?:din|de la|la)\s+(?:(?:loc|localitatea|comuna|com|sat|satul|orasul|municipiul)\b\.?\s*)?", f)
    if m and m.start() > 0:
        name = rem[: m.start()]
        rem = rem[m.end():]
    else:
        m2 = RE_LOCALITY_PFX.match(f)
        if m2:
            rem = rem[m2.end():]
    hint = _clean_target(rem) or None
    return spec("BRIDGE", name, locality_hint=hint, road_ref=road_ref)


# ------------------------------------------------------------------ scopes


def _county_scope(f: str, text: str) -> str | None:
    """County display name if the whole text is a 'whole county' statement."""
    m = re.match(
        r"^(?:partea neamenajata\s+)?(?:pe\s+(?:raza|teritoriul)\s+)?(?:judetului|judetul|judet|jud)\b\.?\s*(.+?)\s*$", f
    )
    if m and (f.startswith(("judet", "jud")) or "pe raza" in f or "pe teritoriul" in f):
        county, rest = _match_county(text[m.start(1):])
        if county and not _clean_target(rest):
            return county
    m = re.match(r"^partea neamenajata\s+pe\s+(?:raza|teritoriul)\s+(?:judetului|judetul|jud)\b\.?\s*(.+?)\s*$", f)
    if m:
        county, rest = _match_county(text[m.start(1):])
        if county and not _clean_target(rest):
            return county
    m = re.match(
        r"^(?:intrare|limita)(?:\s+in)?\s+(?:judetul|judet|jud)\b\.?\s*(.+?)\s*[-–—]\s*(?:iesire|limita)(?:\s+din)?\s+(?:judetul|judet|jud)\b\.?\s*(.+?)\s*\.?\s*(?:fara.*)?$",
        f,
    )
    if m:
        c1, r1 = _match_county(text[m.start(1):m.end(1)])
        c2, r2 = _match_county(text[m.start(2):m.end(2)])
        if c1 and c1 == c2 and not _clean_target(r1) and not _clean_target(r2):
            return c1
    return None


_SEP_RE = re.compile(r"\s*([–—])\s*|\s+-\s+|\s-(?=\S)|(?<=\S)-\s+|(?:\s+|-)(?:pana la|pana in|pina la)\s+")


def _splits(text: str) -> list[tuple[str, str, str]]:
    """Candidate (left, right, kind) splits; kind in {'endash','hyphen','bare','connector'}."""
    f = _fl(text)
    out: list[tuple[str, str, str]] = []
    for m in _SEP_RE.finditer(f):
        tok = m.group(0)
        if m.group(1):
            kind = "endash"
        elif "pana" in tok or "pina" in tok:
            kind = "connector"
        else:
            kind = "hyphen"
        out.append((text[: m.start()], text[m.end():], kind))
    for m in re.finditer(r"(?<=[^\W\d_])-(?=[^\W\d_])", f):
        left, right = text[: m.start()], text[m.end():]
        rf = _fl(right)
        lf = _fl(left).strip()
        if rf.startswith(_SPLIT_KW) or RE_SOURCE.match(lf + " ") or re.fullmatch(r"izvo\w*", lf):
            out.append((left, right, "bare"))
    return out


_LOC_MARK = re.compile(r"\b(?:loc|localitatea)\b\.?")


def _parse_interval(text: str) -> LimitSpec | None:
    f = _fl(text)
    lead = re.match(r"^(?:de la|intre)\s+", f)
    body = text[lead.end():] if lead else text
    cands = _splits(body)
    if not cands:
        return None
    scored = []
    for left, right, kind in cands:
        if len(_LOC_MARK.findall(_fl(left))) > 1 or len(_LOC_MARK.findall(_fl(right))) > 1:
            continue
        a, b = _endpoint(left, "from"), _endpoint(right, "to")
        scored.append((kind, a, b))
    if not scored:
        return None
    valid = [c for c in scored if c[1].kind != "UNKNOWN" and c[2].kind != "UNKNOWN"]
    one_ok = [c for c in scored if not (c[1].kind == "UNKNOWN" and c[2].kind == "UNKNOWN")]
    pool = valid if valid else (one_ok if len(scored) == 1 else [])
    if not pool:
        return None
    for want in ("endash", "hyphen", "connector", "bare"):
        for kind, a, b in pool:
            if kind == want:
                return LimitSpec("interval", a, b, raw=text)
    return None  # pragma: no cover


def parse_limits(text: str, *, water_name: str = "") -> LimitSpec:
    raw = text if text is not None else ""
    s = _prep(raw)
    f = _fl(s)
    tribs = bool(RE_TRIBS.search(f))

    def done(spec: LimitSpec) -> LimitSpec:
        return spec if spec.includes_tributaries == tribs else LimitSpec(
            spec.scope, spec.from_, spec.to, spec.localities, spec.county, tribs, spec.raw
        )

    if RE_EMPTY.match(s):
        return LimitSpec("empty", raw=raw)
    county = _county_scope(f, s)
    if county:
        return done(LimitSpec("whole_county", county=county, raw=raw))
    if RE_WHOLE_COURSE.search(f):
        return done(LimitSpec("whole_course", raw=raw))
    if "," in s and not re.search(r"[–—]|(?:^|\s)-(?:\s|$)", s):
        parts = [_clean_target(p) for p in s.split(",")]
        if len(parts) >= 3 and all(_is_toponym(p) and not RE_SOURCE.match(_fl(p)) and not RE_CONF.match(_fl(p)) for p in parts):
            return done(LimitSpec("locality_list", localities=tuple(parts), raw=raw))
    iv = _parse_interval(s)
    if iv is not None:
        return done(LimitSpec("interval", iv.from_, iv.to, raw=raw))
    return done(LimitSpec("unparsed", raw=raw))


# ------------------------------------------------------------------------ CLI


def cli(argv: list[str]) -> int:
    """`python -m rivernet parse`: parse every river water's `limite`."""
    import argparse
    import json
    from collections import Counter
    from pathlib import Path

    ap = argparse.ArgumentParser(prog="rivernet parse")
    ap.add_argument("--waters", default="public/data/waters.json")
    ap.add_argument("--out-dir", default="data/sectors")
    ns = ap.parse_args(argv)

    waters = json.loads(Path(ns.waters).read_text(encoding="utf-8"))
    out = Path(ns.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scopes: Counter = Counter()
    kinds: Counter = Counter()
    bad = total = 0
    rows = []
    for w in sorted((w for w in waters if w.get("subtype") == "rau"), key=lambda w: w["slug"]):
        spec = parse_limits(w.get("limite") or "", water_name=w.get("name") or "")
        d = spec.to_dict()
        rows.append({"slug": w["slug"], "raw": w.get("limite") or "", "spec": d})
        total += 1
        scopes[spec.scope] += 1
        if spec.scope == "interval":
            for e in (spec.from_, spec.to):
                kinds[e.kind] += 1
            if "UNKNOWN" in (spec.from_.kind, spec.to.kind):
                bad += 1
        elif spec.scope == "unparsed":
            bad += 1
    with (out / "limits_parsed.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "total": total,
        "scopes": dict(sorted(scopes.items())),
        "endpointKinds": dict(sorted(kinds.items())),
        "unparsedOrUnknown": bad,
        "unparsedOrUnknownShare": round(bad / total, 4) if total else 0.0,
    }
    (out / "limits_parsed_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0
