#!/usr/bin/env python3
import os, json, re
from bs4 import BeautifulSoup

# ========= Config =========
PLOT_HTML = "assets/all_sporulation_genes_scatter_plot.html"
HTML_DIRS = ["."]
TXT_DIR = "data"
EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__"}
MAX_TXT_CHARS = 20000
GENE_MIN_LEN = 2        # adjust if your genes can be 1 char
GENE_MAX_LEN = 20
# A light heuristic: typical gene tokens: letters/digits/_/-/. no spaces
GENE_TOKEN_RE = re.compile(r'^[A-Za-z0-9_.-]{%d,%d}$' % (GENE_MIN_LEN, GENE_MAX_LEN))

def should_exclude(path):
    parts = set(os.path.normpath(path).split(os.sep))
    return bool(parts & EXCLUDE_DIRS)

# ---------- Generic HTML indexing ----------
def iter_html_files():
    for root in HTML_DIRS:
        for d, _, files in os.walk(root):
            if should_exclude(d):
                continue
            for f in files:
                if f.lower().endswith(".html"):
                    path = os.path.join(d, f)
                    url = path.replace("\\","/").lstrip("./")  # relative URL for Pages
                    yield path, url

def extract_text_from_html(soup):
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
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

# ---------- TXT indexing ----------
def iter_txt_files():
    if not os.path.isdir(TXT_DIR):
        return
    for d, _, files in os.walk(TXT_DIR):
        for f in files:
            if f.lower().endswith(".txt"):
                path = os.path.join(d, f)
                url = path.replace("\\","/").lstrip("./")
                yield path, url

def record_from_txt(path, url):
    title = os.path.basename(path).replace("_", " ")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except Exception as e:
        text = f"(Could not read file: {e})"
    content = re.sub(r"\s+", " ", text).strip()
    if len(content) > MAX_TXT_CHARS:
        content = content[:MAX_TXT_CHARS]
    tags = []
    cl = content.lower()
    for key, tag in [("sporulation","sporulation"), ("yb955","YB955"), ("mfd","Mfd")]:
        if key in cl: tags.append(tag)
    return {"title": title, "url": url, "content": content, "tags": tags}

# ---------- Gene extraction from Plotly HTML ----------
def extract_genes_from_plotly_html(path):
    """
    Tries to extract gene names from a Plotly scatter HTML.
    Strategy:
      1) Parse all <script> contents.
      2) Look for JSON-like arrays in keys commonly used by Plotly: "text", "hovertext", "customdata".
      3) Collect string tokens that look like gene names (heuristic).
    """
    if not os.path.isfile(path):
        return []

    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        html = fh.read()

    soup = BeautifulSoup(html, "html.parser")
    scripts = [s.get_text() or "" for s in soup.find_all("script")]

    candidates = set()

    # Helper: pull array after a given key, e.g. "text": [...]
    def pull_arrays(script_text, key):
        out = []
        # match "key": [ ... ] (non-greedy across newlines)
        pattern = re.compile(rf'"{key}"\s*:\s*\[(.*?)\]', re.DOTALL)
        for m in pattern.finditer(script_text):
            arr_raw = m.group(1)
            # grab quoted strings inside array
            for s in re.finditer(r'"([^"]+)"', arr_raw):
                out.append(s.group(1))
        return out

    keys_to_try = ["hovertext", "text", "customdata", "name"]  # common Plotly fields
    for sc in scripts:
        for k in keys_to_try:
            items = pull_arrays(sc, k)
            for item in items:
                tok = item.strip()
                # Heuristic: prefer single-token gene-like strings (no spaces)
                if " " in tok:
                    continue
                if GENE_TOKEN_RE.match(tok):
                    candidates.add(tok)

        # Fallback: any quoted single tokens near Plotly.newPlot payloads
        for m in re.finditer(r'"([A-Za-z0-9_.-]{%d,%d})"' % (GENE_MIN_LEN, GENE_MAX_LEN), sc):
            tok = m.group(1)
            if GENE_TOKEN_RE.match(tok):
                candidates.add(tok)

    # Optional: filter obvious non-genes (common UI words). Add more if needed.
    blacklist = {"Plotly", "plot", "hover", "x", "y", "null", "NaN"}
    genes = sorted([g for g in candidates if g not in blacklist])

    return genes

def gene_records_from_plot(plot_path, plot_url):
    genes = extract_genes_from_plotly_html(plot_path)
    records = []
    for g in genes:
        # Link to plot with a hash the viewer can parse: #gene=GENE
        url = f"{plot_url}#gene={g}"
        rec = {
            "title": g,
            "url": url,
            "content": f"Gene {g} in All Sporulation Genes scatter plot.",
            "tags": ["gene", "sporulation"]
        }
        records.append(rec)
    return records

# ---------- Main ----------
def main():
    records = []

    # 1) HTML pages
    for p, u in iter_html_files():
        records.append(record_from_html(p, u))

    # 2) TXT summaries (optional but useful)
    for p, u in iter_txt_files():
        records.append(record_from_txt(p, u))

    # 3) Genes from the Plotly HTML
    plot_path = PLOT_HTML
    plot_url = plot_path.replace("\\","/").lstrip("./")
    if os.path.isfile(plot_path):
        gene_recs = gene_records_from_plot(plot_path, plot_url)
        records.extend(gene_recs)
        print(f"Extracted {len(gene_recs)} genes from {plot_path}")
    else:
        print(f"WARNING: Plot file not found: {plot_path}")

    os.makedirs("data", exist_ok=True)
    with open("data/search.json", "w", encoding="utf-8") as out:
        json.dump(records, out, ensure_ascii=False, indent=2)

    print(f"Wrote {len(records)} records to data/search.json")
    # Print a few sample gene records for sanity
    sample = [r for r in records if r["tags"] and "gene" in r["tags"]][:5]
    for r in sample:
        print("GENE:", r["title"], "->", r["url"])

if __name__ == "__main__":
    main()
