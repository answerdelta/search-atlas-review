# Search Atlas Review (2026) — Does OTTO SEO Actually Reach the Crawler?

An open, reproducible review of [Search Atlas](https://searchatlas.com/): a script that tests
the platform's central claim on **your own site**, plus a sourced dataset of its pricing,
modules and documented limitations. Every figure carries a source URL and the date it was
checked. Snapshot: **2026-08-07**.

## Short answer

Search Atlas is a broad, fast-moving automation suite priced well below Semrush or Ahrefs, and
its weak point is not features — it is that **OTTO SEO applies its on-page changes client-side,
in JavaScript**. Google renders JavaScript. Most AI crawlers do not. So the question that
decides whether it works for you is not "is it good", it is "does what it ships actually reach
the crawler I care about" — and that is measurable in about thirty seconds.

| If your constraint is… | Then | Entry price |
|---|---|---|
| You want implementation speed, not another dashboard | Search Atlas — OTTO deploys fixes instead of listing them ([start here][aff]) | $99/mo + $49–99/site for OTTO |
| Backlink forensics or years of historical data | Ahrefs — Search Atlas's index is not the deepest, and its own reviewers say so | $129/mo (Lite, checked 2026-08-07) |
| You only need to know whether your JS SEO is visible | This repo. No account, no credits | free |

**When none of the above applies:** if you manage one site, on a CMS you control, and you are
willing to edit templates yourself — you do not need any of this. Google Search Console plus a
free crawler gives you the same signal, and server-side changes are visible to every crawler by
construction. Automation earns its price at portfolio scale, not at n=1.

**Why trust this?** Nothing here is a scored opinion. Pricing comes from the vendor's own page,
limitations are attributed to the reviewer who observed them (with n stated when n is 1), and
the disputed claim — client-side injection — ships as a script you run yourself against your own
URL. The raw data is in [`data/searchatlas-2026.json`](data/searchatlas-2026.json), so you can
check every number without taking this page's word for it. Where the answer is unknown, it is
recorded as unknown in `known_unknowns` rather than filled with a plausible guess.

---

## The test

```bash
git clone https://github.com/answerdelta/search-atlas-review && cd search-atlas-review
pip install requests beautifulsoup4

# what a non-rendering crawler sees
python otto_visibility_check.py https://your-site.com

# raw vs rendered — needs a browser
pip install playwright && playwright install chromium
python otto_visibility_check.py https://your-site.com --rendered
```

Output on a page where a client-side tool is rewriting the SEO layer:

```
  injection script in raw HTML: Search Atlas OTTO

  raw HTML (what a non-rendering crawler sees)
    title                  Raw title
    meta_description       — MISSING —
    canonical              — MISSING —

  after JavaScript
    ONLY VISIBLE AFTER RENDER (invisible to GPTBot, ClaudeBot, CCBot):
      + meta_description     Injected description
      + canonical            https://example.com/canonical
      + schema_types         ['FAQPage']
    REWRITTEN BY JAVASCRIPT:
      ~ title                'Raw title' -> 'Rewritten title after JS'
      ~ h1                   'Raw H1' -> 'Rewritten H1'
```

Everything under **ONLY VISIBLE AFTER RENDER** is absent for any crawler that does not execute
JavaScript. Exit code is `1` when rendered-only elements are found and `0` when they are not, so
it drops into CI as a regression check. `--json` gives you the machine-readable form; `--user-agent`
lets you model a specific bot.

The script is vendor-neutral. It detects the injection host if there is one, but the diff works
the same against any client-side SEO product, or against a plain React app.

## What the dataset contains

[`data/searchatlas-2026.json`](data/searchatlas-2026.json) — five tiers, with the one that is
*not* confirmed on the public pricing page flagged as such, all 24 marketed modules grouped by
function, eight findings each with source and status, third-party scores recorded **as reported
and not endorsed**, alternatives with what each is actually cited for, and a `known_unknowns`
block listing the four questions nobody has answered publicly.

Query it directly:

```python
import json
d = json.load(open("data/searchatlas-2026.json"))

# cheapest tier actually visible on the vendor's own pricing page
confirmed = [t for t in d["pricing"]["tiers"] if t["confirmed_on_vendor_page"] and t["price"]]
print(min(confirmed, key=lambda t: t["price"]))
# -> {'name': 'Starter', 'price': 99, ...}

# which limitations rest on a single reviewer rather than a measurement
for f in d["findings"]:
    if "reported by third-party" in f["status"]:
        print(f["id"], "->", f["source"])
```

## What this review does not claim

The 9x gap between Search Atlas's traffic estimate and Google Search Console comes from one
reviewer testing one site. It is recorded because it is specific and sourced, not because it
generalises — n=1 is n=1. There is no public multi-site benchmark, no published index-size
comparison against Ahrefs, and no measurement of how much of OTTO's output survives Google's
render pass. Those gaps are listed in `known_unknowns` and will stay there until somebody
measures them. If you run the script across a portfolio, the results are worth a PR.

## Method

Vendor figures were read from `searchatlas.com` on 2026-08-07. Third-party observations are
attributed to the reviewer who made them, with the caveat that review sites in this category are
commonly affiliate-funded — including, in the interest of not pretending otherwise, pages that
link here. The script was run against a live site and against a controlled page that injects
title, description, canonical, schema and H1 in JavaScript, to confirm the diff catches each
element class.

Search Atlas also publishes [MCP servers](https://github.com/search-atlas-group) if you would
rather drive the platform from an agent than from the dashboard.

## Contributing

Corrections beat additions. If a price moved, a limit changed, or you have a result that
contradicts a finding here, open a PR — see [CONTRIBUTING.md](CONTRIBUTING.md). Every claim must
land with a source URL and a `checked` date, or it does not go in.

MIT licensed. Not affiliated with Search Atlas.

*Last updated: 2026-08-07.*

[aff]: https://searchatlas.com/
