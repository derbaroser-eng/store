#!/usr/bin/env python3
"""Generate store/index.html from the verified suite catalogue.

Checkout links come only from suite_checkout_manifest.json entries with
http_status 200. Names and descriptions come from the shipped suite index.
Deterministic and fails closed on catalogue drift.
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRODUCTS = ROOT.parent
SUITE = PRODUCTS / "index.html"
MANIFEST = PRODUCTS / "suite_checkout_manifest.json"
BASE = "https://derbaroser-eng.github.io/"
STRIPE_RE = re.compile(r"https://buy\.stripe\.com/[A-Za-z0-9_-]+")
CARD = "<a class=\x22card\x22"

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AURUM Store - real tools, instant checkout</title>
<meta name="description" content="__COUNT__ tested digital products with live Stripe checkout. No account, no subscriptions.">
<style>
:root{--bg:#0b0f14;--fg:#e6edf3;--dim:#9aa7b4;--acc:#4cc2ff;--card:#11161d;--line:#21262d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:56px 24px}
h1{font-size:2.2rem;margin:0 0 10px}p.lede{color:var(--dim);margin:0 0 34px;max-width:640px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;
transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--acc);transform:translateY(-2px)}
.card h3{margin:0 0 6px;font-size:1.02rem}.card p{color:var(--dim);font-size:.9rem;margin:0 0 12px}
.price{color:var(--acc);font-weight:700;font-size:1.1rem;margin:0 0 12px}
.actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.btn{background:var(--acc);color:#04121d;font-weight:700;padding:8px 16px;
border-radius:8px;font-size:.9rem;text-decoration:none}
.btn.alt{background:transparent;color:var(--acc);border:1px solid var(--acc)}
.details{color:var(--dim);font-size:.85rem}
footer{margin-top:52px;padding-top:20px;border-top:1px solid var(--line);
font-size:.85rem;color:var(--dim)}
</style></head><body><div class="wrap">
<h1>The AURUM Store</h1>
<p class="lede">__COUNT__ products, built and tested. Every checkout is a live Stripe
payment link verified against the signed catalogue - instant delivery, no account.</p>
<div class="grid" data-products="__COUNT__">
"""

TAIL = """
</div>
<footer><p>Payments are processed by Stripe. No product on this page is a
simulation; each links to a live, verified Stripe checkout session.</p></footer>
</div></body></html>
"""


def parse_suite():
    out = {}
    text = SUITE.read_text(encoding="utf-8")
    for chunk in text.split(CARD)[1:]:
        page = re.search(r"href=\x22([^\x22]+)\x22", chunk)
        name = re.search(r"<h3>(.*?)</h3>", chunk, re.S)
        desc = re.search(r"<p>(.*?)</p>", chunk, re.S)
        price = re.search(r"<div class=\x22price\x22>(.*?)</div>", chunk, re.S)
        if not (page and name):
            continue
        slug = re.sub(r"^" + re.escape(BASE) + r"|/$", "", page.group(1))
        if not slug or "/" in slug:
            continue
        out[slug] = {
            "page": page.group(1),
            "name": html.unescape(name.group(1)).strip(),
            "desc": html.unescape(desc.group(1)).strip() if desc else "",
            "price": html.unescape(price.group(1)).strip() if price else "",
            "links": set(STRIPE_RE.findall(chunk)),
        }
    return out


def render_card(slug, item, urls):
    esc = html.escape
    parts = ["<article class=\x22card\x22 data-slug=\x22%s\x22>" % esc(slug),
             "  <h3>%s</h3>" % esc(item["name"])]
    if item["desc"]:
        parts.append("  <p>%s</p>" % esc(item["desc"]))
    if item["price"]:
        parts.append("  <div class=\x22price\x22>%s</div>" % esc(item["price"]))
    parts.append("  <div class=\x22actions\x22>")
    for i, url in enumerate(urls):
        label = "Buy now" if i == 0 else "Name your price"
        css = "btn" if i == 0 else "btn alt"
        parts.append("    <a class=\x22%s\x22 href=\x22%s\x22>%s</a>"
                     % (css, esc(url), label))
    parts.append("    <a class=\x22details\x22 href=\x22%s\x22>Details</a>"
                 % esc(item["page"]))
    parts.append("  </div>")
    parts.append("</article>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "index.html"))
    args = ap.parse_args()
    products = json.loads(MANIFEST.read_text(encoding="utf-8"))["products"]
    suite = parse_suite()
    if set(suite) != set(products):
        raise SystemExit("catalogue drift: suite=%s manifest=%s"
                         % (sorted(set(suite)), sorted(set(products))))
    cards = []
    for slug, entry in products.items():
        if entry.get("http_status") != 200:
            raise SystemExit("unverified checkout for " + slug)
        urls = entry["checkout_urls"]
        if not urls or not set(suite[slug]["links"]) <= set(urls):
            raise SystemExit("checkout drift for " + slug)
        cards.append(render_card(slug, suite[slug], urls))
    doc = HEAD.replace("__COUNT__", str(len(cards))) + "\n".join(cards) + TAIL
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    print("wrote %s: %d verified products" % (args.out, len(cards)))


if __name__ == "__main__":
    main()
