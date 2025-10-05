#!/usr/bin/env python3
import os, json, re
from bs4 import BeautifulSoup

# What to scan
HTML_DIRS = ["."]
TXT_DIR = "data"  # index .txt files inside data/

# Exclusions for the HTML crawl (we still want to read TXT in data/)
EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__"}

def should_exclude(path):
    parts = set(os.path.normpath(path).split(os.sep))
    return bool(parts & EXCLUDE_DIRS)

def iter_html_files():
    for root in HTML_DIRS:
        for d, _, files in os.walk(root):
            if should_exclude(d):
                continue
            for f in files:
                if f.lower().endswith(".html"):
                    path = os.path.join(d, f)
                    # Use relative URL (no leading slash) so project Pages work
                    url = path.lstrip("./")
                    yield path, url

def iter_txt_files():
    if not os.path.isdir(TXT_DIR):
        return
    for d, _, files in os.walk(TXT_DIR):
        for f in files:
            if f.lower().endswith(".txt"):
                path = os.path.join(d, f)
                url = path.replace("\\", "/").lstrip("./")
                yield path, url

def extract_text_from_html(html_soup):
    for tag in html_soup(["script", "style", "noscript"]):
        tag.decompose()
    text = html_soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)

def record_from_html(path, url):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        soup = BeautifulSoup(fh.read(), "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else os.path.basename(path)

    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = (desc_tag.get("content") or "").strip() if desc_tag else ""

    headings = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(re.compile(r"^h[1-6]$")))
    paras = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))

    content = " ".join(x for x in [desc, headings, paras] if x) or extract_text_from_html(soup)

    tags = []
    cl = content.lower()
    for key, tag in [("sporulation","sporulation"), ("yb955","YB955"), ("mfd","Mfd")]:
        if key in cl: tags.append(tag)

    return {"title": title, "url": url, "content": content, "tags": tags}

def record_from_txt(path, url):
    # Title based on filename
    title = os.path.basename(path).replace("_", " ")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except Exception as e:
        text = f"(Could not read file: {e})"

    # Keep the index small; store a preview but searchable
    content = re.sub(r"\s+", " ", text).strip()
    if len(content) > 20000:  # cap to 20k chars to avoid huge JSON
        content = content[:20000]

    tags = []
    cl = content.lower()
    for key, tag in [("sporulation","sporulation"), ("yb955","YB955"), ("mfd","Mfd")]:
        if key in cl: tags.append(tag)

    return {"title": title, "url": url, "content": content, "tags": tags}

def main():
    records = []

    # HTML pages (index + assets/*.html, etc.)
    for p, u in iter_html_files():
        rec = record_from_html(p, u)
        records.append(rec)

    # TXT files in data/ (e.g., Summary_Stats_*.txt)
    for p, u in iter_txt_files():
        rec = record_from_txt(p, u)
        records.append(rec)

    os.makedirs("data", exist_ok=True)
    with open("data/search.json", "w", encoding="utf-8") as out:
        json.dump(records, out, ensure_ascii=False, indent=2)

    print(f"Wrote {len(records)} records to data/search.json")
    # Optional: print some of what was indexed
    for r in records[:8]:
        print("INDEXED:", r["url"])

if __name__ == "__main__":
    main()
