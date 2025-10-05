#!/usr/bin/env python3
import os, json, re
from bs4 import BeautifulSoup

# Directories to scan for HTML files (add more as needed)
SCAN_DIRS = ["."]
EXCLUDE = {"assets", "data", ".git", ".github"}

def html_files():
    for root in SCAN_DIRS:
        for d, subdirs, files in os.walk(root):
            # skip excluded folders
            parts = set(os.path.normpath(d).split(os.sep))
            if parts & EXCLUDE:
                continue
            for f in files:
                if f.endswith(".html"):
                    path = os.path.join(d, f)
                    # Normalize URL-ish path for GitHub Pages
                    url = path.lstrip("./")
                    yield path, "/" + url

def extract_text(html):
    # remove scripts/styles
    for tag in html(["script", "style", "noscript"]):
        tag.decompose()
    text = html.get_text(" ", strip=True)
    # collapse whitespace
    return re.sub(r"\s+", " ", text)

def record_from_html(path, url):
    with open(path, "r", encoding="utf-8") as fh:
        soup = BeautifulSoup(fh.read(), "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else os.path.basename(path))
    # meta description if present
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    # collect headings & paragraph text (optional but helpful)
    headings = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(re.compile("^h[1-6]$")))
    paras = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
    content = " ".join(x for x in [desc, headings, paras] if x)
    if not content:
        content = extract_text(soup)
    return {
        "title": title,
        "url": url,
        "content": content,
        "tags": []  # add your own tags if useful
    }

records = [record_from_html(p, u) for p, u in html_files()]
os.makedirs("data", exist_ok=True)
with open("data/search.json", "w", encoding="utf-8") as out:
    json.dump(records, out, ensure_ascii=False, indent=2)

print(f"Wrote {len(records)} records to data/search.json")
