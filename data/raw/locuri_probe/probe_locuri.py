#!/usr/bin/env python3
"""Recon probe for https://locuridepescuit.ro/ape-contractate

Fetches the main listing + pagination pages, saves raw HTML, and prints a
structural summary (associations, counties, waters, sector km, pagination).
Not the full scraper -- just reconnaissance.
"""
import os
import re
import sys
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests as cr

BASE = "https://locuridepescuit.ro"
START = BASE + "/ape-contractate"
OUT_DIR = "/home/stefan/undepescuim/data/raw/locuri_probe"
os.makedirs(OUT_DIR, exist_ok=True)

# NOTE: site serves a wildcard cert (*.locuridepescuit.ro) which does NOT cover
# the apex hostname, and it 301s www->apex. So verification must be disabled.
SESSION = cr.Session(impersonate="chrome", verify=False, timeout=30)


def fetch(url: str) -> str:
    r = SESSION.get(url, allow_redirects=True)
    print(f"[fetch] {r.status_code} {r.url} len={len(r.content)}", file=sys.stderr)
    r.raise_for_status()
    return r.text


def save_raw(name: str, html: str) -> str:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[saved] {path}", file=sys.stderr)
    return path


def main():
    html = fetch(START)
    save_raw("ape-contractate_p1.html", html)
    soup = BeautifulSoup(html, "html.parser")

    # ---- general page structure ----
    print("TITLE:", soup.title.get_text(strip=True) if soup.title else None)
    # find heading hierarchy
    for h in soup.find_all(["h1", "h2", "h3"])[:20]:
        t = h.get_text(" ", strip=True)
        if t:
            print(f"  {h.name}: {t[:120]}")

    # ---- links: pagination / county / association ----
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        txt = a.get_text(" ", strip=True)
        key = (href, txt)
        links[key] = links.get(key, 0) + 1
    print(f"\nTOTAL <a> tags: {len(soup.find_all('a', href=True))}")

    # candidate pagination
    pag = [f"{txt!r} -> {href}" for (href, txt), n in sorted(links.items(), key=lambda x: -x[1])[:10]]
    print("TOP LINKS BY COUNT:")
    for p in pag:
        print("   ", p)

    # look for obvious pagination patterns
    pag_links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        txt = a.get_text(strip=True)
        if re.search(r"page|pagina|\?p=", href, re.I) or re.fullmatch(r"\d+", txt) or txt.lower() in ("next", "next ›", "următoarea", "»"):
            pag_links.add((txt, href))
    print("\nPAGINATION-LIKE LINKS:")
    for txt, href in sorted(pag_links)[:40]:
        print(f"   {txt!r} -> {href}")

    # look for county links (judet)
    county_links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        txt = a.get_text(strip=True)
        if re.search(r"judet|county", href + " " + txt, re.I):
            county_links.add((txt, href))
    print(f"\nCOUNTY-LIKE LINKS ({len(county_links)}):")
    for txt, href in sorted(county_links)[:30]:
        print(f"   {txt!r} -> {href}")

    # ---- candidate listing containers ----
    print("\nTAG COUNTS:", {t.name: len(soup.find_all(t.name)) for t in soup.find_all(["table", "article", "li", "div"], limit=0)})


if __name__ == "__main__":
    main()
