#!/usr/bin/env python3
"""Parse association pages from locuridepescuit.ro (probe).
Extracts: name, county (from URL), contact fields, counties with contracted
waters, and the contracted-waters list.
"""
import json
import re
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup

NOISE = ("Obtineti Instructiuni deplasare", "Obțineți Instrucțiuni deplasare")


def _clean(val: str, label: str) -> str:
    for n in NOISE:
        val = val.replace(n, "")
    val = val.replace(label, "", 1)
    return " ".join(val.split()).strip()


def parse_association(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    path = urlparse(url).path.rstrip("/").split("/")
    county = path[-2] if len(path) >= 2 else None
    slug = path[-1]

    out = {
        "url": url,
        "slug": slug,
        "county_from_url": county,
        "name": soup.h1.get_text(" ", strip=True) if soup.h1 else None,
    }

    # contact fields keyed by H5 label
    for h5 in soup.find_all("h5"):
        label = h5.get_text(" ", strip=True)
        key = {
            "Adresa": "address",
            "Telefon": "phone",
            "Email": "email",
            "Website": "website",
            "Județe în care Asociația are ape contractate": "counties_contract",
        }.get(label)
        if not key:
            continue
        block = h5.find_parent("div", class_="element")
        if not block:
            continue
        val = _clean(block.get_text(" ", strip=True), label)
        if val:
            out[key] = val

    # description
    for h5 in soup.find_all("h5"):
        if h5.get_text(" ", strip=True) == "Descriere":
            block = h5.find_parent("div", class_="element")
            if block:
                out["description"] = _clean(block.get_text(" ", strip=True), "Descriere")
            break

    # contracted waters: within the main profile tab, the LAST div.listing-details
    # is the waters list (the FIRST holds counties; similar-listings section holds related cards).
    main_tab = soup.find("section", class_=re.compile(r"tab-type-main"))
    waters = []
    if main_tab:
        details_divs = main_tab.find_all("div", class_="listing-details")
        if details_divs:
            for li in details_divs[-1].find_all("li"):
                span = li.find("span", class_="category-name")
                t = (span or li).get_text(" ", strip=True)
                if t:
                    waters.append(t)
    # de-dup while preserving order
    seen, uniq = set(), []
    for w in waters:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    out["contracted_waters"] = uniq
    out["contracted_waters_count"] = len(uniq)
    return out


if __name__ == "__main__":
    pages = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    for fname, url in pages.items():
        html = open(fname, encoding="utf-8").read()
        print(json.dumps(parse_association(html, url), ensure_ascii=False, indent=2))
        print("=" * 70)
