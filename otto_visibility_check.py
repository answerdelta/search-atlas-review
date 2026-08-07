#!/usr/bin/env python3
"""
otto_visibility_check.py — does your JS-injected SEO actually reach the crawler?

Search Atlas OTTO SEO (and every other pixel/script-based "autopilot SEO" product)
applies its changes client-side, through a JavaScript snippet. Google renders
JavaScript, so those changes can be picked up — but only on the second pass, and
only for crawlers that render at all. Most LLM crawlers (GPTBot, ClaudeBot,
PerplexityBot, CCBot) do not execute JavaScript.

This script tells you, for any URL, which SEO-critical elements exist in the raw
HTML versus which only appear after JavaScript runs. Anything in the
"rendered-only" column is invisible to non-rendering crawlers.

Usage
-----
    # raw HTML only — no browser needed
    python otto_visibility_check.py https://example.com

    # raw vs rendered — requires: pip install playwright && playwright install chromium
    python otto_visibility_check.py https://example.com --rendered

    # machine-readable
    python otto_visibility_check.py https://example.com --rendered --json

Exit codes: 0 = no rendered-only SEO elements, 1 = rendered-only elements found,
2 = fetch error. Suitable for CI.

MIT licensed. Vendor-neutral: it works the same on any JS-injection SEO tool.
"""

import argparse
import json
import sys

import requests
from bs4 import BeautifulSoup

# Script hosts used by client-side SEO injection products. Presence in the raw
# HTML means SEO changes are likely applied after render.
INJECTORS = {
    "sa.searchatlas.com": "Search Atlas OTTO",
    "searchatlas.com/otto": "Search Atlas OTTO",
    "dashboard.searchatlas.com": "Search Atlas",
    "cdn.searchatlas.com": "Search Atlas",
    "seovendor": "generic",
}

UA_GOOGLEBOT = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)


def extract(html):
    """Pull the SEO-critical elements out of an HTML string."""
    soup = BeautifulSoup(html, "html.parser")

    def attr(tag, name):
        return tag.get(name, "").strip() if tag else None

    def meta(name=None, prop=None):
        if name:
            return attr(soup.find("meta", attrs={"name": name}), "content")
        return attr(soup.find("meta", attrs={"property": prop}), "content")

    h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    imgs = soup.find_all("img")
    schema_types = []
    for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(node.string or "{}")
        except (ValueError, TypeError):
            schema_types.append("<invalid JSON-LD>")
            continue
        for item in payload if isinstance(payload, list) else [payload]:
            if isinstance(item, dict) and item.get("@type"):
                t = item["@type"]
                schema_types.extend(t if isinstance(t, list) else [t])

    return {
        "title": soup.title.get_text(strip=True) if soup.title else None,
        "meta_description": meta(name="description"),
        "meta_robots": meta(name="robots"),
        "canonical": attr(soup.find("link", attrs={"rel": "canonical"}), "href"),
        "og_title": meta(prop="og:title"),
        "og_description": meta(prop="og:description"),
        "h1": h1s[0] if h1s else None,
        "h1_count": len(h1s),
        "schema_types": sorted(set(schema_types)),
        "hreflang_count": len(soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})),
        "internal_link_count": len(soup.find_all("a", href=True)),
        "img_count": len(imgs),
        "img_missing_alt": sum(1 for i in imgs if not i.get("alt", "").strip()),
    }


def detect_injector(html):
    lowered = html.lower()
    return sorted({label for needle, label in INJECTORS.items() if needle in lowered})


def fetch_raw(url, timeout, user_agent):
    r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_rendered(url, timeout, user_agent):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "--rendered needs Playwright:\n"
            "    pip install playwright && playwright install chromium"
        )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=user_agent)
        page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
        html = page.content()
        browser.close()
    return html


SCALARS = (
    "title", "meta_description", "meta_robots", "canonical",
    "og_title", "og_description", "h1",
)


def diff(raw, rendered):
    """Classify every field as added / changed / unchanged after JS."""
    out = {"added": {}, "changed": {}, "unchanged": []}
    for key in SCALARS:
        a, b = raw.get(key), rendered.get(key)
        if a == b:
            out["unchanged"].append(key)
        elif not a and b:
            out["added"][key] = b
        else:
            out["changed"][key] = {"raw": a, "rendered": b}

    new_schema = sorted(set(rendered["schema_types"]) - set(raw["schema_types"]))
    if new_schema:
        out["added"]["schema_types"] = new_schema
    elif rendered["schema_types"] == raw["schema_types"]:
        out["unchanged"].append("schema_types")

    for key in ("hreflang_count", "internal_link_count", "img_missing_alt"):
        if raw[key] != rendered[key]:
            out["changed"][key] = {"raw": raw[key], "rendered": rendered[key]}
        else:
            out["unchanged"].append(key)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("url")
    ap.add_argument("--rendered", action="store_true",
                    help="also fetch with a real browser and diff")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--user-agent", default=UA_GOOGLEBOT,
                    help="default: Googlebot. Try GPTBot to model an LLM crawler.")
    args = ap.parse_args()

    try:
        raw_html = fetch_raw(args.url, args.timeout, args.user_agent)
    except requests.RequestException as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 2

    report = {
        "url": args.url,
        "user_agent": args.user_agent,
        "injectors_detected": detect_injector(raw_html),
        "raw": extract(raw_html),
    }

    if args.rendered:
        rendered_html = fetch_rendered(args.url, args.timeout, args.user_agent)
        report["rendered"] = extract(rendered_html)
        report["diff"] = diff(report["raw"], report["rendered"])

    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"\n  {args.url}")
        print(f"  UA: {args.user_agent[:60]}")
        inj = report["injectors_detected"]
        print(f"  injection script in raw HTML: {', '.join(inj) if inj else 'none detected'}\n")
        print("  raw HTML (what a non-rendering crawler sees)")
        for k, v in report["raw"].items():
            print(f"    {k:22} {str(v)[:90] if v not in (None, [], 0) else '— MISSING —'}")
        if args.rendered:
            d = report["diff"]
            print("\n  after JavaScript")
            if d["added"]:
                print("    ONLY VISIBLE AFTER RENDER (invisible to GPTBot, ClaudeBot, CCBot):")
                for k, v in d["added"].items():
                    print(f"      + {k:20} {str(v)[:80]}")
            if d["changed"]:
                print("    REWRITTEN BY JAVASCRIPT:")
                for k, v in d["changed"].items():
                    print(f"      ~ {k:20} {str(v['raw'])[:35]!r} -> {str(v['rendered'])[:35]!r}")
            if not d["added"] and not d["changed"]:
                print("    no SEO-critical element changed — everything is server-side. Good.")

    if args.rendered and (report["diff"]["added"] or report["diff"]["changed"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
