"""Build the five Termly legal pages into the preview site.

Input: raw_<termly-slug>.html files, a tag-for-tag cleaned copy of each
Termly document (headings, paragraphs, lists, tables, links, bold/italic;
Termly's inline styles and editor tags removed, text unchanged).

Output:
  - <out>/<slug>.html  Divi-ready fragment (original Termly anchor ids)
  - <out>/<slug>.txt   plain text
  - LEGAL entries injected into index.html and v2/index.html

Usage: python3 tools/build_legal.py RAW_DIR OUT_DIR
"""
import json, re, sys, pathlib
from bs4 import BeautifulSoup, NavigableString

RAW, OUT = map(pathlib.Path, sys.argv[1:3])
REPO = pathlib.Path(__file__).resolve().parent.parent

# site route, Termly slug, page title, output file name
DOCS = [
    ("privacy", "privacy-policy", "Privacy Policy", "privacy-policy"),
    ("cookie-policy", "cookie-policy", "Cookie Policy", "cookie-policy"),
    ("terms", "terms-of-service", "Terms and Conditions", "terms-and-conditions"),
    ("disclaimer", "disclaimer", "Disclaimer", "disclaimer"),
    ("accessibility", "a11y-statement", "Accessibility Statement", "accessibility-statement"),
]


def tidy(html):
    """Shared clean-up: one list per run of items, no duplicate or unused ids."""
    html = re.sub(r"</ul>\s*<ul>", "", html)
    # Termly splits one table into several back-to-back tables; join them
    # (only header tables; Cookie Policy uses one small table per cookie on purpose)
    if "<thead>" in html:
        html = re.sub(r"</tbody></table>\s*<table><tbody>", "", html)
    soup = BeautifulSoup(html, "html.parser")
    linked = {a["href"][1:] for a in soup.find_all("a", href=True) if a["href"].startswith("#")}
    seen = set()
    for el in soup.find_all(id=True):
        i = el["id"]
        if i in seen or i == "control" or (el.name == "span" and i not in linked):
            del el["id"]
        else:
            seen.add(i)
    for el in soup.find_all("span"):
        if not el.attrs and not el.contents:
            el.decompose()
        elif not el.attrs:
            el.unwrap()
    for el in soup.find_all("div"):
        if not el.attrs:
            el.unwrap()
    # header: the page template shows the title and the "Last updated" line
    h1 = soup.find("h1")
    if h1:
        h1.decompose()
    byline = ""
    first = soup.find("p")
    if first and first.get_text().strip().startswith("Last updated"):
        byline = re.sub(r"\s+", " ", first.get_text()).strip()
        first.decompose()
    return soup, byline


def to_text(soup):
    lines = []
    for el in soup.find_all(["h2", "h3", "p", "li", "tr"]):
        if el.name == "p" and el.find_parent(["li", "td", "th"]):
            continue
        if el.name == "tr":
            t = " | ".join(re.sub(r"\s+", " ", c.get_text()).strip() for c in el.find_all(["th", "td"]))
        else:
            t = re.sub(r"\s+", " ", el.get_text()).strip()
        if not t:
            continue
        if el.name == "h2":
            lines += ["", "## " + t, ""]
        elif el.name == "h3":
            lines += ["", "### " + t, ""]
        elif el.name == "li":
            lines.append("- " + t)
        else:
            lines += [t, ""] if el.name == "p" else [t]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


entries = []
OUT.mkdir(parents=True, exist_ok=True)
for route, slug, title, fname in DOCS:
    raw = (RAW / f"raw_{slug}.html").read_text()
    soup, byline = tidy(raw)
    # Divi copy: original ids, external links open in a new tab
    divi = BeautifulSoup(str(soup), "html.parser")
    for a in divi.find_all("a", href=True):
        if a["href"].startswith("http"):
            a["target"], a["rel"] = "_blank", "noopener"
    head = f"<h1>{title}</h1>\n" + (f"<p><strong>{byline}</strong></p>\n" if byline else "")
    (OUT / f"{fname}.html").write_text(head + str(divi) + "\n")
    (OUT / f"{fname}.txt").write_text(title.upper() + "\n" + (byline + "\n" if byline else "") + "\n" + to_text(soup))
    # Site copy: anchors become #route/route-id so the hash router can scroll to them
    site = BeautifulSoup(str(soup), "html.parser")
    for el in site.find_all(id=True):
        el["id"] = f"{route}-{el['id']}"
    for a in site.find_all("a", href=True):
        h = a["href"]
        if h.startswith("#"):
            a["href"] = f"#{route}/{route}-{h[1:]}"
        elif h.startswith("http"):
            a["target"], a["rel"] = "_blank", "noopener"
    body = re.sub(r"\s*\n\s*", " ", str(site))
    entries.append(f"  {json.dumps(route)}:{{t:{json.dumps(title)},h:{json.dumps(title)},by:{json.dumps(byline)},html:{json.dumps(body, ensure_ascii=False)}}}".replace("</", "<\\/"))

LEGAL_JS = "var LEGAL={\n" + ",\n".join(entries) + "\n};\n"
RENDER_OLD = re.compile(r"function renderLegal\(key\)\{.*?\n\}\n", re.S)
RENDER_NEW = (
    "function renderLegal(key){\n"
    "  var g=LEGAL[key];$(\"#l-crumb\").textContent=g.t;$(\"#l-h1\").textContent=g.h;$(\"#l-by\").innerHTML=g.by;\n"
    "  $(\"#l-main\").innerHTML=\"<div class=\\\"termly-doc\\\">\"+g.html+\"</div>\";\n"
    "}\n"
)
CSS = (
    "/* Termly legal documents */\n"
    ".termly-doc{max-width:760px;font-size:1.0625rem;line-height:1.65;overflow-wrap:break-word}\n"
    ".termly-doc h2{font-size:clamp(1.25rem,1.1rem + .6vw,1.6rem);letter-spacing:-.02em;margin:2.2em 0 .6em}\n"
    ".termly-doc h3{font-size:1.15rem;margin:1.6em 0 .5em}\n"
    ".termly-doc p{margin:0 0 1em}\n"
    ".termly-doc ul{margin:0 0 1.1em;padding-left:1.4em;list-style:disc}\n"
    ".termly-doc li{margin:0 0 .5em}\n"
    ".termly-doc li p,.termly-doc td p{margin:0}\n"
    ".termly-doc a{color:var(--indigo,#303890);text-decoration:underline}\n"
    ".termly-doc table{width:100%;border-collapse:collapse;margin:0 0 1.2em;font-size:1rem}\n"
    ".termly-doc th,.termly-doc td{border:1px solid var(--line-2,#d9dbe8);padding:10px 12px;text-align:left;vertical-align:top}\n"
    ".termly-doc thead th:first-child{width:30%}.termly-doc thead th:last-child{width:7em}\n"
    ".termly-doc th{background:var(--mist,#f3f4fa);font-weight:600}\n"
    ".termly-doc [id]{scroll-margin-top:110px}\n"
    "@media (max-width:640px){.termly-doc table,.termly-doc tbody,.termly-doc thead,.termly-doc tr{display:block}.termly-doc th,.termly-doc td{display:block;border-bottom:0}.termly-doc tr{border-bottom:1px solid var(--line-2,#d9dbe8);margin-bottom:12px}}\n"
)
FOOT_OLD = '<a href="#privacy">Privacy policy</a><a href="#terms">Terms</a><a href="#accessibility">Accessibility</a>'
FOOT_NEW = ('<a href="#privacy">Privacy Policy</a><a href="#cookie-policy">Cookie Policy</a>'
            '<a href="#terms">Terms and Conditions</a><a href="#disclaimer">Disclaimer</a>'
            '<a href="#accessibility">Accessibility Statement</a>')

for f in ["index.html", "v2/index.html"]:
    p = REPO / f
    s = p.read_text()
    s, n1 = re.subn(r"var LEGAL=\{\n.*?\n\};\n", lambda m: LEGAL_JS, s, count=1, flags=re.S)
    s, n2 = RENDER_OLD.subn(lambda m: RENDER_NEW, s, count=1)
    if "/* Termly legal documents */" not in s:
        s, n3 = re.subn(r"</style>", lambda m: CSS + "</style>", s, count=1)
    else:
        s = re.sub(r"/\* Termly legal documents \*/\n.*?(?=</style>)", lambda m: CSS, s, count=1, flags=re.S)
        n3 = 1
    n4 = s.count(FOOT_OLD)
    s = s.replace(FOOT_OLD, FOOT_NEW)
    assert n1 == 1 and n2 == 1 and n3 == 1, (f, n1, n2, n3)
    p.write_text(s)
    print(f, "footer links replaced:", n4)
