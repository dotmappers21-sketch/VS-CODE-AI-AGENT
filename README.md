# Lead Generation Pro

> AI-powered B2B lead generation system for **Australia, USA, UK, and India** — discovers businesses via keyword research, enriches contacts with names, emails, and phones, and exports sorted CSV files ready for outreach.

---

## Features

- **Multi-source enrichment** — Apollo.io · Lusha · SerpApi · Web scraping
- **AI-powered email classification** — OpenAI agent classifies personal vs. generic emails using name/company cross-referencing
- **Full-name resolution** — extracts names from company names, domain slugs, and LinkedIn URLs
- **Parallel processing** — 8-worker `ThreadPoolExecutor` for domain enrichment (~8-12 min for 150 domains)
- **Smart CSV sorting** — partition-based: Name+Email+Phone → Name+Phone → Name+Email → Phone → Email
- **52 industries** — pre-built keyword libraries from Dentist to Solar Panel Installation
- **API Credits Dashboard** — real-time React dashboard showing remaining Apollo/Lusha/Semrush credits and search quotas

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI key (optional — for AI email classification)

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Run the GUI

```bash
python lead_generator_v5.4.py
```

### 4. Run the Credits Dashboard (optional)

```bash
# Backend
cd dashboard/server
npm install
cp .env.example .env   # fill in your API keys
npm start              # runs on http://localhost:3001

# Frontend (new terminal)
cd dashboard/client
npm install
npm run dev            # opens http://localhost:3000
```

---

## Configuration

All API keys are set in the `API_KEYS` dict at the top of `lead_generator_v5.4.py`:

| Key | Service | Used For |
|---|---|---|
| `semrush` | SEMrush | Keyword expansion (Phase 2) |
| `serpapi` | SerpApi | Domain discovery + name fallback (Phase 3) |
| `apollo` | Apollo.io | People search + org enrichment (Phase 4) |
| `lusha` | Lusha | Person + company enrichment (Phase 4) |
| `openai` | OpenAI | Email type classification (Phase 5b) |

---

## Pipeline

```
Phase 1: Seed Keywords
        ↓
Phase 2: SEMrush Keyword Expansion (~30 keywords)
        ↓
Phase 3: Domain Discovery — SEMrush Organic + SerpApi (up to 150 domains)
        ↓
Phase 4: Multi-source Enrichment (8 parallel workers)
         ├─ Apollo org enrich    → company name, phone
         ├─ Apollo people search → names, roles, emails
         ├─ Apollo enrich_person → full names
         ├─ Lusha company info   → always called per domain
         ├─ Lusha person enrich  → email, phone, role
         ├─ Web scraping         → homepage, /contact
         └─ SerpApi name search  → last-name fallback
        ↓
Phase 5: Data Cleanup + Deduplication
        ↓
Phase 5b: OpenAI Email Verification (batch)
        ↓
Phase 6: Partition Sort → CSV Export (ALL + TOP)
```

---

## CSV Output

Two files are generated per run:

| File | Contents |
|---|---|
| `leads_ALL_*.csv` | Every lead, sorted by partition |
| `leads_TOP_N_*.csv` | Top N leads in partition order |

**Partition sort order:**

1. Name + Email + Phone — personal emails first
2. Name + Phone only
3. Name + Email only — personal emails first
4. Phone only
5. Email only — personal emails first

**Source column tags:** `Apollo`, `+Lusha`, `+Scrape`, `+NameMatch`, `+CompanyName`, `+DomainName`, `+LinkedIn`, `+EmailInfer`, `+ScrapeName`, `+SerpApiName`

---

## Supported Countries

| Code | Country | Phone Format |
|---|---|---|
| AU | Australia | +61 |
| USA | United States | +1 |
| UK | United Kingdom | +44 |
| India | India | +91 |

---

## Requirements

- Python 3.11+
- `requests >= 2.31.0`
- `beautifulsoup4 >= 4.12.0`
- Node.js 18+ (dashboard only)

---

## Version History

| Version | Highlights |
|---|---|
| v5.4 | Partition-based sorting, smart email classifier, 52 industries, credits dashboard |
| v5.3 | Company/domain/LinkedIn name extraction, name abbreviation dictionary |
| v5.2 | Full-name resolution: email inference, SerpApi name search, scraped-name backfill |
| v5.1 | ThreadPoolExecutor (8 workers), skip-if-complete, optimized rate limiters |
| v5 | New sorting, personal email TOP CSV, Lusha fix |
| v4 | OpenAI email verification, decision-maker grouping |
