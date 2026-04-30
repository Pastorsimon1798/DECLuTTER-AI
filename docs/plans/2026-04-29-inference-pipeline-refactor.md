# Inference Pipeline Refactor: Move Deterministic Work to the Database

> **Status:** Architectural analysis. Ready for implementation when scheduled.
> **Created:** 2026-04-29
> **Audience:** Data engineers, backend architects, AI coding agents
> **Goal:** Reduce LLM burden by moving lookup, matching, categorization, and pricing rules into a robust deterministic database layer. Reserve the LLM for vision detection, novel items, and creative tasks.

---

## Executive Summary

The current inference pipeline asks the LLM to do **boring work** — generating price ranges for common items, returning free-text labels that require fuzzy matching, and pricing items one-at-a-time in N+1 loops. This is slow, expensive, and inconsistent.

**This document identifies exactly what to move to the database, what the new schema should look like, and what the LLM should keep doing.**

The guiding principle:

> **The LLM handles *interesting* work (vision, creativity, novelty). The database handles *boring* work (lookups, rules, matching, categorization).**

---

## Current Pipeline: Where the LLM Wastes Cycles

### Touchpoint 1: Price Estimation (`llm_price_estimator.py`)

```python
# LLM prompt (temperature=0, max_tokens=128):
# "What is the typical garage-sale price for a used 'bluetooth speaker'?"
# → {"low": 10, "median": 35, "high": 80}
```

**Problem:** The LLM is asked to recall the price of common items from its training data. This is a **lookup**, not reasoning. It's:
- **Slow:** 500ms–2s per call (LM Studio round-trip)
- **Inconsistent:** Same item can return different prices across calls
- **Expensive:** Every cache miss hits the inference server
- **Brittle:** JSON parsing, markdown stripping, type validation, ordering enforcement — all defensive code against LLM misbehavior

**Current mitigation:** SQLite cache with 90-day TTL. But cache misses for common items still hit the LLM unnecessarily.

### Touchpoint 2: Vision Analysis (`analysis_adapter.py`)

```python
# LLM prompt: "Analyze this image and return items with label, confidence, estimated_value_usd"
# → {"items": [{"label": "portable speaker", "confidence": 0.92, "estimated_value_usd": 45}]}
```

**Problem:** The vision LLM returns **free-text labels** like "portable speaker" or "JBL Flip 5." The pipeline then:
1. Discards the LLM's `estimated_value_usd` entirely (good — it's overridden)
2. Runs fuzzy substring matching across ALL rows in `price_ranges` (O(n) string scan)
3. If no match, hits the price LLM for a fresh estimate

**The vision LLM has no awareness of the canonical taxonomy.** It invents its own labels every time.

### Touchpoint 3: Analysis Route N+1 Loop (`analysis.py`)

```python
for item in result.items:
    valuation = valuation_service.estimate(
        ValuationRequest(label=item.label, condition="unknown")
    )
```

**Problem:** Each detected item triggers a **separate DB query** (and potentially a separate LLM call). For a cluttered photo with 8 items, that's 8 round-trips. Should be one batch query.

### Touchpoint 4: Category Assignment (`listing_service.py`)

```python
_category_map = {
    "electronics": "Consumer Electronics",
    "book": "Books & Magazines",
    "clothing": "Clothing, Shoes & Accessories",
    "toy": "Toys & Hobbies",
    "kitchen item": "Home & Garden",
    "paper clutter": "Collectibles",
}
```

**Problem:** A 6-entry hardcoded dictionary. Any item not in these six buckets gets "Everything Else." This is unmaintainable and wrong for 6,072+ item types.

---

## The Refactor: What Moves to the Database

### 1. Item Taxonomy — From Free-Text to Canonical IDs

**New table: `item_taxonomy`**

```sql
CREATE TABLE item_taxonomy (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,           -- "bluetooth speaker"
    normalized_name TEXT NOT NULL UNIQUE,   -- "bluetooth speaker"
    category_id INTEGER NOT NULL,
    parent_id INTEGER REFERENCES item_taxonomy(id),
    description TEXT,                        -- "Portable wireless audio device"
    typical_dimensions_cm TEXT,             -- "18x7x7"
    typical_weight_kg REAL,                 -- 0.4
    safety_checklist_tag TEXT,              -- "electronics"
    condition_assessment_hints TEXT,        -- JSON: {"check_ports": true, "check_battery": true}
    marketplace_category_ebay TEXT,         -- "15052" (Consumer Electronics > Portable Audio)
    marketplace_category_facebook TEXT,     -- "ELECTRONICS"
    created_at TEXT NOT NULL
);

CREATE TABLE item_taxonomy_aliases (
    id INTEGER PRIMARY KEY,
    taxonomy_id INTEGER NOT NULL REFERENCES item_taxonomy(id),
    alias TEXT NOT NULL,                     -- "portable speaker"
    alias_normalized TEXT NOT NULL,
    source TEXT DEFAULT 'manual',            -- manual, llm_generated, user_submitted
    UNIQUE(taxonomy_id, alias_normalized)
);

CREATE INDEX idx_taxonomy_normalized ON item_taxonomy(normalized_name);
CREATE INDEX idx_aliases_normalized ON item_taxonomy_aliases(alias_normalized);
CREATE VIRTUAL TABLE taxonomy_fts USING fts5(canonical_name, description, content='item_taxonomy', content_rowid='id');
```

**What this replaces:**
- Fuzzy substring matching in `PriceDatabase.get_price_range()`
- Hardcoded category mapping in `ListingDraftService`
- Brittle label normalization across the pipeline

**How it works:**
1. Vision LLM returns a free-text label: `"portable speaker"`
2. Deterministic code normalizes: `"portable speaker"`
3. Query `item_taxonomy_aliases` for exact match → finds `taxonomy_id` for `"bluetooth speaker"`
4. Use canonical name for all downstream lookups (price, category, safety checklist)
5. If no alias match, fall back to FTS5 full-text search, then semantic embedding similarity
6. If still no match → **this is a novel item. Hand to LLM for pricing. Cache result.**

**Degrees of freedom preserved:**
- The LLM can still detect novel items not in taxonomy (e.g., "vintage Soviet oscilloscope")
- Users can submit new aliases ("My mom calls this a 'boom box'")
- Aliases can be auto-generated from LLM outputs and community-verified

---

### 2. Price Rules Engine — From LLM Recall to Deterministic Computation

**New table: `price_rules`**

```sql
CREATE TABLE price_rules (
    id INTEGER PRIMARY KEY,
    taxonomy_id INTEGER REFERENCES item_taxonomy(id),
    category_id INTEGER REFERENCES categories(id),
    -- If taxonomy_id is set, rule is specific. If only category_id, rule is category-default.
    condition_multiplier_new REAL DEFAULT 1.0,
    condition_multiplier_like_new REAL DEFAULT 0.85,
    condition_multiplier_good REAL DEFAULT 0.70,
    condition_multiplier_fair REAL DEFAULT 0.40,
    condition_multiplier_poor REAL DEFAULT 0.15,
    base_low_price REAL,                     -- Category baseline
    base_median_price REAL,
    base_high_price REAL,
    brand_premium_rules TEXT,                -- JSON: {"apple": 1.30, "sony": 1.15, "generic": 1.0}
    age_depreciation_pct_per_year REAL,      -- Electronics: 20.0, Books: 5.0, Furniture: 10.0
    seasonal_adjustment_rules TEXT,          -- JSON: {"december": 1.20, "january": 0.80}
    region_adjustment_rules TEXT,            -- JSON: {"nyc": 1.15, "rural_midwest": 0.85}
    source TEXT NOT NULL,                    -- seeded, community, llm_derived
    confidence TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    marketplace_mapping_ebay TEXT,
    marketplace_mapping_facebook TEXT,
    typical_weight_class TEXT,               -- small, medium, large, bulky
    shipping_complexity TEXT                 -- simple, fragile, oversized, hazardous
);
```

**What this replaces:**
- LLM price estimation for common items (99%+ of cache hits)
- Hardcoded condition multipliers in `/valuation` simple endpoint
- Hardcoded category map in `ListingDraftService`

**How it works:**

```python
def compute_price(taxonomy_id: int, condition: str, brand: str | None, age_years: float) -> PriceRange:
    # 1. Fetch taxonomy-specific rule, or category-default rule
    rule = get_price_rule(taxonomy_id)
    
    # 2. Apply base price
    low = rule.base_low_price
    median = rule.base_median_price
    high = rule.base_high_price
    
    # 3. Apply condition multiplier
    multiplier = getattr(rule, f"condition_multiplier_{condition}", 0.7)
    low *= multiplier
    median *= multiplier
    high *= multiplier
    
    # 4. Apply brand premium
    if brand and brand in rule.brand_premium_rules:
        premium = rule.brand_premium_rules[brand]
        low *= premium
        median *= premium
        high *= premium
    
    # 5. Apply age depreciation
    if age_years and rule.age_depreciation_pct_per_year:
        depreciation = max(0.1, 1.0 - (age_years * rule.age_depreciation_pct_per_year / 100))
        low *= depreciation
        median *= depreciation
        high *= depreciation
    
    return PriceRange(low=round(low, 2), median=round(median, 2), high=round(high, 2))
```

**LLM involvement:**
- **No LLM call** if taxonomy has a price rule.
- **LLM called only for:** Novel items not in taxonomy, items with no price rule, or when user explicitly requests "get me an AI estimate."
- When LLM returns a price for a novel item, we **derive a price rule** from it (store base prices, infer category defaults) and add the item to taxonomy. Next time: deterministic.

**Degrees of freedom preserved:**
- Rules are data, not code. Update via admin UI or bulk import.
- Community sales data auto-adjusts rules (same mechanism as today, but applied to `price_rules` instead of raw `price_ranges`).
- Brand premiums and age depreciation are configurable per category.

---

### 3. Batch Valuation — Eliminate N+1

**Current (N+1):**
```python
for item in result.items:           # 8 items
    valuation = valuation_service.estimate(ValuationRequest(label=item.label))
    # → 8 DB queries, potentially 8 LLM calls
```

**New (batch):**
```python
labels = [item.label for item in result.items]
valuations = valuation_service.estimate_batch(labels, condition="unknown")
# → 1 DB query with IN clause, 0–1 LLM call for the entire batch
```

**Implementation:**
```sql
-- Single query resolves all labels
SELECT t.canonical_name, t.id as taxonomy_id,
       pr.base_low_price, pr.base_median_price, pr.base_high_price,
       pr.condition_multiplier_good
FROM item_taxonomy_aliases a
JOIN item_taxonomy t ON a.taxonomy_id = t.id
LEFT JOIN price_rules pr ON pr.taxonomy_id = t.id
WHERE a.alias_normalized IN (?, ?, ?, ?, ?, ?, ?, ?);
```

**LLM involvement:**
- Batch query returns prices for 7 out of 8 items.
- The 1 missing item is collected and sent to the LLM in a **single batch prompt**:
  ```
  "What are typical resale prices for these items: ['vintage Soviet oscilloscope', 'ceramic owl figurine']?"
  → [{"label": "...", "low": ..., "median": ..., "high": ...}, ...]
  ```
- One LLM call handles all novel items instead of N serial calls.

---

### 4. Constrained Vision Prompt — Taxonomy-Aware Detection

**Current prompt:**
```
"Analyze this image and return items with label, confidence, estimated_value_usd"
→ LLM invents labels: "portable speaker", "JBL Flip 5", "wireless audio device"
```

**New prompt:**
```
"Analyze this decluttering image. Identify items from this canonical catalog:
[bluetooth speaker, wireless headphones, hardcover book, ceramic mug, ... (top 200 common items)].

For each item found, return:
- canonical_label: MUST be from the catalog above
- confidence: 0.0–1.0
- visible_condition_hint: one of [new, like_new, good, fair, poor]
- visible_brand: if identifiable

If an item is NOT in the catalog, use:
- canonical_label: "UNKNOWN"
- free_text_description: your best description
- confidence: 0.0–1.0

Return ONLY JSON."
```

**What this replaces:**
- Fuzzy label matching entirely (for catalog items)
- Inconsistent labeling across photos
- LLM hallucination of non-existent item names

**How it works:**
1. Populate the prompt with the top 200 most common taxonomy entries (by frequency in seed data + community sales).
2. LLM is constrained to the catalog → deterministic downstream lookups.
3. "UNKNOWN" items are handled separately: free-text description → embedding search → taxonomy alias matching → or LLM pricing if truly novel.
4. Condition and brand hints from vision reduce the burden on the user to manually input these.

**Degrees of freedom preserved:**
- LLM can still detect novel items (returns UNKNOWN + description).
- Catalog is dynamically generated per-deployment based on regional popularity.
- Users can override catalog matches: "That's not a bluetooth speaker, it's a smart home hub."

---

### 5. Embedding-Based Semantic Matching — Beyond String Fuzzy Matching

**New table: `taxonomy_embeddings`**

```sql
CREATE TABLE taxonomy_embeddings (
    taxonomy_id INTEGER PRIMARY KEY REFERENCES item_taxonomy(id),
    embedding BLOB NOT NULL,                 -- 384-dim float32 (all-MiniLM-L6-v2)
    model_version TEXT NOT NULL              -- "all-MiniLM-L6-v2:v1"
);
```

**What this replaces:**
- The O(n) substring scan in `PriceDatabase.get_price_range()`
- Failed lookups for semantically similar but textually different labels ("sneakers" vs "running shoes")

**How it works:**
1. Vision LLM returns a label (or UNKNOWN with free-text description).
2. Compute embedding of the label/description using a lightweight local model (all-MiniLM-L6-v2, ~20MB, runs in <50ms on CPU).
3. Query `taxonomy_embeddings` with cosine similarity:
   ```sql
   SELECT taxonomy_id, 
          (embedding * ?) / (||embedding|| * ||?||) as similarity
   FROM taxonomy_embeddings
   WHERE similarity > 0.82
   ORDER BY similarity DESC
   LIMIT 3;
   ```
4. If top match > 0.90 threshold: automatic canonicalization.
5. If 0.82–0.90: present top 3 options to user for disambiguation.
6. If < 0.82: treat as novel, hand to LLM.

**LLM involvement:**
- Zero. Embedding model is deterministic and local.

**Performance:**
- SQLite doesn't natively support vector search. Options:
  - **Option A:** Use `sqlite-vec` extension (C extension, ~100KB, supports vector search)
  - **Option B:** Brute-force in Python with numpy (acceptable for <10K vectors, ~5ms/query)
  - **Option C:** Separate `faiss` or `usearch` index file (~1MB for 10K 384-dim vectors)

---

## New Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER UPLOADS IMAGE                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  IMAGE INTAKE (deterministic: EXIF strip, resize, store)            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  VISION LLM                                                         │
│  Prompt includes top-200 taxonomy catalog                           │
│  Returns: [{canonical_label OR UNKNOWN, confidence, condition_hint}]│
│                                                                     │
│  BURDEN REDUCED: No pricing. No free-text invention. Constrained.   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DETERMINISTIC RESOLUTION (zero LLM)                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Alias matching  │→ │ Embedding search│→ │ Novel item bucket   │  │
│  │ (exact)         │  │ (semantic)      │  │ (LLM fallback)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
│           │                    │                    │               │
│           ▼                    ▼                    ▼               │
│     ┌──────────┐         ┌──────────┐         ┌──────────┐          │
│     │ canonical│         │ canonical│         │ LLM batch│          │
│     │ name     │         │ name     │         │ pricing  │          │
│     └──────────┘         └──────────┘         └──────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BATCH VALUATION (deterministic rules engine)                       │
│  Single query:                                                      │
│  SELECT taxonomy_id, base_low, base_median, base_high,              │
│         condition_multiplier, brand_premium                         │
│  FROM price_rules WHERE taxonomy_id IN (?, ?, ?)                   │
│                                                                     │
│  Apply rules per-item: condition × brand × age = final price       │
│                                                                     │
│  LLM involvement: ZERO for catalog items.                           │
│  LLM involvement: ONE batch call for all novel items.               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RESPONSE                                                           │
│  [{label, confidence, estimated_value_usd, category, safety_tag}]   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quantified Impact

### Before Refactor

| Metric | Value | Notes |
|--------|-------|-------|
| Avg items per photo | 5–8 | Typical cluttered desk/closet |
| DB lookups per photo | 5–8 | One per item (N+1) |
| LLM calls per photo (cache miss) | 5–8 | One per novel item |
| LLM calls per photo (cache hit) | 0 | But cache hits require prior LLM calls |
| Fuzzy string scans per lookup | O(n) ~6,072 rows | Linear scan with substring checks |
| Category assignment accuracy | ~17% | 6 hardcoded categories vs. 6,072 items |
| Vision label consistency | Low | "portable speaker" vs "bluetooth speaker" vs "JBL" |

### After Refactor

| Metric | Value | Notes |
|--------|-------|-------|
| DB lookups per photo | **1** | Single batch query with IN clause |
| LLM calls per photo (novel items) | **0–1** | Batch prompt for all UNKNOWN items |
| LLM calls per photo (catalog items) | **0** | Deterministic rules engine |
| Embedding lookups | **1** | Single vector similarity query |
| Category assignment accuracy | **>95%** | Full taxonomy with parent-child hierarchy |
| Vision label consistency | **High** | Constrained to canonical catalog |
| Avg latency (catalog items) | **<50ms** | Single SQLite query + rule math |
| Avg latency (with novel items) | **<500ms** | One batch LLM call for all novel items |

---

## Schema Migration Plan

### Phase 1: Add Taxonomy Tables (backward-compatible)

```sql
-- New tables
CREATE TABLE item_taxonomy (...);
CREATE TABLE item_taxonomy_aliases (...);
CREATE TABLE categories (...);
CREATE TABLE price_rules (...);
CREATE TABLE taxonomy_embeddings (...);

-- Migrate existing price_seed.json data
INSERT INTO item_taxonomy (canonical_name, normalized_name, category_id, ...)
SELECT label, normalized_label, inferred_category, ... FROM price_ranges WHERE source = 'seeded';

INSERT INTO item_taxonomy_aliases (taxonomy_id, alias, alias_normalized)
SELECT id, canonical_name, normalized_name FROM item_taxonomy;

INSERT INTO price_rules (taxonomy_id, base_low_price, base_median_price, base_high_price, ...)
SELECT t.id, pr.low_price, pr.median_price, pr.high_price, ...
FROM price_ranges pr
JOIN item_taxonomy t ON pr.normalized_label = t.normalized_name;
```

### Phase 2: Update Code Paths (feature-flagged)

```python
# valuation_service.py
if USE_TAXONOMY_LOOKUP:
    # New path: taxonomy → alias match → embedding search → price rules
    price_range = compute_price_from_rules(taxonomy_id, condition, brand, age)
else:
    # Old path: fuzzy substring → LLM fallback
    price_range = legacy_lookup(label)
```

### Phase 3: Remove Legacy Path

Once telemetry confirms new path handles >99% of lookups correctly:
- Remove `PriceDatabase._all_rows()` O(n) scan
- Remove `LlmPriceEstimator` from hot path (keep for admin/override use)
- Remove hardcoded `_category_map`

---

## What the LLM Keeps Doing (The Interesting Work)

| Task | Why the LLM Is the Right Tool | What We Give It |
|------|------------------------------|-----------------|
| **Vision detection** | Understanding cluttered photos requires visual reasoning | Constrained prompt with taxonomy catalog + "UNKNOWN" escape hatch |
| **Novel item pricing** | General knowledge for rare/unusual items | Batch prompt with multiple items. Results feed into price_rules table. |
| **Creative listing copy** | Writing compelling titles and descriptions | Item metadata + condition + brand. LLM generates human-readable copy. |
| **Trade negotiation (future)** | Context-aware, polite, ND-friendly messaging | Agent-to-agent or agent-to-human message generation with templates as guardrails |
| **Wishlist interpretation** | Natural language understanding | "I want something for my kitchen but nothing too big" → structured want-graph nodes |

---

## What the Database Does (The Boring Work)

| Task | Why the Database Is the Right Tool | What It Replaces |
|------|-----------------------------------|------------------|
| **Canonical item lookup** | Exact match + alias table + embedding similarity | Fuzzy substring O(n) scan |
| **Price computation** | Deterministic rules are fast, consistent, auditable | LLM temperature=0 price recall |
| **Category assignment** | Foreign key relationship, not a dictionary | 6-entry hardcoded `_category_map` |
| **Batch resolution** | SQL IN clause handles N items in one query | N+1 Python loop |
| **Safety checklist routing** | Tag-based lookup, deterministic | Hardcoded tag matching |
| **Marketplace category mapping** | Data-driven, not code-driven | Missing for most items today |

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Taxonomy coverage gaps | Start with all 6,072 seeded items. Add community-submitted aliases. Backfill from LLM outputs over time. |
| Embedding model drift | Store `model_version` with each embedding. Re-compute embeddings when model changes. |
| Over-constraining the vision LLM | "UNKNOWN" escape hatch always available. Telemetry tracks UNKNOWN rate; if >10%, expand catalog. |
| SQLite vector search performance | Use `sqlite-vec` or `faiss` for >10K vectors. For <10K, brute-force numpy is <5ms. |
| Rules engine too rigid | Rules are data, not code. Admin UI for adjusting multipliers. Community sales auto-adjust. |
| Migration complexity | Feature-flagged rollout. Old and new paths run in parallel. Telemetry decides when to cut over. |

---

## Acceptance Criteria (If Implemented)

1. **Latency:** 8-item photo analysis completes in <100ms for all catalog items (no LLM calls).
2. **Accuracy:** Category assignment >95% correct for seeded items (vs. ~17% today).
3. **Consistency:** Same item in different photos returns identical canonical label >95% of the time.
4. **Batch efficiency:** Single DB query handles all items in a photo. Zero N+1 patterns.
5. **Fallback:** Novel items (not in taxonomy) still work — single batch LLM call handles all UNKNOWN items.
6. **Backward compatibility:** Old API endpoints continue working during migration. Feature flag controls cutover.

---

## Open Questions

1. Should the vision LLM be given the full 6,072-item catalog or just the top 200? (Context window limits vs. coverage tradeoff)
2. Should we pre-compute embeddings for all 6,072 items at build time or at runtime?
3. How do we handle brand detection? Vision LLM hint + deterministic brand database? Or let LLM handle brands entirely?
4. Should condition assessment be purely vision-based, purely user-reported, or a hybrid?
5. What's the right threshold for embedding similarity auto-match vs. user disambiguation?

---

## Files to Create / Modify

### New Files
- `server/app/models/taxonomy.py` — Taxonomy + alias + embedding ORM/models
- `server/app/models/categories.py` — Category hierarchy
- `server/app/models/price_rules.py` — Price rules engine
- `server/app/services/taxonomy_resolver.py` — Alias matching + embedding search + canonicalization
- `server/app/services/embedding_service.py` — Local embedding model wrapper
- `server/app/data/taxonomy_seed.json` — Canonical taxonomy + aliases (derived from price_seed.json)

### Modified Files
- `server/app/services/price_database.py` — Add taxonomy-aware lookup, deprecate O(n) scan
- `server/app/services/valuation_service.py` — Add batch estimation, integrate rules engine
- `server/app/services/llm_price_estimator.py` — Move to batch-only, admin-override path
- `server/app/services/listing_service.py` — Replace hardcoded category map with taxonomy lookup
- `server/app/api/routes/analysis.py` — Batch revaluation, constrained vision prompt
- `server/app/services/analysis_adapter.py` — Update prompt to include taxonomy catalog

---

*This document is an architectural specification. It does not commit the team to implementation — it provides the blueprint if and when the decision is made to reduce LLM burden and improve pipeline determinism.*
