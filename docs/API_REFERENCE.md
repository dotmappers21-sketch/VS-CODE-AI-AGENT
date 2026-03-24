# API Integration Reference

This document describes how Lead Generation Pro integrates with each external API, including endpoints used, request formats, response parsing, credit consumption, and known limits.

---

## Apollo.io

**Base URL:** `https://api.apollo.io/api/v1`
**Auth:** `x-api-key: <key>` header
**Credits module:** `ApolloAPI` class (~line 807 in `lead_generator_v5.4.py`)

### Endpoints Used

#### `POST /mixed_people/api_search` — People Search
Searches for contacts associated with a domain.

**Request body:**
```json
{
  "api_key": "<key>",
  "q_organization_domains": "example.com",
  "person_titles": ["owner", "director", "ceo", "founder", "manager", "principal"],
  "per_page": 10,
  "page": 1
}
```

**Response fields used:**
```
people[].first_name
people[].last_name        ← null for sole proprietors
people[].title
people[].email
people[].linkedin_url
people[].organization.name
people[].organization.primary_phone.sanitized_number
```

**Credits:** ~1 export credit per person returned (if email included).
**Rate limit:** ~600 req/min. Pipeline uses 0.25s minimum interval.

---

#### `POST /people/match` — Person Enrichment
Enriches a single person by LinkedIn URL to resolve missing `last_name`.

**Request body:**
```json
{
  "api_key": "<key>",
  "linkedin_url": "https://www.linkedin.com/in/matthew-cornell-5a3b9c",
  "reveal_personal_emails": false
}
```

**Response fields used:**
```
person.first_name
person.last_name
person.title
person.email
```

**Credits:** 1 export credit per successful enrichment.
**Used when:** `last_name` is null in people search result and `linkedin_url` is available.

---

#### `POST /organizations/enrich` — Org Enrichment
Fetches company-level data for a domain.

**Request body:**
```json
{
  "api_key": "<key>",
  "domain": "example.com"
}
```

**Response fields used:**
```
organization.name
organization.primary_phone.sanitized_number
organization.industry
organization.estimated_num_employees
```

**Credits:** 1 org credit per call.
**Called:** Once per domain, at start of Phase 4 Step 1.

---

#### `GET /auth/health` — Credits Check (Dashboard only)
Returns remaining API credits for the authenticated account.

**Response fields used:**
```
account.credits_used_in_current_period
account.credits_limit
```

**No credits consumed** by this endpoint.

---

## Lusha

**Base URL:** `https://api.lusha.com`
**Auth:** `api_key: <key>` header
**Credits module:** `LushaAPI` class (~line 910)

### Endpoints Used

#### `GET /v2/person` — Person Enrichment
Enriches a person by first name, last name, and company domain.

**Query parameters:**
```
firstName=Matthew
lastName=Cornell
company=smithdental.com.au
```

**Response fields used:**
```
data.emails[0].email
data.phoneNumbers[0].localizedNumber
data.jobTitle
```

**Credits:** 1 person credit per successful enrichment.
**Rate limit:** Higher than Apollo. Pipeline uses 0.15s minimum interval.
**Called:** Phase 4 Step 4, for each lead where name is known.

---

#### `GET /v2/company` — Company Info
Fetches company phone number and name by domain.

**Query parameters:**
```
domain=smithdental.com.au
```

**Response fields used:**
```
data.phones[0].number
data.name
```

**Credits:** 1 company credit per call.
**Called:** Phase 4 Step 5, always once per domain (regardless of leads found).

---

#### `GET /v2/account/balance` — Credits Check (Dashboard only)
Returns current credit balance.

**Response fields used:**
```
data.remainingCredits
data.totalCredits
data.renewalDate
```

---

## SerpApi

**Base URL:** `https://serpapi.com/search`
**Auth:** `api_key=<key>` query parameter
**Credits module:** `SerpApiClient` class (~line 728)

### Endpoints Used

All calls use `GET /search` with different parameter combinations.

#### Domain Discovery Search
Finds business websites for a keyword + country.

**Parameters:**
```
engine=google
q=dentist near me
gl=au          (country code: au/us/gb/in)
hl=en
num=10
api_key=<key>
```

**Response fields used:**
```
organic_results[].link    → extract domain from URL
organic_results[].title   → company name fallback
```

**Credits:** 1 search credit per call.
**Rate limit:** 100 searches/month on free plan. Pipeline uses 0.8s interval.

---

#### Business Info Search
Fetches phone number for a specific business domain.

**Parameters:**
```
engine=google
q=site:example.com
gl=au
api_key=<key>
```

**Response fields used:**
```
knowledge_graph.phone
local_results[0].phone
organic_results[0].snippet  → phone number regex fallback
```

**Credits:** 1 search credit per call.
**Called:** Phase 4 Step 6, only for domains missing phone after all other sources.

---

#### Full-Name Search (V5.2+)
Finds full name mentions for a person at a specific company.

**Parameters:**
```
engine=google
q="Matthew" site:matthewcornell.com.au
gl=au
api_key=<key>
```

**Response fields used:**
```
organic_results[0].title
organic_results[0].snippet
```

Parses response with regex `r'\b(Matthew\s+[A-Z][a-z]+)\b'` to extract full name.
**Credits:** 1 search credit per call.
**Called:** V5.2 only (replaced by cheaper V5.3 in-data extraction approach).

---

## SEMrush

**Base URL:** `https://api.semrush.com`
**Auth:** `key=<key>` query parameter
**Credits module:** `SemrushAPI` class (~line 636)

### Endpoints Used

#### Keyword Organic Results
Returns websites ranking for a keyword in a country.

**Parameters:**
```
type=phrase_organic
key=<key>
phrase=dentist near me
database=au       (au/us/uk/in)
export_columns=Dn,Po,Tr
display_limit=10
```

**Response:** CSV text
**Columns used:** `Dn` (domain), `Po` (position), `Tr` (traffic estimate)

**Credits:** 10 API units per request (1 unit = 1 keyword row returned).
**Rate limit:** Varies by plan. Pipeline uses 0.8s interval.

---

#### Keyword Expansion — Organic
Finds related keywords with organic search volume.

**Parameters:**
```
type=phrase_related
key=<key>
phrase=dentist near me
database=au
export_columns=Ph,Nq
display_limit=20
```

**Columns used:** `Ph` (phrase), `Nq` (national search volume)

---

#### Keyword Expansion — Adwords
Finds related commercial keywords from paid search.

**Parameters:**
```
type=phrase_adwords
key=<key>
phrase=dentist near me
database=au
export_columns=Ph,Nq
display_limit=20
```

---

#### Credits Check (Dashboard only)

**URL:** `https://www.semrush.com/users/countapiunits.html?key=<key>`
**Response:** Plain integer (remaining API units)
**No units consumed** by this endpoint.

**Search conversion:** 1 search ≈ 2.67 API units (pipeline uses ~10 units per keyword × ~30 keywords ÷ 150 domains ≈ 2 units per lead discovery step).

---

## OpenAI

**Base URL:** `https://api.openai.com/v1`
**Auth:** `Authorization: Bearer <key>` header
**Module:** `classify_email_openai()` function

### Endpoint Used

#### `POST /chat/completions` — Email Classification (Phase 5b)
Batch-classifies all emails as Personal or Generic using a single API call.

**Model:** `gpt-4o-mini`

**Prompt structure:**
```
System: You are an expert at classifying email addresses...
User: Classify the following emails as Personal or Generic.
      Return a JSON array of objects with {email, type} fields.

      Email list:
      1. matt@matthewcornell.com.au | Name: Matthew Cornell | Company: Matthew Cornell Photography
      2. info@smithdental.com.au | Name: John Smith | Company: Smith Dental
      ...
```

**Response parsing:**
```json
[
  {"email": "matt@matthewcornell.com.au", "type": "Personal"},
  {"email": "info@smithdental.com.au", "type": "Generic"}
]
```

**Cost:** ~$0.0001 per 100 emails at gpt-4o-mini pricing.
**Called:** Once per pipeline run, after deduplication, only if `OPENAI_API_KEY` is set.
**Fallback:** `classify_email_smart()` runs without OpenAI if key is absent or call fails.

---

## Web Scraping

Not a paid API — uses `requests` + `BeautifulSoup`.
**Module:** `WebScraper` class (~line 1081)

### Pages Scraped Per Domain

1. `https://<domain>/` — homepage
2. `https://<domain>/contact` — contact page

### Data Extracted

| Field | Source |
|---|---|
| Phone | `<a href="tel:...">`, `<p>` text matching phone regex, `<span>` |
| Email | `<a href="mailto:...">`, text matching email regex |
| Candidate names | `<title>`, `<h1>`, `<h2>`, `<meta name="author">` |

### Phone Regex Patterns (by country)

| Country | Pattern |
|---|---|
| Australia | `(?:\+61\|0)[2-9]\d{8}` |
| USA | `(?:\+1)?[2-9]\d{2}[2-9]\d{6}` |
| UK | `(?:\+44\|0)[1-9]\d{9,10}` |
| India | `(?:\+91\|0)[6-9]\d{9}` |

### Thread Safety Note
`WebScraper` uses stateless `requests.get(url, headers=self._headers, timeout=10)` calls — no shared `Session` object — making it safe for concurrent use across 8 workers.

---

## Dashboard API (Internal)

**Base URL:** `http://localhost:3001/api`
**Module:** `dashboard/server/index.js`

| Endpoint | Method | Description |
|---|---|---|
| `/credits` | GET | Returns cached credit data (5-min TTL) |
| `/credits/refresh` | POST | Clears cache + re-fetches all APIs in parallel |

**Response schema:**
```json
{
  "apollo": {
    "remaining": 4200,
    "total": 5000,
    "percentage": 84,
    "remainingSearches": 2100,
    "resetDate": "2025-01-01",
    "usageRate": 12,
    "status": "ok"
  },
  "lusha": { ... },
  "semrush": { ... },
  "summary": {
    "totalSearchesAvailable": 6350,
    "servicesHealthy": 3,
    "servicesLow": 0,
    "servicesCritical": 0
  }
}
```

**`remainingSearches` calculation:**
- Apollo: `remaining ÷ 2` (2 credits average per enriched lead)
- Lusha: `remaining ÷ 2` (person + company call per domain)
- Semrush: `remaining ÷ 2.67` (empirical units-per-domain average)
