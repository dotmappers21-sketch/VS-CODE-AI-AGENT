# Changelog

All notable changes to **Lead Generation Pro** are documented here.

---

## [v5.4] — 2024-12

### Added
- **Partition-based CSV sorting** — 5-tier lead ranking replacing the previous flat score system
  - Tier 1: Name + Email + Phone (personal emails ranked first within tier)
  - Tier 2: Name + Phone only
  - Tier 3: Name + Email only (personal emails ranked first)
  - Tier 4: Phone only
  - Tier 5: Email only (personal emails ranked first)
  - Tiebreakers: domain presence (+20), role/title (+15), full name (+10), company name (+5)
- **Smart email classifier** (`classify_email_smart`) — replaces simple prefix-only heuristic
  - Name cross-referencing: if first/last name word appears in email local-part → Personal
  - Company cross-referencing: if company keyword appears in email for a different person → Generic
  - Falls back to OpenAI batch verification when API key is set
- **52-industry keyword library** — added 25 new industries to existing 27:
  - Wedding Planner, Tattoo Artist, Florist, Baker/Cake Decorator, Caterer
  - Personal Trainer, Yoga/Pilates Instructor, Massage Therapist
  - Interior Designer, Web Developer, Graphic Designer, Copywriter/Content Writer
  - Tutor, Music Teacher, Driving School
  - Pet Grooming, Locksmith, Moving/Removalist, Printing Service
  - Optometrist, Podiatrist, Dermatologist
  - Home Inspector, Painter/Decorator, Solar Panel Installer
- **API Credits Dashboard** — standalone React + Express app for real-time monitoring
  - Shows remaining credits + remaining searches for Apollo, Lusha, Semrush
  - Color-coded health indicators (green >20%, orange 5-20%, red <5%)
  - Auto-refreshes every 30 seconds; manual refresh button
  - 5-minute server-side cache to prevent unnecessary API calls
  - Alert banners for low/critical credit states

### Changed
- `leads_TOP_N_*.csv` now includes ALL leads (not just personal-email leads) sorted by partition order
- Source column tags updated: `+CompanyName`, `+DomainName`, `+LinkedIn`, `+ScrapeName`, `+SerpApiName`

---

## [v5.3] — 2024-11

### Added
- **Company name extraction** (`_extract_name_from_company`) — resolves full name from business name
  - Strips 50+ business suffix tokens (Photography, Studio, Creative, Design, Clinic, ...)
  - Matches first-name abbreviations against remaining words (Matt ↔ Matthew)
  - Example: "Matthew Cornell Photography" + first="Matt" → "Matthew Cornell"
- **Domain slug extraction** (`_extract_name_from_domain`) — resolves full name from domain
  - Strips country TLDs (.com.au, .co.uk, .co.in), splits slug into tokens
  - Example: "matthewcornell.com.au" + first="Matt" → "Matthew Cornell"
- **LinkedIn URL extraction** (`_extract_name_from_linkedin_url`) — parses `/in/firstname-lastname-...`
  - Strips numeric suffixes (LinkedIn profile ID at end of slug)
  - Example: `/in/matthew-cornell-photography-5a3b9c` → "Matthew Cornell"
- **Name abbreviation dictionary** — 40+ entries covering common informal/formal pairs:
  - matt↔matthew, mike↔michael, chris↔christopher/christine, alex↔alexander/alexandra
  - rob↔robert, kate↔katherine/katelyn, liz↔elizabeth, ben↔benjamin, tom↔thomas, etc.
- **Resolution at Step 2** — name resolution runs immediately when Apollo people data is parsed, before any further enrichment steps
- **Resolution at Step 6b** — final pass over all leads for any remaining first-name-only records

### Changed
- `_infer_name_from_email` now uses `_get_name_variants()` to handle abbreviation forms when matching email local-part against first name

---

## [v5.2] — 2024-10

### Added
- **Email-based name inference** (`_infer_name_from_email`) — extracts last name from email when only first name is known
  - Pattern: `firstname.lastname@domain.com` → extracts `lastname`
  - Validates against domain to avoid false positives
- **SerpApi name search** — Google search `"FirstName" site:domain` to find full-name mentions
  - Parses title/snippet for `"FirstName Lastname"` pattern
  - Used as fallback when all other name sources return first-name only
- **Scraped-name backfill** — web scraper now extracts candidate names from homepage/contact page
  - Parses `<title>`, `<h1>`, `<h2>` and meta author tags
  - Backfills missing names at Step 3 before Lusha enrichment

### Changed
- Phase 4 enrichment order adjusted to try cheaper/faster name resolution before expensive API calls
- `WebScraper._scrape_page` returns structured dict including `candidate_names` list

---

## [v5.1] — 2024-09

### Added
- **ThreadPoolExecutor (8 workers)** — Phase 4 domain enrichment now runs in parallel
  - Extracted `_enrich_single_domain(domain, index, total) -> list[dict]` method
  - Each worker returns its own lead list; `self.leads` assembled after all futures complete
  - `self._log_lock = threading.Lock()` protects GUI log/progress callbacks from concurrent writes
- **Skip-if-complete logic** (`_lead_is_complete`) — skips enrichment steps for leads already having full name + email + phone
  - Checked before Apollo enrich_person, Lusha person enrichment, and SerpApi fallback
- **Rate limiter optimisation** — reduced minimum intervals for all APIs:
  - Apollo: 0.4s → 0.25s
  - Lusha: 0.2s → 0.15s
  - WebScraper: 0.5s → 0.3s
  - SEMrush: 1.2s → 0.8s
  - SerpApi: 1.2s → 0.8s
- **Reduced web scrape paths** — from 3 paths (`/`, `/contact`, `/about-us`) to 2 (`/`, `/contact`), as `/about-us` rarely contains actionable contact info

### Fixed
- `requests.Session` thread-safety bug — `WebScraper` was sharing a single `Session` across 8 threads. Replaced with stateless `requests.get(url, headers=self._headers, ...)` calls.
- Apollo `per_page=25` bug — call site was overriding the method's default of 10, causing quota burn on low-result queries. Reverted to default.

### Performance
- Phase 4 execution time: ~30-45 min (V5 sequential) → **~4-6 min** (V5.1 parallel, 8 workers)
- Total pipeline for 150 domains: **8-12 min** (target achieved)

---

## [v5] — 2024-08

### Added
- **Full-name resolution** — `enrich_person` now attempts Apollo `people/match` API when `last_name` is null in people search results
- **New partition scoring** — replaced flat relevance score with name/email/phone completeness tiers
- **Lusha fix** — corrected `v2/person` endpoint URL and auth header format that was silently returning 401

### Changed
- `ThreadPoolExecutor` imported (but not yet used — see V5.1 fix)
- TOP CSV filter changed from "has_phone" to "personal email" prioritisation

---

## [v4] — 2024-06

### Added
- **OpenAI email verification** — `gpt-4o-mini` batch API call to classify Personal vs Generic emails
- **Decision-maker grouping** — leads with `title` matching seniority keywords (Owner, Director, CEO, Founder, ...) ranked above staff leads
- **Apollo `organizations/enrich`** — adds company phone, industry, headcount to all leads from that domain

### Changed
- Phase 5 data cleanup now includes role-based deduplication (keep highest-seniority lead per domain when email matches)

---

## [v3] — 2024-04

### Added
- **Lusha integration** — `v2/company` + `v2/person` endpoints as secondary enrichment source
- **SerpApi domain discovery** — supplements SEMrush organic results with Google SERP scraping
- **Australia, USA, UK, India** country support with phone normalisation per region

---

## [v2] — 2024-02

### Added
- **SEMrush keyword expansion** — organic + adwords keyword research (Phase 2)
- **27-industry keyword library** — Dentist, Lawyer, Plumber, Electrician, Real Estate Agent, ...
- **CSV export** with source tracking columns

---

## [v1] — 2024-01

### Initial Release
- Apollo.io people search + org enrichment
- Basic web scraping (homepage)
- tkinter GUI with country + industry dropdowns
- Single-threaded pipeline
