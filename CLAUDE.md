# Sell My Stuff — Long Beach, CA

Local selling workspace for unused items. All items are local pickup only (Long Beach, CA).

## Quick Reference

| Item | Platform(s) | Price | Status |
|------|------------|-------|--------|
| Jasion X-Hunter ST | FB Marketplace, OfferUp, Craigslist, Reddit, FB groups | $749-799 | Pending listing |
| [Electronics TBD] | FB Marketplace, OfferUp, Craigslist | TBD | Pending listing |

## Workspace Structure

- `inventory.md` — Master item list with specs, condition, pricing
- `listings/` — Ready-to-copy listing text for each item
- `templates/` — Reusable templates (listing, auto-replies, safety)
- `research/` — Platform guides, pricing data, market research
- `tracking.md` — Where listed, responses, price drops, sold/pending

## Safety Rules

- Meet at police station parking lot (safe exchange zone)
- Cash, Zelle, or Venmo only — no checks, no weird payment apps
- Daytime meetings only, bring a friend or share location
- For e-bike test rides: hold their car keys or cash FIRST
- Never ship anything

## Automation Stack (All Free)

| Tool | Purpose |
|------|---------|
| FB native auto-reply | Handles "still available?" automatically |
| FB Auto Reply AI (Chrome) | Smarter responses to other questions |
| PopPublic (Chrome) | Autofill listings across FB, Craigslist, Nextdoor |
| FB Marketplace Relister (Chrome) | Auto-bump listings every 3-7 days |

## Commands

| Trigger | Action |
|---------|--------|
| `status` | Show tracking.md state |
| `list [item]` | Generate listing text for an item |
| `price-drop [item]` | Apply next price drop |
| `new [item]` | Add new item to inventory |
| `sold [item] [price] [platform]` | Mark item as sold |
