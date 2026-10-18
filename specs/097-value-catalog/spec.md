# Feature Specification: What a client sells, in its own catalog's words

**Created**: 2026-10-18

**Status**: Implemented (this PR)

**Input**:
- CTO, 2026-10-18: Value is next, and only zero-cost work is in scope (independent developer, no paid sources).
- On 20 typical agency clients, 10 were read only as "retail trade" (ISIC G), which says nothing of what they sell.

## What changes
- **`OFFER/CATALOG_CATEGORIES`**, a new kind in the Value family, DECLARED by the site. It is read from two free, public signals of the client's own site:
  1. **Catalog links on its homepage**, on catalog paths in any platform or language: `/collections/`, `/product-category/`, `/categoria/`, `/kategorie/`, `/catalogo/`, `/c/`.
     - The link text is used, or its slug when the text is empty.
     - Never kept: promotions, "shop all", gift cards, audiences ("Mujer", "Men", "Kids"), counts or anything with digits.
  2. **On Shopify storefronts, the public catalog's product types** (`/products.json`).
     - It costs one request within the site budget, with robots respected.
     - Only product types are kept, with how many products carry each. Products, prices and descriptions are never kept.
     - Season codes (AW26, SS25) and generic types ("food", "product") are dropped.

  Product types win when they name three or more; otherwise catalog links (at least two) are used.
- **Family value:** the client's own catalog categories become the Value headline, ahead of a sector code.
- **Integration:** AXENT reads it as capability evidence, the marketing pool maps it to Value, and the web shows it in 6 languages.

## Measured on the real sites of the panel (2026-10-18)
7 of 15 readable sites now say what they sell:

| Client | Categories |
|---|---|
| Velasca | casual shirts, boat shoes, penny loafers… |
| Claus Porto | soaps, fragrances, reed diffusers, candles… |
| mymuesli | muesli, porridge, bars, tea… |
| Ecoalf | coats and jackets, knitwear, dresses… |
| Huel | hot meals, protein snacks, ready-to-drink… |
| einhorn | condoms, period products |
| Tony's Chocolonely | big bars, small bars |

Sites with JavaScript-only menus or no catalog paths keep their activity reading.

## Doctrine
- DECLARED by the client's own site: what it offers, never what it sells most.
- There is no scraping of products or prices.
- One request, within budget, with robots respected.
