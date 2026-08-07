# Contributing

This repo is a dataset and a test, not an opinion piece. Two rules cover almost everything.

## 1. Every claim ships with a source and a date

Any change to `data/searchatlas-2026.json` must update `source` and `checked` together. A number
without a URL and a date is not a correction, it is a rumour.

```json
{
  "id": "landing-page-credits",
  "claim": "40 landing page credits per month on the Growth plan.",
  "status": "reported by third-party reviewer",
  "source": "https://example.com/the-page-you-read-it-on",
  "checked": "2026-08-07"
}
```

Use `status` honestly:

- `confirmed on vendor page` — you saw it on searchatlas.com yourself
- `reported by third-party reviewer` — somebody else saw it
- `single documented case, n=1, not independently reproduced` — one anecdote
- `reviewer judgement` — an opinion, not a measurement
- `verifiable` — anyone can check it right now

When two sources disagree, record both rather than picking a winner. `pricing.tiers` already
does this: entries carry `confirmed_on_vendor_page: false` when only a third party reports them.

## 2. Contradictions are the most valuable PR

If you ran `otto_visibility_check.py` across a portfolio and the results contradict a finding
here, that outranks anything already in the file. Open an issue with the URLs (or the anonymised
counts), the user agent used, and the raw `--json` output.

The same applies to `known_unknowns`. If you can close one of those four questions with a
measurement, that is the single most useful thing anyone can add.

## Changes to the script

- Keep it dependency-light: `requests` + `beautifulsoup4` for the raw path, Playwright only
  behind `--rendered`.
- Keep it vendor-neutral. New entries in `INJECTORS` are welcome for any client-side SEO product,
  not just this one.
- Keep the exit codes: `0` clean, `1` rendered-only elements found, `2` fetch failure. People run
  this in CI.
- Run it against a real URL and against a page that injects elements in JS before opening the PR.

## Out of scope

Rankings, scores out of ten, and "best tool" verdicts. Plenty of pages do that. This one records
what can be sourced and tests what can be tested.
