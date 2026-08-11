#!/usr/bin/env python3
"""
ANPA contracted-waters PDF parser (canonical source) — Phase 2 of the
UndePescuim.ro data pipeline.

Parses `pdftotext -layout` output of ANPA's "Lista habitatelor acvatice
naturale contractate" and emits normalized JSONL records:

  data/processed/anpa_waters.jsonl      — one record per water section (habitat)
  data/processed/anpa_contracts.jsonl   — one record per association contract block
  data/processed/review_queue.jsonl     — rows flagged for manual review
  data/processed/sources.jsonl          — appended with a provenance row per file

Layout notes (observed in the 23.02.2026 edition):
  * `pdftotext -layout` columns:  name [0,50) | limits [50,105) | value [105,122) | assoc [122,)
  * Association blocks span multiple water rows; the block name + address sit in the
    right-hand column and "cu sediul în" marks the start of the address.
  * Water names, limits and values can wrap across lines; a row is anchored on its
    NAME line and limits/value fragments are attached to the NEAREST name line
    (ties broken by boundary-start heuristics).
  * km vs Ha units are mixed ("115 Km", "5Ha", "250 ha", "19,2 Km", "perimetral 25 km").
  * Contract numbers appear in the right column as "44/26.10.2017", occasionally
    spaced ("16 / 13. 09. 2017") or year-only ("664/598/1982"), with
    "ACT ADIȚIONAL NR. X/DD.MM.YYYY" addenda.

Run:  python3 src/pipeline/parse_anpa.py [--input PATH] [--out DIR] [--schema-version 1.0.0]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Column geometry (pdftotext -layout)
# --------------------------------------------------------------------------
NAME_SLICE = slice(0, 50)
LIMITS_SLICE = slice(50, 105)
VALUE_MIN_COL = 100
ASSOC_SLICE = slice(122, None)

# --------------------------------------------------------------------------
# Noise / structural patterns
# --------------------------------------------------------------------------
NOISE_RE = re.compile(
    r"^(?:"
    r"MINISTERUL AGRICULTURII|"
    r"Agenția Națională pentru Pescuit și Acvacultură|"
    r"Agenţia Naţională pentru Pescuit şi Acvacultură|"
    r"str\. Sf|"
    r"telefon:|"
    r"email:|"
    r"www\.anpa|"
    r"\d+\s*$"
    r")"
)
COUNTY_RE = re.compile(r"^JUDEȚ(?:UL)?\s+(.+)$", re.I)
COUNTY_MIN_COL = 70

# --------------------------------------------------------------------------
# Values
# --------------------------------------------------------------------------
VALUE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(km|ha)", re.I)


def value_on_line(line: str):
    """Last km/Ha match whose start column is in the value zone (>= 100)."""
    best = None
    for m in VALUE_RE.finditer(line):
        if m.start() >= VALUE_MIN_COL:
            best = m
    if best is None:
        return None
    raw, unit = best.group(1), best.group(2).lower()
    try:
        num = float(raw.replace(",", "."))
    except ValueError:
        return None
    return num, unit, best.group(0).strip()


# --------------------------------------------------------------------------
# Contracts & addenda (right column)
# --------------------------------------------------------------------------
CONTRACT_RE = re.compile(
    r"(\d+(?:/\d+)*)\s*/\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})"
)
# year-only contract numbers, e.g. "664/598/1982"
CONTRACT_YEAR_RE = re.compile(r"(\d+/\d+)/(\d{4})\b")
ADDENDUM_RE = re.compile(
    r"(?:NR\.?|Nr\.?)\s*(\d+(?:/\d+)*)\s*/\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})"
)
UNKNOWN_ASSOC = "(unknown association)"


def iso_date(dd, mm, yyyy):
    try:
        return datetime(int(yyyy), int(mm), int(dd)).strftime("%Y-%m-%d")
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Association name detection (right column)
# --------------------------------------------------------------------------
ASSOC_PREFIX_RE = re.compile(r"^(AJVPS|AVPS|AJPS|APS|CS|AV|ASOCIA|Asocia|A\.)")

# --------------------------------------------------------------------------
# Water rows: continuation vs new-row heuristics
# --------------------------------------------------------------------------
WATER_PREFIX_RE = re.compile(
    r"^(?:Râul|Raul|Lacul|Lac|Balta|Bălțile|Baltile|Valea|Văile|Pârâul|Parâul|Pârâu|"
    r"Canalul|Canal|Canalele|Acumularea|Acumulare|Japșa|Japsa|Gârla|Garla|Prut|Topa|"
    r"Rețeaua|Reteaua|Fondul|Baraj|Brațele|Bratul|Izvorul|Dunărea|Dunarea)",
    re.I,
)
# open-row name endings that clearly need a continuation fragment
CONNECTOR_END_RE = re.compile(
    r"(?:"
    r"cu afluenții săi$|cu afluenţii săi$|cu afluenții$|cu afluenţii$|"
    r"cu bălțile$|cu bălţile$|bălțile$|bălţile$|"
    r"afluenții$|afluenţii$|afluenții săi$|afluenţii săi$|adiacente$|"
    r"de acumulare$|acumulare\s*$|cu$|și$|si$|de$|ale$|ale Râului$|ale Raului$|"
    r"Rasa și$|Rasa si$|include\s*$|braț mort\s+\w+$|braţ mort\s+\w+$|"
    r"Someșul$|Somesul$|Mureșul$|Muresul$|Oltul$|"
    r"si Valea$|și Valea$|Valea\s*$|,\s*$|pâraiele\s*$|pîraiele\s*$"
    r")$",
    re.I,
)
# boundary-start phrases: a limits fragment starting with these on a tie
# belongs to the NEXT name line
BOUNDARY_START_RE = re.compile(
    r"^(?:Izvoare|izvoare|Aval|aval|Comuna|comuna|Limita|limita|Limită|limită|"
    r"Conf\.|conf\. cu|de la|Pe raza|la izvoare|La izvoare|"
    r"între|Intre|granița|Granita|zona|Zona|lângă|Langă|același|Același|"
    r"canal de|Canal de|Amonte|amonte|râul Moldova|raul Moldova|paralel|"
    r"mal stâng|Mal stâng|"
    r"cu afluenții|cu afluenţii|cu bălțile|cu bălţile)",
)

# --------------------------------------------------------------------------
# Water type mapping from name prefix
# --------------------------------------------------------------------------
WATER_TYPE_RULES = [
    (re.compile(r"^(?:Lac|Lacul)\s+acumulare|^(?:Acumulare|Acumularea)"), "accumulation"),
    (re.compile(r"^(?:Râul|Raul)"), "river"),
    (re.compile(r"^(?:Lac|Lacul)"), "lake"),
    (re.compile(r"^(?:Canal|Canalul|Canalele|Rețeaua|Reteaua)"), "canal"),
    (re.compile(r"^(?:Pârâul|Parâul|Pârâu|Valea|Văile|Izvorul|Prut)"), "stream"),
    (re.compile(r"^(?:Balta|Bălțile|Baltile|Japșa|Japsa|Gârla|Garla|Topa|Doaga|Glăjărie|Năruja|Mihoești|Dopca)"), "pond"),
]


def water_type(name: str) -> str:
    for rx, wt in WATER_TYPE_RULES:
        if rx.search(name):
            return wt
    return "other"


# --------------------------------------------------------------------------
# Name normalization (ASCII fold, lowercase, whitespace collapse)
# --------------------------------------------------------------------------
def ascii_fold(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def name_normalized(text: str) -> str:
    return re.sub(r"\s+", " ", ascii_fold(text).lower()).strip()


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", ascii_fold(text).lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


# --------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------
class Row:
    __slots__ = ("idx", "county", "name", "own_limits", "value", "value_raw",
                 "block", "contract", "contract_date", "act_aditional", "flags")

    def __init__(self, idx, county, name):
        self.idx = idx
        self.county = county
        self.name = name
        self.own_limits = []          # (line_idx, text) attached to this row
        self.value = None             # (number, unit)
        self.value_raw = None
        self.block = None             # Block
        self.contract = None
        self.contract_date = None
        self.act_aditional = None
        self.flags = []


class Block:
    __slots__ = ("start_idx", "county", "name", "address", "contracts", "addenda")

    def __init__(self, start_idx, county, name):
        self.start_idx = start_idx
        self.county = county
        self.name = name
        self.address = ""
        self.contracts = []           # (line_idx, number, date)
        self.addenda = []             # (line_idx, number)


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------
class AnpaParser:
    def __init__(self):
        self.rows = []
        self.limits_frags = []        # (line_idx, text)
        self.value_frags = []         # (line_idx, number, unit, raw, limits_text)
        self.blocks = []
        self.counties = []            # ordered county names seen
        self.cur_county = None
        self.cur_block = None         # Block currently being assembled
        self.in_address = False
        self.address_frags = []
        self.addendum_pending = False

    # -- right-column handling -------------------------------------------
    def start_block(self, idx: int, name_frag: str):
        self.cur_block = Block(idx, self.cur_county, name_frag)
        self.blocks.append(self.cur_block)
        self.in_address = False
        self.address_frags = []

    def process_assoc(self, idx: int, assoc_text: str):
        if not assoc_text:
            return
        text = assoc_text

        # "cu sediul în" finalizes the association name and starts the address
        if "cu sediul" in text:
            if self.cur_block is None:
                self.start_block(idx, UNKNOWN_ASSOC)
            self.in_address = True
            self.address_frags = []
            text = re.sub(r"cu sediul\s+[îi]n", "", text).strip()

        # addenda: "ACT ADIȚIONAL" then "NR. X/DD.MM.YYYY"
        if "ADITIONAL" in text.upper().replace("Ț", "T").replace("Ţ", "T"):
            self.addendum_pending = True
            text = re.sub(r"ACT\s+ADI[ȚT]IONAL", "", text, flags=re.I).strip()
        addendum_token = None
        if self.addendum_pending:
            m = ADDENDUM_RE.search(text)
            if m:
                addendum_token = f"{m.group(1)}/{m.group(2)}.{m.group(3)}.{m.group(4)}"
                text = ADDENDUM_RE.sub("", text).strip()
                self.addendum_pending = False

        # pull contract tokens out FIRST so the association name stays clean
        # (a new block may start on the same line, e.g. "AJVPS BACĂU 33/11.10.2017")
        contract_tokens = []
        m = CONTRACT_RE.search(text)
        if m:
            num = f"{m.group(1)}/{m.group(2)}.{m.group(3)}.{m.group(4)}"
            date = iso_date(m.group(2), m.group(3), m.group(4))
            contract_tokens.append((num, date))
            text = text[: m.start()] + text[m.end():]
        else:
            my = CONTRACT_YEAR_RE.search(text)
            if my:
                num = f"{my.group(1)}/{my.group(2)}"
                contract_tokens.append((num, None))
                text = text[: my.start()] + text[my.end():]
        text = re.sub(r"\s+", " ", text).strip()

        # association name / address / name continuation
        if ASSOC_PREFIX_RE.match(text):
            if self.cur_block is None:
                self.start_block(idx, text)
            elif self.cur_block.name == UNKNOWN_ASSOC:
                self.cur_block.name = text
                self.cur_block.start_idx = idx
            elif not self.in_address:
                # multi-line association name ("AJVPS MIERCUREA-" + "CIUC")
                self.cur_block.name = (self.cur_block.name + " " + text).strip()
            else:
                self.start_block(idx, text)
        elif text and self.in_address:
            self.address_frags.append(text)
            if self.cur_block is not None:
                self.cur_block.address = " ".join(self.address_frags).strip()
        elif text:
            # non-prefix continuation of the association name (e.g. "ARAD", "SEVERIN")
            if self.cur_block is not None and len(text) > 1:
                self.cur_block.name = (self.cur_block.name + " " + text).strip()

        # attach contract/addendum tokens to the (possibly new) block
        if addendum_token is not None:
            if self.cur_block is None:
                self.start_block(idx, UNKNOWN_ASSOC)
            self.cur_block.addenda.append((idx, addendum_token))
        for num, date in contract_tokens:
            if self.cur_block is None:
                self.start_block(idx, UNKNOWN_ASSOC)
            self.cur_block.contracts.append((idx, num, date))

    # -- main loop ---------------------------------------------------------
    def parse(self, lines):
        for idx, raw in enumerate(lines):
            line = raw.replace("\f", "").rstrip("\r\n")
            if not line.strip():
                continue

            # county header
            head = line.strip()
            cm = COUNTY_RE.match(head)
            if cm:
                col = line.find("JUDEȚ")
                if col >= COUNTY_MIN_COL:
                    self.cur_county = cm.group(1).strip()
                    if self.cur_county not in self.counties:
                        self.counties.append(self.cur_county)
                    self.cur_block = None
                    self.in_address = False
                    self.address_frags = []
                    self.addendum_pending = False
                    continue

            # noise (footer, page header, title block)
            if NOISE_RE.match(line.strip()):
                continue
            if self.cur_county is None:
                continue

            assoc_text = line[ASSOC_SLICE].strip()
            self.process_assoc(idx, assoc_text)

            name = line[NAME_SLICE].strip()
            lim = line[LIMITS_SLICE].strip()
            v = value_on_line(line)

            if name:
                # skip placeholder rows (e.g. Mehedinți's "  -  -  -  - " row)
                if name.strip("-").strip() == "":
                    continue
                if self.is_name_continuation(name):
                    row = self.rows[-1]
                    row.name = (row.name + " " + name).strip()
                    if lim:
                        row.own_limits.append((idx, lim))
                    if v and row.value is None:
                        row.value = v[:2]
                        row.value_raw = v[2]
                else:
                    row = Row(idx, self.cur_county, name)
                    self.rows.append(row)
                    if lim:
                        row.own_limits.append((idx, lim))
                    if v:
                        row.value = v[:2]
                        row.value_raw = v[2]
            else:
                if lim:
                    self.limits_frags.append((idx, lim))
                if v:
                    self.value_frags.append((idx, v[0], v[1], v[2], lim))

        return self

    def is_name_continuation(self, name_text: str) -> bool:
        if not self.rows or self.rows[-1].county != self.cur_county:
            return False
        open_row = self.rows[-1]
        nm = open_row.name
        # special composite row: "Fondul piscicol 24 Ciceu: include <streams>"
        # component lines carry an inline km marker ("Pârâul Tekero – 5 km,")
        if nm.lower().startswith("fondul piscicol") and re.search(r"\d", name_text):
            return True
        # continuation fragments never start with a capital water-type word
        if name_text[0].islower():
            # "pâraiele Boia Mare" is a proper (lowercase-styled) water name,
            # but "pâraiele Uria și Murgoci" continues "Valea Urii cu"
            if re.match(r"p[âî]raiele\b", name_text, re.I) and not CONNECTOR_END_RE.search(nm):
                return False
            return True
        # a fresh water name always starts a new row
        if re.match(WATER_PREFIX_RE, name_text):
            return False
        if CONNECTOR_END_RE.search(nm):
            return True
        words = name_text.split()
        if len(words) == 1 and open_row.value is None:
            return True
        return False

    # -- pass 2: fragment assignment --------------------------------------
    def nearest(self, ln_idx):
        """Return (nearest_row, prev_candidate, next_candidate) for a fragment.

        prev_candidate/next_candidate are non-None only when there is a tie
        between a name line before and a name line after the fragment.
        """
        if not self.rows:
            return None, None, None
        dmin = min(abs(r.idx - ln_idx) for r in self.rows)
        ties = [r for r in self.rows if abs(r.idx - ln_idx) == dmin]
        prev_c = [r for r in ties if r.idx < ln_idx]
        next_c = [r for r in ties if r.idx > ln_idx]
        return ties[0], (prev_c[-1] if prev_c else None), (next_c[0] if next_c else None)

    @staticmethod
    def pick_side(prev_c, next_c, text):
        if prev_c and next_c:
            # tie: boundary-start phrases belong to the NEXT name line
            return next_c if BOUNDARY_START_RE.match(text) else prev_c
        return next_c if next_c else prev_c

    def assemble(self):
        # limits fragments
        for ln_idx, text in self.limits_frags:
            row, prev_c, next_c = self.nearest(ln_idx)
            if row is None:
                continue
            row = self.pick_side(prev_c, next_c, text)
            row.own_limits.append((ln_idx, text))

        # value fragments (tie-break follows the line's limits text when present)
        for ln_idx, num, unit, raw, lim_text in self.value_frags:
            row, prev_c, next_c = self.nearest(ln_idx)
            if row is None:
                continue
            boundary = lim_text if lim_text else raw
            row = self.pick_side(prev_c, next_c, boundary)
            if row.value is None:
                row.value = (num, unit)
                row.value_raw = raw
            else:
                # row already has a value (multi-sector habitats: Someș, Putna)
                if abs(row.value[0] - num) > 0.001:
                    row.flags.append("multi_sector_value")

        # sort each row's limits fragments by line order
        for r in self.rows:
            r.own_limits.sort(key=lambda t: t[0])

        # assign blocks & contracts
        for r in self.rows:
            county_blocks = [b for b in self.blocks if b.county == r.county]
            if not county_blocks:
                r.flags.append("no_association_block")
                continue
            prev = [b for b in county_blocks if b.start_idx <= r.idx]
            block = prev[-1] if prev else county_blocks[0]
            r.block = block
            before = [c for c in block.contracts if c[0] <= r.idx]
            if before:
                r.contract, r.contract_date = before[-1][1], before[-1][2]
            elif block.contracts:
                r.contract, r.contract_date = block.contracts[0][1], block.contracts[0][2]
            else:
                r.flags.append("no_contract_number")
            if block.addenda:
                ab = [a for a in block.addenda if a[0] <= r.idx]
                r.act_aditional = (ab[-1] if ab else block.addenda[0])[1]

        return self

    # -- output helpers -----------------------------------------------------
    def limits_text(self, row: Row) -> str:
        parts = [t for _, t in row.own_limits]
        text = re.sub(r"\s+", " ", " ".join(parts)).strip()
        text = re.sub(r"\s+([),])", r"\1", text)
        text = re.sub(r"\(\s+", "(", text)
        return text


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def county_lookup():
    """Load counties.json (from the repo) into {name_ascii_lower: id}."""
    path = Path(__file__).resolve().parents[2] / "data" / "raw" / "counties.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {c["name_ascii"].lower(): c["id"] for c in data}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


# --------------------------------------------------------------------------
# PDF-geometry block overlay (authoritative block boundaries)
#
# The text layer alone cannot locate block boundaries reliably: the
# association NAME text can sit mid-cell (e.g. "AJVPS BACĂU" at y=179.1 while
# its merged cell starts at y=124.1 with Râul Bistrița). The PDF's table cell
# geometry is the source of truth. pymupdf (optional dependency) extracts the
# merged association cells; the text parser keeps doing names/limits/values
# and contract detection, and this overlay re-assigns row -> block.
# --------------------------------------------------------------------------
ROW_HEIGHT_THRESHOLD = 1.5  # empty cell taller than 1.5x a row = continuation


def pdf_row_blocks(pdf_path):
    """Return {county: [(name_normalized, block_name_or_None), ...]} in document
    order, derived from the PDF's table cell geometry.

    A row is assigned the block of the association cell whose y-range contains
    the row's y-center. Empty cells that span >=2 rows are cross-page/continued
    cells (same block). An empty single-row cell (or no cell) = orphan -> None.
    Returns None when pymupdf is unavailable.
    """
    try:
        import pymupdf  # optional
    except ImportError:
        return None

    doc = pymupdf.open(pdf_path)
    county_rows = {}
    cur_county = None
    cur_block = None

    for pno in range(doc.page_count):
        page = doc[pno]
        tabs = page.find_tables()
        if not tabs.tables:
            continue
        t = tabs.tables[0]
        ext = t.extract()
        rows = t.rows

        # collect assoc-column cells: (y0, y1, text) for cells with x0 > 540
        assoc_cells = []
        for ri, row in enumerate(rows):
            for c in row.cells:
                if c is None or c[0] <= 540:
                    continue
                txt = ''
                if len(ext[ri]) > 3 and ext[ri][3]:
                    txt = " ".join(str(ext[ri][3]).split())
                assoc_cells.append((c[1], c[3], txt))
        # dedupe identical y-spans
        seen = set()
        uniq = []
        for y0, y1, txt in assoc_cells:
            key = (round(y0, 1), round(y1, 1))
            if key in seen:
                continue
            seen.add(key)
            uniq.append((y0, y1, txt))
        assoc_cells = uniq

        # per-row centers for the tall-cell heuristic
        row_centers = []
        for ri, row in enumerate(rows):
            ok = [c for c in row.cells if c is not None]
            if not ok:
                row_centers.append(None)
                continue
            yc = (row.bbox[1] + row.bbox[3]) / 2
            row_centers.append(yc)

        for ri, row in enumerate(rows):
            ok = [c for c in row.cells if c is not None]
            if not ok:
                continue
            name = " ".join((ext[ri][0] or "").split()) if len(ext[ri]) > 0 else ""
            if not name:
                continue
            cm = COUNTY_RE.match(name)
            if cm:
                cur_county = cm.group(1).strip()
                cur_block = None
                continue
            if name.strip("-").strip() == "":
                continue
            yc = row_centers[ri]
            if yc is None:
                continue

            covering = [c for c in assoc_cells if c[0] - 0.5 <= yc <= c[1] + 0.5]
            if covering:
                named = [c for c in covering if block_name_of(c[2])]
                if named:
                    cur_block = block_name_of(named[0][2])
                else:
                    # empty cell: tall -> continuation; single-row -> orphan
                    tall = any(
                        (c[1] - c[0]) > 2.0 * (row.bbox[3] - row.bbox[1])
                        for c in covering
                    )
                    if not tall:
                        cur_block = None
            else:
                cur_block = None

            if cur_county is None:
                continue
            county_rows.setdefault(cur_county, []).append(
                (name_normalized(name), cur_block)
            )

    return county_rows


def apply_pdf_blocks(rows, blocks, pdf_map):
    """Override row->block assignment using the PDF-authoritative map.

    Walks each county's rows in document order, matching by normalized name
    (with a small lookahead for rows the text parser merged). Sets r.block to
    the parser's Block whose normalized name matches, or None for orphans.
    Re-resolves contract/addendum from the (possibly new) block.
    """
    from collections import defaultdict

    by_county = defaultdict(list)
    for r in rows:
        by_county[r.county].append(r)
    blocks_by_county = defaultdict(list)
    for b in blocks:
        blocks_by_county[b.county].append(b)

    for county, pdf_rows in pdf_map.items():
        county_blocks = blocks_by_county.get(county, [])
        if not county_blocks:
            continue

        block_by_name = {}
        for b in county_blocks:
            key = name_normalized(b.name)
            block_by_name.setdefault(key, b)

        pr = by_county.get(county, [])
        j = 0
        for r in pr:
            rn = name_normalized(r.name)
            # find the matching pdf row starting at j (or the next few rows
            # that the text parser may have merged)
            matched = None
            k = j
            while k < len(pdf_rows) and k < j + 3:
                pdf_name, pdf_block = pdf_rows[k]
                if pdf_name == rn:
                    matched = pdf_rows[k]
                    j = k + 1
                    break
                k += 1
            if matched is None:
                # merged row: rn may be pdf_name + ' ' + pdf_name_next
                if (
                    j + 1 < len(pdf_rows)
                    and rn.startswith(pdf_rows[j][0])
                    and rn.endswith(pdf_rows[j + 1][0])
                ):
                    matched = pdf_rows[j]
                    j += 2
                else:
                    # keep text-heuristic block but flag
                    r.flags.append("pdf_row_unmatched")
                    continue

            _, pdf_block = matched
            if pdf_block is None:
                r.block = None
                r.contract = None
                r.contract_date = None
                r.act_aditional = None
                if "no_association_block" not in r.flags:
                    r.flags.append("no_association_block")
                continue

            b = block_by_name.get(name_normalized(pdf_block))
            if b is None:
                r.flags.append("pdf_block_unmatched")
                continue
            r.block = b
            # re-resolve contract & addendum from the new block
            before = [c for c in b.contracts if c[0] <= r.idx]
            if before:
                r.contract, r.contract_date = before[-1][1], before[-1][2]
            elif b.contracts:
                r.contract, r.contract_date = b.contracts[0][1], b.contracts[0][2]
            else:
                r.contract, r.contract_date = None, None
                if "no_contract_number" not in r.flags:
                    r.flags.append("no_contract_number")
            if b.addenda:
                ab = [a for a in b.addenda if a[0] <= r.idx]
                r.act_aditional = (ab[-1] if ab else b.addenda[0])[1]
            else:
                r.act_aditional = None
    return rows


def block_name_of(text):
    """Association name from a cell's text (strip address after 'cu sediul')."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    nm = t.split("cu sediul")[0].strip()
    if ASSOC_PREFIX_RE.match(nm):
        return nm
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Parse ANPA contracted-waters PDF text.")
    ap.add_argument("--input", default=None, help="pdftotext -layout txt file")
    ap.add_argument("--out", default=None, help="output directory (default data/processed)")
    ap.add_argument("--schema-version", default="1.0.0")
    args = ap.parse_args(argv)

    repo = Path(__file__).resolve().parents[2]
    default_input = (
        repo
        / "data/raw/anpa_probe/Lista-habitatelor-acvatice-naturale-contractate-23.02.2026.txt"
    )
    src = Path(args.input) if args.input else default_input
    out_dir = Path(args.out) if args.out else repo / "data/processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    county_ids = county_lookup()
    # split on newline only — splitlines() would split on formfeeds and
    # shift source_row references by the number of page breaks
    lines = src.read_text(encoding="utf-8").split("\n")

    parser = AnpaParser().parse(lines).assemble()

    county_id_of = {}
    for c in parser.counties:
        cid = county_ids.get(name_normalized(c))
        county_id_of[c] = cid or slugify(name_normalized(c))

    ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    schema_version = args.schema_version
    fname = src.name

    # ---------------- waters ----------------
    waters_out = out_dir / "anpa_waters.jsonl"
    rows = parser.rows
    with waters_out.open("w", encoding="utf-8") as f:
        for i, r in enumerate(rows):
            assoc = r.block.name if r.block else None
            if assoc:
                assoc = re.sub(r"-\s+", "-", assoc)
            rec = {
                "id": f"anpa-{i + 1:04d}",
                "source": "anpa",
                "file": fname,
                "source_row": r.idx + 1,
                "county": r.county,
                "county_id": county_id_of.get(r.county),
                "association": assoc,
                "water_name": r.name,
                "name_normalized": name_normalized(r.name),
                "water_type": water_type(r.name),
                "limits_text": parser.limits_text(r),
                "sector_km": r.value[0] if r.value and r.value[1] == "km" else None,
                "sector_ha": r.value[0] if r.value and r.value[1] == "ha" else None,
                "sector_unit": r.value[1] if r.value else None,
                "sector_raw": r.value_raw,
                "contract_number": r.contract,
                "contract_date": r.contract_date,
                "act_aditional": r.act_aditional,
                "is_contracted": True,
                "flags": sorted(set(r.flags)),
            }
            if not rec["sector_unit"]:
                rec["flags"].append("missing_value")
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---------------- contracts (association blocks) ----------------
    contracts_out = out_dir / "anpa_contracts.jsonl"
    with contracts_out.open("w", encoding="utf-8") as f:
        for bi, b in enumerate(parser.blocks):
            water_ids = [f"anpa-{i + 1:04d}" for i, r in enumerate(rows) if r.block is b]
            rec = {
                "id": f"anpa-c{bi + 1:03d}",
                "source": "anpa",
                "file": fname,
                "source_row": b.start_idx + 1,
                "county": b.county,
                "county_id": county_id_of.get(b.county),
                "association": re.sub(r"-\s+", "-", b.name),
                "name_normalized": name_normalized(b.name),
                "address": b.address or None,
                "contracts": [{"contract_number": c[1], "contract_date": c[2]} for c in b.contracts],
                "act_aditional": [a[1] for a in b.addenda] or None,
                "water_count": len(water_ids),
                "water_ids": water_ids,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---------------- review queue ----------------
    review_out = out_dir / "review_queue.jsonl"
    with review_out.open("w", encoding="utf-8") as f:
        for i, r in enumerate(rows):
            flags = set(r.flags)
            if not r.value:
                flags.add("missing_value")
            if not flags:
                continue
            rec = {
                "id": f"anpa-{i + 1:04d}",
                "source_row": r.idx + 1,
                "county": r.county,
                "water_name": r.name,
                "limits_text": parser.limits_text(r),
                "flags": sorted(flags),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---------------- sources.jsonl (append) ----------------
    sources_out = out_dir / "sources.jsonl"
    src_date = None
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", fname)
    if m:
        src_date = iso_date(m.group(1), m.group(2), m.group(3))
    src_rec = {
        "id": str(uuid.uuid4()),
        "source_name": "anpa",
        "raw_file_path": f"data/raw/anpa_probe/{fname}",
        "raw_file_url": None,
        "source_date": src_date,
        "ingested_at": ingested_at,
        "record_count": len(rows),
        "schema_version": schema_version,
    }
    existing = sources_out.read_text(encoding="utf-8").strip() if sources_out.exists() else ""
    with sources_out.open("a", encoding="utf-8") as f:
        if existing:
            f.write("\n")
        f.write(json.dumps(src_rec, ensure_ascii=False) + "\n")

    # ---------------- validation report ----------------
    report = validate(parser, rows)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def validate(parser, rows):
    counties_with_rows = {}
    n_km = n_ha = 0
    for r in rows:
        counties_with_rows[r.county] = counties_with_rows.get(r.county, 0) + 1
        if r.value and r.value[1] == "km":
            n_km += r.value[0]
        elif r.value and r.value[1] == "ha":
            n_ha += r.value[0]
    return {
        "county_headers": len(parser.counties),
        "counties_with_rows": len(counties_with_rows),
        "water_rows": len(rows),
        "km_rows": sum(1 for r in rows if r.value and r.value[1] == "km"),
        "ha_rows": sum(1 for r in rows if r.value and r.value[1] == "ha"),
        "total_km": round(n_km, 2),
        "total_ha": round(n_ha, 2),
        "rows_missing_value": sum(1 for r in rows if not r.value),
        "association_blocks": len(parser.blocks),
        "rows_with_contract": sum(1 for r in rows if r.contract),
        "rows_flagged": sum(1 for r in rows if r.flags),
        "counties_detail": counties_with_rows,
    }


if __name__ == "__main__":
    report = main()
    sys.exit(0 if isinstance(report, dict) else 1)
