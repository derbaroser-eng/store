# AURUM Store

Live storefront at https://derbaroser-eng.github.io/store/

Thirteen tested digital products, each with a verified live Stripe checkout.
No account, no subscriptions, no data leaves your machine.

## Regenerate

The catalogue is generated, not hand-edited:

    python build_store.py

Checkout links come only from `../suite_checkout_manifest.json`, whose entries
were checked with HTTP 200. Product names, descriptions and prices come from
the shipped suite index `../index.html`. The generator fails closed on drift.

## Test

    python test_store.py

Nine acceptance tests: one verified card per product, no invented checkout
links, all pages https, no placeholders, byte-stable regeneration.

## Writing

- [I built 13 tools you buy once, because subscribing to a CSV parser broke something in me](https://dev.to/aurum_revenue/i-built-13-tools-you-buy-once-because-subscribing-to-a-csv-parser-broke-something-in-me-n7g) — why these are one-time purchases, and what's actually in the catalogue.
