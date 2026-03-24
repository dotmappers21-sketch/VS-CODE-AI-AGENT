# Architecture Overview — Lead Generation Pro

## System Design

Lead Generation Pro is a multi-phase pipeline that turns a single industry keyword into enriched, ranked B2B leads ready for outreach. It is built as a Python desktop application with an optional React-based API monitoring dashboard.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interface (tkinter)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│   │ Country/Ind. │  │ API Key Grid │  │  Progress Log + Cancel  │  │
│   └──────────────┘  └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                               │  Spawns background Thread
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LeadGeneratorPipeline (Core)                      │
│                                                                      │
│  Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6│
│  Seeds      Expand      Discover    Enrich      Dedupe     Export    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Map

### Python Backend (`lead_generator_v5.4.py`)

| Class | Responsibility |
|---|---|
| `RateLimiter` | Token-bucket rate limiter with `threading.Lock` for thread-safe API call pacing |
| `SemrushAPI` | Keyword expansion — organic + adwords keyword research |
| `SerpApiClient` | Domain discovery from Google SERP results + full-name fallback searches |
| `ApolloAPI` | People search, org enrichment, person enrichment (primary data source) |
| `LushaAPI` | Person + company enrichment (secondary data source) |
| `WebScraper` | Homepage + /contact page scraping for phones, emails, names |
| `LeadGeneratorPipeline` | Orchestrates all 6 phases; owns `ThreadPoolExecutor` for Phase 4 |
| `LeadGeneratorGUI` | tkinter GUI — collects inputs, drives pipeline, handles cancel |

### Dashboard Backend (`dashboard/server/index.js`)

| Module | Responsibility |
|---|---|
| `GET /api/credits` | Returns cached credit data (5-min TTL) for Apollo, Lusha, Semrush |
| `POST /api/credits/refresh` | Force-clears cache and re-fetches all three APIs in parallel |
| Credit fetchers | `fetchApolloCredits`, `fetchLushaCredits`, `fetchSemrushCredits` — each normalise raw API response into `{remaining, total, percentage, remainingSearches, resetDate, usageRate}` |

### Dashboard Frontend (`dashboard/client/src/`)

| File | Responsibility |
|---|---|
| `useCreditsContext.js` | React hook — fetches on mount, auto-refreshes every 30s, exposes `{data, loading, error, refresh}` |
| `CreditsDashboard.jsx` | Main UI — summary card, per-service cards with progress bars, alert banners |
| `App.jsx` | Root component wrapping `CreditsDashboard` |

---

## Data Flow — Phase by Phase

### Phase 1 — Seed Keywords
```
Industry selection (e.g. "Dentist")
    → SEED_KEYWORDS["dentist"] = ["dentist near me", "dental clinic", ...]
```
Seeds are hard-coded keyword lists per industry. No API call here.

### Phase 2 — SEMrush Keyword Expansion
```
Seed keywords
    → SemrushAPI.organic_keywords(kw, country)  [rate: 0.8s]
    → SemrushAPI.adwords_keywords(kw, country)  [rate: 0.8s]
    → Deduplicate → top ~30 keywords
```
Expands seeds to related commercial-intent keywords used by real businesses.

### Phase 3 — Domain Discovery
```
Expanded keywords
    → SemrushAPI.organic_results(kw, country)   → domains
    → SerpApiClient.search_domains(kw, country) → domains  [rate: 0.8s]
    → Deduplicate → up to 150 unique domains
```

### Phase 4 — Multi-source Enrichment (Parallel)

This is the most complex phase. Each domain is processed by `_enrich_single_domain()` which runs as an independent task inside a `ThreadPoolExecutor(max_workers=8)`.

```
Domain (e.g. "smithdental.com.au")
    │
    ├─ Step 1: ApolloAPI.org_enrich(domain)
    │       → company_name, phone, industry
    │
    ├─ Step 2: ApolloAPI.people_search(domain)
    │       → [{first_name, last_name, title, email, linkedin_url}]
    │       └─ Step 2b: ApolloAPI.enrich_person(linkedin_url)  [if last_name missing]
    │       └─ Step 2c: name resolution from company/domain/linkedin
    │
    ├─ Step 3: WebScraper.scrape(domain, ["/", "/contact"])
    │       → phone, email, scraped_names
    │
    ├─ Step 4: LushaAPI.person_enrich(first, last, domain)
    │       → email, phone, role
    │
    ├─ Step 5: LushaAPI.company_info(domain)
    │       → company_name, phone
    │
    └─ Step 6: SerpApiClient.business_info(domain) [phone fallback]
            → phone
            └─ Step 6b: SerpApiClient.name_search(first, company) [name fallback]
```

**Thread safety:** `RateLimiter` uses `threading.Lock`. The `_log_lock` protects GUI callback. Each worker returns its own `list[dict]` — no shared mutation of `self.leads` until after all workers complete.

### Phase 5 — Deduplication + Email Classification
```
Raw leads list
    → Deduplicate by (domain + name) and (domain + email)
    → classify_email_smart(email, name, company)
        ├─ GENERIC_EMAIL_PREFIXES check (info@, admin@, ...)
        ├─ Name word match  (matt in matt@... → Personal)
        └─ Company word match (smithdental in email for "Smith Dental" → Generic)
    → OpenAI gpt-4o-mini batch verification (if API key set)
```

### Phase 6 — Partition Sort + CSV Export

Leads are scored and sorted into 5 partitions:

```
Partition 1 (score 6000+): Name + Email + Phone  [personal email +500]
Partition 2 (score 4000+): Name + Phone only
Partition 3 (score 3000+): Name + Email only      [personal email +500]
Partition 4 (score 2000+): Phone only
Partition 5 (score 1000+): Email only              [personal email +500]

Tiebreakers within partition:
  +20 has domain
  +15 has role/title
  +10 full name (contains space)
  +5  has company name
```

Two CSV files are exported: `leads_ALL_*.csv` and `leads_TOP_N_*.csv`.

---

## Concurrency Model

```
Main Thread (tkinter event loop)
    │
    └─► Pipeline Thread (daemon=True)
            │
            └─► Phase 4: ThreadPoolExecutor (max_workers=8)
                    ├─ Worker 1: _enrich_single_domain(domain_001)
                    ├─ Worker 2: _enrich_single_domain(domain_002)
                    ├─ ...
                    └─ Worker 8: _enrich_single_domain(domain_008)
```

Workers share:
- `RateLimiter` instances (thread-safe via `threading.Lock`)
- API client instances (`self.apollo`, `self.lusha`, etc.)
- `self._cancelled` flag (read-only from workers)

Workers do NOT share:
- Lead data — each returns its own `list[dict]`
- Log/progress state — protected by `self._log_lock`

---

## Rate Limiting Strategy

| API | Min Interval | Reason |
|---|---|---|
| SEMrush | 0.8s | Free tier: 10 req/s, but with retries buffer |
| SerpApi | 0.8s | 100 searches/month — conservative |
| Apollo | 0.25s | 600 req/min limit — 4 req/s safe |
| Lusha | 0.15s | Higher rate limit, less data per call |
| WebScraper | 0.3s | Polite crawling; avoid bot detection |

---

## Name Resolution Logic (V5.3+)

When Apollo returns `first_name` only (common for sole proprietors), the pipeline attempts to reconstruct the full name from data already in-hand:

```
1. Company name: "Matthew Cornell Photography"
   → strip business suffixes (Photography, Studio, Design, ...)
   → if first_name "Matt" is an abbreviation of "Matthew":
       → remaining words → last name candidate: "Cornell"
   → result: "Matthew Cornell"

2. Domain slug: "matthewcornell.com.au"
   → strip TLDs, split slug
   → match first_name variants against slug prefix
   → extract suffix as last name: "Cornell"

3. LinkedIn URL: "/in/matthew-cornell-photography-123abc"
   → extract slug path, split by "-"
   → find first_name variant, take next token as last name
   → result: "Matthew Cornell"
```

Name abbreviation dictionary covers 40+ entries: matt↔matthew, mike↔michael, chris↔christopher, etc.

---

## Directory Structure

```
VS-CODE-AI-AGENT/
├── lead_generator_v5.4.py        # Production pipeline (current)
├── lead_generator_v5.3.py        # Name resolution version
├── lead_generator_v5.2.py        # Email inference + SerpApi name search
├── lead_generator_v5.1.py        # ThreadPoolExecutor + thread safety
├── lead_generator_v5.py          # Original V5 (full names, new sort, Lusha fix)
├── lead_generator_v4.py          # Previous stable version
├── requirements.txt              # Python dependencies
├── README.md                     # Quick start + feature overview
├── ARCHITECTURE.md               # This file
├── CHANGELOG.md                  # Full version history
├── docs/
│   └── API_REFERENCE.md          # External API integration details
└── dashboard/
    ├── client/                   # React + Vite frontend
    │   ├── src/
    │   │   ├── App.jsx
    │   │   ├── CreditsDashboard.jsx
    │   │   ├── useCreditsContext.js
    │   │   └── main.jsx
    │   ├── index.html
    │   ├── package.json
    │   └── vite.config.js
    └── server/                   # Express.js backend
        ├── index.js
        ├── package.json
        └── .env.example
```
