# DECLuTTER-AI 2026 Launch Plan — Porter Value Chain Edition

**Repo:** `Pastorsimon1798/DECLuTTER-AI`  
**Date:** April 22, 2026  
**Audience:** coding agents, maintainers, product reviewers, and launch operators  
**Purpose:** build DECLuTTER-AI into a launch-ready, neurodivergent-first decluttering and resale assistant that estimates item value, creates listings automatically, supports agents, and avoids unsafe automation.

---

## 0. Source-of-truth statement

This document is the implementation source of truth for the 2026 launch build.

The current repo already has a Flutter MVP direction: capture/review flow, timer-oriented decluttering flow, mock/TFLite-oriented detection scaffolding, and neurodivergent-friendly UX goals. This plan keeps the Flutter app and neurodivergent mission, but supersedes any older instruction that says the launch app should have **no backend, no provider APIs, no marketplace integrations, or no price estimates**.

### Non-negotiables

1. **Keep Flutter for the mobile client.** Do not rewrite the app in React Native, Swift, Kotlin, or web-only for v1.
2. **Do not keep the app Flutter-only.** A secure backend is required for valuation, OAuth, marketplace APIs, public listing pages, agent protocols, audit logs, and secrets.
3. **Do not scrape marketplaces.** Use official APIs or assisted listing kits.
4. **Do not publish silently.** The app can create listings automatically, but the user must review before public publishing.
5. **Do not put secrets in Flutter.** Marketplace tokens, OAuth secrets, API keys, and AI provider keys live only on the backend.
6. **Do not overclaim value.** Show “estimated asking price” or “likely resale range,” never “guaranteed money.”
7. **Do not optimize for resellers over neurodivergent users.** The primary outcome is relief, clarity, and cleared space.
8. **Do not expose private seller data to buyer agents.** Public agent endpoints expose only approved listing data.
9. **Do not let agents perform consequential actions without approval.** Publishing, reservation, buyer replies, meetup scheduling, and price changes require explicit user approval.
10. **Do not list prohibited or sensitive items.** Block unsafe categories and private-information photos.

---

## 1. One-sentence product strategy

**DECLuTTER-AI turns a clutter photo into a safe next action: donate, recycle, keep, or create a reviewed listing that shows the money likely available and can be published/exported with minimal cognitive load.**

Feature name for the resale workflow: **Cash-to-Clear**.

---

## 2. Is this the right stack in April 2026?

### 2.1 Final decision

**Flutter is the right client stack. Flutter-only is not the right product stack.**

The correct launch architecture is:

```text
Flutter mobile app
  + FastAPI backend
  + Postgres database
  + object storage
  + AI provider adapter
  + eBay official API adapter
  + assisted listing export adapters
  + public listing/agent endpoints
```

### 2.2 Final stack

| Layer | Launch choice | Why |
|---|---|---|
| Mobile app | Flutter stable / Dart stable | Existing repo, camera-first UX, iOS + Android from one codebase |
| Mobile state | Riverpod | Testable state, feature isolation, good for coding agents |
| Routing | GoRouter | Deep links for listing review, eBay return, and settings flows |
| Local persistence | Drift + SQLite | Offline session history, Maybe Bin, local drafts, undo |
| API client | Dio | Interceptors for Firebase ID token, App Check token, retries |
| Auth | Firebase Auth | Anonymous-first, upgradeable to email/Google/Apple |
| Backend abuse control | Firebase App Check | Reduces unauthorized client abuse of paid APIs |
| Backend | Python 3.12+ FastAPI | Strong API, AI, image-processing, validation, testing ecosystem |
| DB | Postgres | Relational fit for sessions, items, listings, tokens, agent permissions, audit logs |
| ORM/migrations | SQLAlchemy 2 + Alembic | Typed models and explicit migrations |
| Storage | Google Cloud Storage or S3-compatible private/public buckets | Private photos, public listing images, lifecycle rules |
| Secrets | Google Secret Manager or equivalent | No secrets in app or repo |
| Hosting | Google Cloud Run | Containerized, scalable backend and worker services |
| Async jobs | Cloud Tasks/PubSub worker | AI analysis, valuation, listing publish retries |
| AI | Backend-only OpenAI Responses API adapter for launch | Vision + structured outputs; provider can be swapped later |
| Marketplace direct publish | eBay Sell APIs | Most realistic official direct-listing path |
| Other marketplace support | Listing Kit export/share | Avoid unsupported bot posting or scraping |
| Agent support | MCP + A2A + OpenAPI + Schema.org JSON-LD | Friendly to user-owned agents and buyer agents |
| CI/CD | GitHub Actions | Fits the repo and coding-agent workflow |
| Infrastructure as code | Terraform | Reproducible staging/prod |

### 2.3 Anti-stack choices

Do not use:

- **Flutter-only backendless app** — cannot safely handle secrets, OAuth, public pages, or agents.
- **On-device VLM as primary launch intelligence** — too fragile for valuation/listing quality across devices.
- **Marketplace automation bots** — policy, security, and reliability risk.
- **Facebook Marketplace auto-posting in v1** — use listing kits unless official partner access is granted.
- **Generic chatbot UX** — the product must produce decisions and actions, not just conversation.

---

## 3. Porter’s Value Chain lens

Porter’s Value Chain breaks a company into strategically relevant activities that create value and competitive advantage. Applied to DECLuTTER-AI, the “finished product” is not just an app screen. It is this transformation:

```text
cluttered item
  -> recognized item
  -> decision-ready item
  -> valued item
  -> listing-ready item
  -> buyer-readable listing
  -> cleared space + recovered money + lower stress
```

### 3.1 Value chain summary

| Porter activity | DECLuTTER-AI equivalent | Value created | Build implication |
|---|---|---|---|
| Inbound logistics | Intake of photos, crops, user context, preferences, marketplace account status, buyer-agent signals | Converts overwhelming physical clutter into safe structured inputs | Capture flow, privacy scan, EXIF stripping, session model, storage |
| Operations | AI recognition, privacy checks, valuation, sellability scoring, listing generation, decision cards | Converts inputs into clear decisions and listing assets | FastAPI, AI adapter, eBay comps, listing generator, neurodivergent UX |
| Outbound logistics | eBay publishing, listing kits, public pages, public JSON, MCP/A2A/OpenAPI | Moves listing-ready data to buyer channels safely | eBay API, export/share, public listing packet, no scraping |
| Marketing & sales | Listing title, photos, price, category, public metadata, buyer-agent readability | Makes items discoverable and trustworthy | Schema.org, buyer templates, SEO, marketplace-appropriate copy |
| Service | Buyer Q&A relay, reminders, mark sold/donated, Maybe Bin, safety guidance, deletion | Helps users finish the clearing loop | Notifications, inquiry inbox, status sync, support and deletion flows |
| Firm infrastructure | Compliance, governance, privacy, app-store readiness, audit logs, cost controls | Creates trust and launch stability | Security, data deletion, audit_events, policy blocks |
| Human resource management | Founder/support workflows, neurodivergent user feedback, moderation process | Keeps product aligned with lived user needs | QA scripts, support queue, advisory feedback, issue labels |
| Technology development | Flutter, backend, AI, valuation, marketplace adapters, agent protocols | Creates defensible automation | Modular code, MCP/A2A, JSON-LD, tests, provider adapters |
| Procurement | AI provider, eBay developer access, cloud, storage, data sources, marketplace partnerships | Secures reliable inputs and channels | Quotas, secrets, vendor monitoring, fallback listing kits |

### 3.2 Strategic conclusion from Porter’s lens

The competitive advantage is **not** “AI writes listings.” That is easy to copy.

The defensible value chain is:

```text
neurodivergent-friendly photo intake
  + privacy-aware item recognition
  + value/effort scoring
  + official marketplace publishing
  + safe assisted exports
  + agent-readable public listing packets
  + seller approval gates
  + post-listing service loop
```

### 3.3 Margin definition for this product

For users:

```text
user value margin =
  recovered money
  + time saved
  + decision fatigue reduced
  + space cleared
  + shame avoided
  - effort required
  - privacy risk
  - platform friction
```

For the business:

```text
business margin =
  subscription / usage / marketplace-adjacent revenue
  - AI cost
  - cloud/storage cost
  - marketplace API friction
  - support/moderation cost
  - app-store/compliance cost
```

The business must never improve its margin by increasing user cognitive load.

### 3.4 Value-chain build priority

Porter’s lens changes the build order. Do not build a flashy listing writer first.

Build in this order:

```text
1. Safe photo intake
2. Structured item recognition
3. Value/effort scoring
4. Decision cards
5. Listing draft generation
6. eBay publish/export channels
7. Public listing packets
8. Buyer-agent inquiries
9. Post-listing service loop
```

Why:

- listing generation without safe intake creates privacy risk
- marketplace publishing without value scoring creates low-value selling clutter
- buyer-agent support without public listing structure creates fragile integrations
- service reminders without item status tracking create nagging instead of help

---

## 4. Product scope

### 4.1 Modes

#### Quick Clear

For overwhelmed users who do not want to sell today.

Features:

- capture/photo upload
- identify item groups
- recommend Keep / Donate / Trash / Recycle / Relocate / Maybe
- no marketplace setup
- can work without pricing if cloud valuation is disabled

#### Find Money

For users motivated by value.

Features:

- capture/photo upload
- identify sellable items
- estimate likely resale range
- show **Money on the Table** total
- rank top 3 sellable items
- suggest donate/recycle for low-value items

#### Listing Sprint

For users ready to sell.

Features:

- generate listing draft
- guided listing photo review
- price/condition/category editor
- eBay publish after review
- listing kit export for other platforms
- buyer templates
- public listing packet

### 4.2 Marketplace scope

| Platform | Launch behavior | Rationale |
|---|---|---|
| eBay | Direct listing through official APIs | Most realistic official direct publish path |
| Facebook Marketplace | Listing Kit only unless accepted into partner program | Avoid unsupported auto-posting |
| OfferUp | Listing Kit + export support | Assisted workflow only |
| Mercari personal | Listing Kit only | Do not assume public personal-listing API |
| Mercari Shops | Future optional adapter for shop users | Token/shop API only, not default consumer flow |
| Craigslist/others | Listing Kit only | No bot posting |

### 4.3 Definition of “automatic listing”

Automatic listing means:

1. App identifies the item.
2. App estimates resale value.
3. App generates title, description, price, category, condition, photos, and buyer messages.
4. User reviews and confirms.
5. Backend publishes to eBay or exports a listing kit.

It does **not** mean silent publishing.

---

## 5. Neurodivergent-first UX rules

### 5.1 Screen rules

Every screen must have:

- one primary action
- no more than two secondary actions
- large touch targets
- dynamic type support
- VoiceOver/TalkBack labels
- visible progress
- undo where possible
- “Not today” escape route
- “Donate instead” for sellable items
- “I’m stuck” decision rescue

### 5.2 Language rules

Use:

- “zone”
- “items”
- “not worth your energy today”
- “save for later”
- “good enough to post”
- “estimated asking price”

Avoid:

- “mess”
- “junk”
- “lazy”
- “failed”
- “perfect listing”
- “guaranteed value”

### 5.3 Energy modes

```text
I have 2 minutes
I have 5 minutes
I have 10 minutes
I can list items today
```

Behavior:

| Energy mode | Behavior |
|---|---|
| 2 minutes | one easiest clear action only |
| 5 minutes | top 1 sellable item only |
| 10 minutes | top 3 sellable items |
| Can list today | Listing Sprint queue enabled |

### 5.4 “I’m stuck” algorithm

```text
if prohibited/high-risk:
  suggest safe disposal or keep private
elif value_high_usd < 10:
  suggest Donate/Reycle
elif user_energy low and effort medium/high:
  suggest Not Today or Donate
elif confidence low:
  suggest Maybe Bin
else:
  suggest Create Listing Draft
```

---

## 6. Architecture

### 6.1 System flow

```text
Flutter app
  -> capture photo
  -> strip EXIF
  -> privacy scan / user review
  -> upload to object storage through backend
  -> backend AI item analysis
  -> eBay comps + valuation
  -> decision cards
  -> listing draft
  -> user review
  -> eBay publish OR listing kit export
  -> public listing packet / buyer-agent endpoint
  -> service loop: Q&A, reminders, mark sold/donated
```

### 6.2 Monorepo structure

```text
DECLuTTER-AI/
  README.md
  LAUNCH_PLAN_2026.md
  app/
    lib/
      main.dart
      src/
        core/
          api/
          auth/
          db/
          design/
          routing/
          errors/
        features/
          capture/
          privacy_scan/
          session/
          detect/
          valuation/
          decide/
          listing/
          marketplace/
          agent/
          history/
          settings/
    test/
    integration_test/
  server/
    app/
      main.py
      api/routes/
      core/
      db/
      schemas/
      services/
        ai/
        image/
        valuation/
        listing/
        marketplace/
        agents/
    tests/
    pyproject.toml
    Dockerfile
  infra/
    terraform/
  docs/
    launch/
    agents/
    marketplace/
```

### 6.3 Backend requirements

Use Python 3.12+ FastAPI.

Required backend modules:

```text
analysis.py
valuation.py
listing_drafts.py
marketplace_ebay.py
public_listings.py
mcp.py
a2a.py
user_data.py
```

Use:

```text
FastAPI
Pydantic v2
SQLAlchemy 2
Alembic
asyncpg
httpx
Pillow
OpenAI SDK
firebase-admin
cryptography
tenacity
pytest
respx
ruff
mypy
```

### 6.4 Environment variables

```bash
APP_ENV=local|staging|production
DATABASE_URL=postgresql+asyncpg://...
PUBLIC_BASE_URL=https://api.example.com
FIREBASE_PROJECT_ID=...
FIREBASE_APP_CHECK_REQUIRED=true
GCS_BUCKET_PRIVATE=declutter-private-prod
GCS_BUCKET_PUBLIC=declutter-public-prod
OPENAI_API_KEY=...
OPENAI_MODEL_ITEM_ANALYSIS=gpt-5.4-mini
OPENAI_MODEL_LISTING=gpt-5.4-mini
EBAY_ENV=sandbox|production
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_REDIRECT_URI=...
EBAY_MARKETPLACE_ID=EBAY_US
TOKEN_ENCRYPTION_KEY=...
AGENT_CARD_SIGNING_KEY=...
```

Production startup must fail if required secrets are missing.

---

## 7. Core data model

### 7.1 Main tables

```sql
users(
  id uuid primary key,
  firebase_uid text unique not null,
  email text,
  created_at timestamptz,
  deleted_at timestamptz
);

user_preferences(
  user_id uuid primary key references users(id),
  default_energy_mode text not null default 'ten_minutes',
  telemetry_opt_in boolean not null default false,
  allow_personal_agent_read boolean not null default false,
  allow_personal_agent_write_drafts boolean not null default false,
  allow_personal_agent_request_publish boolean not null default false
);

declutter_sessions(
  id uuid primary key,
  user_id uuid references users(id),
  zone_label text not null,
  mode text not null,
  status text not null,
  energy_mode text not null,
  original_image_storage_key text,
  sanitized_image_storage_key text,
  money_low_usd numeric(10,2),
  money_high_usd numeric(10,2),
  created_at timestamptz,
  updated_at timestamptz,
  finished_at timestamptz,
  deleted_at timestamptz
);

detected_items(
  id uuid primary key,
  session_id uuid references declutter_sessions(id),
  user_id uuid references users(id),
  label text not null,
  normalized_label text not null,
  category text not null,
  description text not null,
  brand text,
  model text,
  quantity int not null default 1,
  bbox_json jsonb,
  crop_storage_key text,
  detection_confidence text not null,
  condition_guess text not null,
  sensitive_flags jsonb not null default '[]',
  prohibited_flags jsonb not null default '[]',
  listing_allowed boolean not null default true,
  listing_block_reason text,
  created_at timestamptz,
  updated_at timestamptz
);

valuations(
  id uuid primary key,
  item_id uuid references detected_items(id),
  low_amount numeric(10,2) not null,
  high_amount numeric(10,2) not null,
  recommended_price numeric(10,2) not null,
  confidence text not null,
  source text not null,
  basis text not null,
  comp_count int not null default 0,
  comps_json jsonb not null default '[]',
  effort_score text not null,
  sellability_score int not null,
  recommended_action text not null,
  created_at timestamptz
);

listing_drafts(
  id uuid primary key,
  item_id uuid references detected_items(id),
  user_id uuid references users(id),
  platform text not null,
  status text not null,
  title text not null,
  description text not null,
  condition text not null,
  category_name text not null,
  category_external_id text,
  price_amount numeric(10,2) not null,
  currency text not null default 'USD',
  quantity int not null default 1,
  photo_storage_keys jsonb not null default '[]',
  shipping_plan_json jsonb not null default '{}',
  pickup_plan_json jsonb not null default '{}',
  buyer_templates_json jsonb not null default '{}',
  agent_visibility text not null default 'private',
  user_reviewed_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz
);

marketplace_accounts(
  id uuid primary key,
  user_id uuid references users(id),
  platform text not null,
  external_account_id text,
  encrypted_access_token bytea,
  encrypted_refresh_token bytea,
  token_expires_at timestamptz,
  scopes_json jsonb not null default '[]',
  status text not null,
  created_at timestamptz,
  updated_at timestamptz,
  unique(user_id, platform)
);

marketplace_listings(
  id uuid primary key,
  draft_id uuid references listing_drafts(id),
  platform text not null,
  external_listing_id text,
  external_offer_id text,
  external_inventory_sku text,
  public_url text,
  status text not null,
  published_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz
);

public_listing_pages(
  id uuid primary key,
  draft_id uuid references listing_drafts(id),
  slug text unique not null,
  public_json jsonb not null,
  schema_org_json jsonb not null,
  status text not null,
  created_at timestamptz,
  updated_at timestamptz
);

buyer_inquiries(
  id uuid primary key,
  public_listing_id uuid references public_listing_pages(id),
  seller_user_id uuid references users(id),
  buyer_display_name text,
  buyer_contact_relay text,
  buyer_agent_id text,
  message text not null,
  structured_offer_json jsonb,
  status text not null,
  created_at timestamptz,
  seller_reviewed_at timestamptz
);

agent_permissions(
  id uuid primary key,
  user_id uuid references users(id),
  agent_subject text not null,
  scopes_json jsonb not null,
  status text not null,
  created_at timestamptz,
  expires_at timestamptz,
  revoked_at timestamptz
);

audit_events(
  id uuid primary key,
  user_id uuid references users(id),
  actor_type text not null,
  actor_id text,
  event_type text not null,
  resource_type text not null,
  resource_id uuid,
  metadata_json jsonb not null default '{}',
  created_at timestamptz
);
```

### 7.2 Required enums

```text
mode: quick_clear | find_money | listing_sprint
session_status: created | uploaded | analyzing | analysis_ready | deciding | listing_sprint | finished | error
confidence: low | medium | high
condition_guess: new_open_box | used_like_new | used_good | used_fair | for_parts | unknown
recommended_action: sell_online | sell_local | bundle | donate | recycle | trash | keep_private | maybe
platform: ebay | facebook_marketplace_assisted | offerup_assisted | mercari_assisted | mercari_shops | craigslist_assisted | generic
listing_status: draft | needs_review | ready_to_publish | publishing | published | exported | rejected | archived | error
agent_visibility: private | public_agent_readable | marketplace_only
```

---

## 8. API contracts

### 8.1 Auth

Private endpoints require:

```http
Authorization: Bearer <Firebase ID token>
X-Firebase-AppCheck: <App Check token>
```

Public listing endpoints are unauthenticated but rate-limited.

### 8.2 Error format

```json
{
  "error": {
    "code": "string_snake_case",
    "message": "User-safe sentence.",
    "details": {},
    "request_id": "uuid"
  }
}
```

Never return raw eBay/OpenAI/internal errors to users.

### 8.3 Private endpoints

```http
POST /v1/sessions
POST /v1/sessions/{session_id}/images
POST /v1/sessions/{session_id}/analyze
GET  /v1/sessions/{session_id}
PATCH /v1/items/{item_id}/decision
POST /v1/items/{item_id}/value
POST /v1/items/{item_id}/listing-drafts
PATCH /v1/listing-drafts/{draft_id}
POST /v1/listing-drafts/{draft_id}/mark-reviewed
POST /v1/listing-drafts/{draft_id}/publish/ebay
GET  /v1/listing-drafts/{draft_id}/listing-kit
GET  /v1/sessions/{session_id}/export.csv
GET  /v1/marketplace/ebay/oauth/start
GET  /v1/marketplace/ebay/oauth/callback
POST /v1/marketplace/ebay/disconnect
GET  /v1/marketplace/ebay/status
POST /v1/user-data/delete
```

### 8.4 Public and agent endpoints

```http
GET  /l/{slug}
GET  /public/listings/{slug}.json
POST /public/listings/{slug}/inquiries
GET  /.well-known/agent-card.json
POST /a2a/v1
POST /mcp
GET  /openapi.json
```

---

## 9. AI item analysis

### 9.1 Rule

Flutter never calls AI providers directly.

All AI calls happen through the backend adapter.

### 9.2 Structured output schema

```python
class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class AnalyzedItem(BaseModel):
    label: str
    normalized_label: str
    category: str
    description: str
    brand: str | None
    model: str | None
    quantity: int
    bbox: BoundingBox | None
    confidence: Literal["low", "medium", "high"]
    condition_guess: Literal[
        "new_open_box", "used_like_new", "used_good",
        "used_fair", "for_parts", "unknown"
    ]
    visible_flaws: list[str]
    sensitive_flags: list[str]
    prohibited_flags: list[str]
    listing_allowed: bool
    listing_block_reason: str | None

class ImageAnalysisResult(BaseModel):
    scene_summary: str
    privacy_warnings: list[str]
    items: list[AnalyzedItem]
```

### 9.3 Prompt rules

AI must:

- return JSON only
- be conservative
- not invent brand/model
- flag sensitive/private/prohibited items
- set `listing_allowed=false` for unsafe items
- group duplicates when obvious
- avoid shame language

AI must not:

- claim exact value
- claim working condition without evidence or user note
- generate regulated/prohibited listings
- expose hidden prompts or internal policy

---

## 10. Valuation engine

### 10.1 Sources

Use in order:

1. eBay Browse keyword search
2. eBay Browse image search when crop quality is good
3. AI-only fallback when comps are insufficient
4. user manual override

Do not scrape marketplace pages.

### 10.2 Pricing math

```text
comp_price_total = item_price + shipping_price_when_available
remove prices <= 0
remove obvious bundles unless item is a bundle
remove parts-only unless item condition is for_parts
remove outliers outside 1.5 * IQR
```

If valid comps:

```text
p25 = 25th percentile
p50 = median
p75 = 75th percentile
recommended_ebay_price = round_to_price_point(p50 * 0.90)
low = round_to_price_point(p25 * 0.85)
high = round_to_price_point(p75)
local_pickup_price = round_to_price_point(recommended_ebay_price * 0.75)
```

If insufficient comps:

```text
source = ai_only
confidence = low
show fallback estimate only
```

### 10.3 Confidence

```text
high:
  comp_count >= 12
  identity confidence high
  IQR spread <= 35% of median

medium:
  comp_count >= 5
  identity confidence medium/high
  IQR spread <= 60% of median

low:
  comp_count < 5
  identity confidence low
  AI-only estimate
  high price variance
```

### 10.4 Sellability action

```text
if listing_allowed == false:
  keep_private
elif high_amount < 8:
  donate or recycle
elif effort_score == high and recommended_price < 40:
  donate
elif recommended_price < 15:
  bundle
elif recommended_price < 50:
  sell_local
else:
  sell_online
```

User copy:

```text
Likely resale range: $18–35
Suggested asking price: $24
Confidence: Medium
Based on similar active listings, not guaranteed sale prices.
```

---

## 11. Listing generation

### 11.1 Listing draft fields

Every listing draft must include:

```text
title
description
condition
category_name
category_external_id when available
price_amount
currency
quantity
photos
visible_flaws
shipping_plan
pickup_plan
buyer_templates
required_user_checks
```

### 11.2 Title rules

Title must:

- be under 80 characters
- include brand/model when known
- include item type
- avoid fake scarcity
- avoid emojis
- avoid all caps
- avoid unverified claims

### 11.3 Description format

```text
1. What it is
2. Condition
3. What is included
4. Known flaws or unknowns
5. Pickup/shipping note
```

### 11.4 Required review checks

Before publish:

```text
I confirmed the title is accurate.
I confirmed the condition is accurate.
I confirmed the photos do not show private information.
I confirmed the item is allowed on this marketplace.
I approve the price.
```

For electronics:

```text
I confirmed whether the item is tested.
I confirmed whether accessories are included.
```

---

## 12. eBay integration

### 12.1 Flow

```text
1. User connects eBay through OAuth.
2. Backend stores encrypted tokens.
3. Backend checks seller account/policies.
4. User creates/reviews listing draft.
5. Backend creates inventory SKU.
6. Backend creates eBay offer.
7. User approves final publish.
8. Backend publishes offer.
9. App stores external listing ID and URL.
```

### 12.2 Backend endpoints

```http
GET  /v1/marketplace/ebay/oauth/start
GET  /v1/marketplace/ebay/oauth/callback
POST /v1/marketplace/ebay/disconnect
GET  /v1/marketplace/ebay/status
POST /v1/listing-drafts/{draft_id}/publish/ebay
```

### 12.3 SKU format

```text
DECLUTTER-{user_short_id}-{item_short_id}-{yyyyMMddHHmm}
```

### 12.4 Preconditions for publish

- draft status is `ready_to_publish`
- user owns draft
- user connected eBay
- eBay token valid or refreshable
- seller policies available
- listing allowed
- photos approved
- final confirmation true

If missing policy:

```json
{
  "error": {
    "code": "ebay_policy_missing",
    "message": "Your eBay account needs a shipping, payment, or return policy before this can be published.",
    "details": {"missing": ["fulfillment_policy"]}
  }
}
```

---

## 13. Assisted marketplace listing kits

For Facebook Marketplace, OfferUp, Mercari personal, Craigslist, and similar platforms:

Allowed:

- copy title
- copy description
- copy price
- share photos
- export CSV/XLSX when official flow supports it
- open marketplace app/site

Forbidden:

- bot posting
- browser automation
- credential capture
- scraping
- CAPTCHA bypass

Listing Kit response:

```json
{
  "title": "Logitech Wireless Keyboard Black Used Tested",
  "description": "Used Logitech wireless keyboard in good working condition.",
  "price": "24.00 USD",
  "condition": "Used - Good",
  "category": "Computer Keyboards & Keypads",
  "copy_blocks": {
    "facebook_marketplace": "copy-ready text",
    "offerup": "copy-ready text",
    "mercari": "copy-ready text",
    "generic": "copy-ready text"
  }
}
```

---

## 14. Agent-friendly design

### 14.1 Agent types

#### User’s own agent

Can help the seller:

- review sessions
- identify top-value items
- generate listing drafts
- export listing kits
- request publish approval

Cannot:

- publish directly
- message buyers directly
- schedule pickup directly
- change price without approval

#### Buyer’s agent

Can:

- read public listing JSON
- parse Schema.org Product/Offer
- ask a structured question through relay

Cannot:

- see private seller data
- reserve item
- purchase directly
- schedule meetup
- bypass marketplace flows

### 14.2 MCP tools

Expose MCP at:

```http
POST /mcp
```

Tools:

```text
declutter.list_sessions
declutter.get_session
declutter.create_session_from_uploaded_image
declutter.estimate_item_value
declutter.generate_listing_draft
declutter.get_listing_draft
declutter.update_listing_draft
declutter.request_publish_listing
declutter.export_listing_kit
declutter.get_public_listing_packet
```

`declutter.request_publish_listing` must return only:

```json
{
  "status": "user_approval_required",
  "approval_url": "declutter://listing-drafts/{id}/review"
}
```

### 14.3 A2A support

Expose:

```http
GET /.well-known/agent-card.json
POST /a2a/v1
```

Public skills:

```text
read_public_listing
ask_listing_question
```

Private seller skills require authentication and scopes.

### 14.4 Public listing packet

```http
GET /public/listings/{slug}.json
```

Returns:

```json
{
  "schema_version": "2026-04-22",
  "title": "Logitech K380 Wireless Keyboard Black Used",
  "description": "Used Logitech wireless keyboard in good working condition.",
  "price": {"amount": "24.00", "currency": "USD"},
  "condition": "Used - Good",
  "category": "computer_accessory",
  "brand": "Logitech",
  "model": "K380",
  "photos": [{"url": "https://cdn.example.com/listing/photo1.jpg", "alt": "Front view"}],
  "availability": "available",
  "fulfillment": {"local_pickup": true, "shipping_available": false},
  "agent_inquiry": {
    "enabled": true,
    "endpoint": "https://api.example.com/public/listings/slug/inquiries",
    "allowed_actions": ["ask_question"],
    "disallowed_actions": ["purchase", "reserve", "schedule_pickup"]
  },
  "seller_privacy": {
    "direct_contact_hidden": true,
    "location_precision": "city_only"
  }
}
```

### 14.5 Schema.org JSON-LD

Public listing pages must include `Product` with nested `Offer` JSON-LD.

Do not expose private seller contact info in JSON-LD.

---

## 15. Safety and prohibited items

### 15.1 Blocked categories

Do not generate publishable listings for:

- firearms, ammunition, firearm parts
- explosives/fireworks
- weapons
- alcohol
- tobacco/nicotine/vapes
- recreational drugs/CBD/THC
- prescription medication
- regulated medical devices
- counterfeit goods
- stolen goods
- government IDs
- payment cards
- personal documents/mail/tax/bank papers
- live animals
- recalled products
- hazardous chemicals
- adult sexual products
- extremist/terrorist merchandise
- anything marketplace policy forbids

### 15.2 Sensitive photo flags

```text
face_visible
address_visible
mail_visible
prescription_label_visible
payment_card_visible
license_plate_visible
child_visible
private_document_visible
screen_with_personal_info_visible
```

If any flag is present:

- warn user
- require crop/retake/confirmation
- block one-tap publish until resolved
- log audit event

User copy:

```text
This photo may show private info.
Crop or retake before listing.
```

---

## 16. Work packages

### WP0 — Repo alignment

Tasks:

- add this plan to repo
- update README to point to it
- mark older conflicting docs as superseded

Acceptance:

- coding agents have one source of truth
- no doc says live marketplace integration is forbidden

### WP1 — Flutter architecture

Tasks:

- upgrade Flutter stable
- add Riverpod, GoRouter, Dio, Drift
- preserve capture and timer flow
- add feature modules

Acceptance:

- app launches
- camera capture works
- timer works
- local DB initialized

### WP2 — Backend scaffold

Tasks:

- create FastAPI server
- add health endpoints
- add SQLAlchemy/Alembic
- add Dockerfile
- add tests

Acceptance:

- `/healthz` returns 200
- migrations run
- tests pass

### WP3 — Auth and App Check

Tasks:

- Firebase Auth mobile setup
- anonymous sign-in
- backend verifies ID token
- backend verifies App Check token

Acceptance:

- unauthenticated private requests fail
- authenticated requests create user row

### WP4 — Image intake and privacy

Tasks:

- strip EXIF
- upload photo
- store private object
- privacy scan/warning

Acceptance:

- oversized files rejected
- private info warning appears
- upload audit event logged

### WP5 — AI item analysis

Tasks:

- AI provider adapter
- structured output schema
- item persistence
- prohibited item detection

Acceptance:

- fixture image returns structured items
- prohibited fixture blocked
- malformed AI output safely rejected

### WP6 — Valuation

Tasks:

- eBay comps adapter
- image search adapter
- pricing math
- confidence label
- sellability score

Acceptance:

- item with comps returns value range
- insufficient comps returns low confidence
- UI labels estimates correctly

### WP7 — Decision flow

Tasks:

- decision cards
- energy modes
- Maybe Bin
- undo
- Money on the Table

Acceptance:

- decisions persist
- user can finish a session without selling

### WP8 — Listing draft generator

Tasks:

- listing schema
- generation prompt
- edit/review UI
- buyer templates

Acceptance:

- draft generated
- title under 80 chars
- review required before publish

### WP9 — eBay integration

Tasks:

- OAuth
- encrypted token storage
- inventory item creation
- offer creation
- publish after approval

Acceptance:

- sandbox publish works
- unreviewed draft cannot publish
- prohibited item cannot publish

### WP10 — Assisted exports

Tasks:

- listing kit endpoint
- copy/share UI
- CSV export

Acceptance:

- Facebook/Mercari/OfferUp kits work
- no bot posting exists

### WP11 — Public listing pages

Tasks:

- slug generation
- public HTML
- JSON packet
- Schema.org JSON-LD
- inquiry endpoint

Acceptance:

- buyer agents can read public listing
- private seller data hidden

### WP12 — MCP user-agent support

Tasks:

- MCP endpoint
- scoped tools
- audit logging

Acceptance:

- disabled MCP returns 403
- missing scope returns 403
- publish tool only requests approval

### WP13 — A2A buyer-agent support

Tasks:

- Agent Card
- public read task
- question relay task

Acceptance:

- buyer agents can discover listing skills
- buyer agents cannot reserve/purchase/schedule

### WP14 — Safety hardening

Tasks:

- prohibited policy
- sensitive image policy
- data deletion
- audit logs

Acceptance:

- prohibited items blocked
- data deletion works
- safety blocks logged

### WP15 — Launch QA

Tasks:

- manual QA
- accessibility QA
- app-store privacy forms
- production deploy

Acceptance:

- capture -> value -> draft -> publish works
- public listing agent packet works
- all CI green

---

## 17. Metrics through Porter’s lens

### Inbound logistics metrics

```text
photo_to_analysis_started_seconds
upload_success_rate
privacy_warning_rate
abandoned_before_upload_rate
```

### Operations metrics

```text
analysis_success_rate
valuation_confidence_distribution
decision_completion_rate
listing_draft_generation_rate
blocked_listing_rate
```

### Outbound logistics metrics

```text
draft_to_publish_rate
ebay_publish_success_rate
export_listing_kit_rate
public_listing_packet_fetch_count
buyer_agent_inquiry_count
```

### Marketing/sales metrics

```text
listing_page_view_count
buyer_inquiry_rate
listing_title_edit_rate
price_edit_rate
sell_through_rate_when_available
```

### Service metrics

```text
mark_sold_or_donated_rate
maybe_bin_resolution_rate
buyer_response_time
notification_opt_out_rate
user_reported_stress_after_listing
```

### Support activity metrics

```text
security_incident_count
privacy_deletion_completion_time
backend_cost_per_analysis
api_quota_usage
accessibility_issue_count
mcp_tool_success_rate
a2a_task_success_rate
```

---

## 18. Manual QA script

### Quick Clear

1. Fresh install.
2. Sign in anonymously.
3. Start Quick Clear.
4. Take photo.
5. Confirm privacy notice.
6. Confirm item cards appear.
7. Tap “I’m stuck.”
8. Confirm one low-friction action.
9. Mark Donate.
10. Undo.
11. Mark Maybe.
12. Finish session.
13. Relaunch app and confirm history.

### Find Money

1. Start Find Money.
2. Upload fixture with three sellable items.
3. Confirm Money on the Table appears.
4. Confirm confidence labels.
5. Tap “Why this price?”
6. Confirm copy says estimates are based on active listings, not guaranteed sales.
7. Donate low-value item.
8. Confirm total updates.

### Listing Sprint

1. Select item.
2. Generate eBay listing draft.
3. Confirm title/description/condition/price/photos.
4. Try publish before review; confirm blocked.
5. Complete review checklist.
6. Publish to eBay sandbox.
7. Confirm marketplace URL stored.
8. Confirm public listing JSON exists.

### Agent flow

1. MCP disabled; call tool; confirm 403.
2. Enable read scope; call list sessions; confirm success.
3. Call draft generation without scope; confirm 403.
4. Enable create draft; confirm draft created.
5. Request publish; confirm approval URL only.
6. Fetch Agent Card.
7. A2A read public listing.
8. A2A ask listing question.
9. Confirm seller review required.

### Safety flow

1. Upload photo with address label.
2. Confirm warning.
3. Try publish; confirm blocked.
4. Upload prohibited fixture.
5. Confirm listing generation blocked.
6. Confirm safe next action shown.

---

## 19. Definition of launch-ready

The app is launch-ready only when:

- [ ] Flutter app passes analysis/tests.
- [ ] Backend passes tests/type checks.
- [ ] Infrastructure is reproducible.
- [ ] Auth/App Check protect private APIs.
- [ ] AI analysis returns structured items.
- [ ] eBay comps valuation works.
- [ ] Estimates are labeled correctly.
- [ ] Listing drafts generate automatically.
- [ ] User review required before publish.
- [ ] eBay sandbox and production controlled publish work.
- [ ] Non-eBay flows use assisted listing kits only.
- [ ] Prohibited items blocked.
- [ ] Sensitive photo warnings work.
- [ ] Public listing pages include JSON-LD.
- [ ] Public listing JSON works.
- [ ] MCP tools work with scopes.
- [ ] A2A Agent Card and public task work.
- [ ] Buyer agents cannot purchase/reserve/schedule.
- [ ] User can delete data.
- [ ] Accessibility QA passes.
- [ ] App-store privacy docs are ready.

---

## 20. References checked

### Repo

- `https://github.com/Pastorsimon1798/DECLuTTER-AI`
- `https://raw.githubusercontent.com/Pastorsimon1798/DECLuTTER-AI/main/README.md`
- `https://raw.githubusercontent.com/Pastorsimon1798/DECLuTTER-AI/main/IMPLEMENTATION_PLAN_2026.md`
- `https://raw.githubusercontent.com/Pastorsimon1798/DECLuTTER-AI/main/ADHD_Vision_Organizer_MVP_Docs_v0.1.md`

### Porter Value Chain

- `https://www.isc.hbs.edu/strategy/business-strategy/Pages/the-value-chain.aspx`
- `https://www.ifm.eng.cam.ac.uk/research/dstools/value-chain-/`
- `https://online.hbs.edu/blog/post/what-is-value-chain-analysis`

### Flutter / platform / security

- `https://docs.flutter.dev/release/release-notes`
- `https://blog.flutter.dev/whats-new-in-flutter-3-41-302ec140e632`
- `https://docs.flutter.dev/app-architecture/guide`
- `https://docs.flutter.dev/app-architecture/recommendations`
- `https://firebase.google.com/docs/app-check`
- `https://mas.owasp.org/MASVS/`

### AI / marketplaces / agents

- `https://developers.openai.com/api/reference/responses/overview/`
- `https://developers.openai.com/api/docs/guides/images-vision`
- `https://developers.openai.com/api/docs/guides/structured-outputs`
- `https://developer.ebay.com/api-docs/buy/browse/overview.html`
- `https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/searchByImage`
- `https://developer.ebay.com/api-docs/sell/inventory/resources/offer/methods/createOffer`
- `https://developers.facebook.com/docs/marketplace/partnerships/`
- `https://help.business.offerup.com/hc/en-us/articles/27947563430292-Create-listings-with-Business-Portal`
- `https://api.mercari-shops.com/docs/index.html`
- `https://modelcontextprotocol.io/specification/2025-06-18`
- `https://a2a-protocol.org/latest/specification/`
- `https://schema.org/Product`
- `https://schema.org/Offer`

---

## 21. Final strategic instruction

Build the value chain, not just the features.

The launch product succeeds when a user can say:

> “I took one photo, saw what was worth money, made a listing without spiraling, and cleared the rest.”

The business succeeds when that user outcome is produced safely, repeatedly, with official marketplace paths and agent-readable listings.

