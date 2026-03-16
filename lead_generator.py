#!/usr/bin/env python3
"""
Lead Generation Automation Tool
================================
A production-ready lead generation tool that discovers businesses via keyword research,
finds their websites, and enriches contacts with names, roles, emails, and phone numbers.

Pipeline: SEMrush Keywords → SEMrush/SerpApi Domain Discovery → Apollo/Lusha/Web Scraping Enrichment → CSV Export

Requirements: requests, beautifulsoup4
Target: Python 3.11+ / PyCharm 2025.3
"""

import csv
import json
import os
import platform
import re
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse

import requests
from bs4 import BeautifulSoup

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

API_KEYS = {
    "semrush": "19a6d563243212fca1886beb6946cef8",
    "serpapi": "ae9dd45690cf5feff7c676938f79eaf798c703d648462875cb89c0c7c05d359e",
    "apollo": "6x7g4KoJuAbc9Ia9uM4YpA",
    "lusha": "b528acff-ae77-4263-a606-bc70697f1e9f",
}

COUNTRY_CONFIG = {
    "AU": {
        "name": "Australia",
        "semrush_db": "au",
        "serpapi_gl": "au",
        "phone_code": "+61",
        "phone_regex": r"(?:\+61\s?|0)[2-478](?:[\s.-]?\d){8}",
        "location_suffix": "Australia",
    },
    "USA": {
        "name": "United States",
        "semrush_db": "us",
        "serpapi_gl": "us",
        "phone_code": "+1",
        "phone_regex": r"(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
        "location_suffix": "United States",
    },
    "UK": {
        "name": "United Kingdom",
        "semrush_db": "uk",
        "serpapi_gl": "uk",
        "phone_code": "+44",
        "phone_regex": r"(?:\+44\s?|0)\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}",
        "location_suffix": "United Kingdom",
    },
    "India": {
        "name": "India",
        "semrush_db": "in",
        "serpapi_gl": "in",
        "phone_code": "+91",
        "phone_regex": r"(?:\+91[\s.-]?|0)?[6-9]\d{9}",
        "location_suffix": "India",
    },
}

# Platform domains to filter out during domain discovery
PLATFORM_DOMAINS = {
    "google.com", "google.com.au", "google.co.uk", "google.co.in",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
    "yelp.com", "yelp.com.au", "yellowpages.com", "yellowpages.com.au",
    "wikipedia.org", "reddit.com", "quora.com", "medium.com",
    "amazon.com", "ebay.com", "ebay.com.au", "alibaba.com",
    "tripadvisor.com", "trustpilot.com", "bbb.org",
    "apple.com", "microsoft.com", "adobe.com",
    "healthgrades.com", "webmd.com", "zocdoc.com",
    "thumbtack.com", "homeadvisor.com", "angi.com", "angieslist.com",
    "glassdoor.com", "indeed.com", "seek.com.au",
    "truelocal.com.au", "hotfrog.com.au", "startlocal.com.au",
    "whitepages.com.au", "yell.com", "justdial.com", "sulekha.com",
    "indiamart.com", "practo.com", "justlanded.com",
    "crunchbase.com", "bloomberg.com", "forbes.com",
    "gov.au", "nhs.uk", "gov.uk", "gov.in", "fda.gov",
    "healthengine.com.au", "hotdoc.com.au", "ratemds.com",
    "wordofmouth.com.au", "localsearch.com.au",
    "finder.com.au", "canstar.com.au", "productreview.com.au",
    "serviceseeking.com.au", "hipages.com.au", "oneflare.com.au",
    "airtasker.com", "bark.com",
    # Health/medical info sites (not actual practices)
    "healthline.com", "mayoclinic.org", "clevelandclinic.org",
    "my.clevelandclinic.org", "webmd.com", "medicalnewstoday.com",
    "verywellhealth.com", "betterhealth.vic.gov.au",
    # Large retailers/corporates (not SMBs)
    "woolworths.com.au", "chemistwarehouse.com.au", "priceline.com.au",
    "amazon.com.au", "colgate.com.au", "colgate.com",
    "bupa.com", "bupa.com.au", "bupaglobal.com",
    "bupaagedcare.com.au", "bupatravelinsurance.com.au",
    # Educational / government
    "sydney.edu.au", "unimelb.edu.au", "uq.edu.au",
    "monash.edu", "adelaide.edu.au", "unsw.edu.au",
}

# ══════════════════════════════════════════════════════════════════════════════
# INDUSTRY KEYWORD DICTIONARY — 25+ industries with 10-15 keywords each
# ══════════════════════════════════════════════════════════════════════════════

INDUSTRY_KEYWORDS = {
    "Dentist": [
        "dental implants", "root canal treatment", "teeth whitening",
        "orthodontist near me", "emergency dentist", "dental clinic",
        "cosmetic dentistry", "dental crown", "wisdom tooth removal",
        "periodontal treatment", "dental veneers", "invisalign provider",
        "pediatric dentist", "teeth cleaning service",
    ],
    "Doctor / General Practitioner": [
        "family doctor near me", "general practitioner clinic", "bulk billing doctor",
        "medical centre", "walk in clinic", "health check up",
        "vaccination clinic", "GP appointment", "after hours doctor",
        "women's health clinic", "men's health check", "pathology services",
    ],
    "Lawyer / Attorney": [
        "family lawyer", "criminal defence lawyer", "personal injury attorney",
        "divorce lawyer near me", "immigration lawyer", "business lawyer",
        "estate planning attorney", "property conveyancer", "employment lawyer",
        "traffic lawyer", "wills and probate", "commercial litigation",
    ],
    "Accountant": [
        "tax accountant near me", "small business accountant", "bookkeeping services",
        "tax return preparation", "BAS lodgement service", "financial auditing",
        "payroll services", "business advisory", "self managed super fund accountant",
        "company tax planning", "forensic accounting", "xero certified accountant",
    ],
    "Plumber": [
        "emergency plumber", "blocked drain plumber", "hot water system repair",
        "gas plumber near me", "bathroom renovation plumber", "leak detection service",
        "pipe relining", "backflow prevention", "plumbing maintenance",
        "sewer repair service", "tap replacement", "toilet repair plumber",
    ],
    "Electrician": [
        "emergency electrician", "electrical contractor near me", "solar panel installer",
        "switchboard upgrade", "LED lighting installation", "smoke alarm installation",
        "electrical safety inspection", "ceiling fan installation", "EV charger installer",
        "commercial electrician", "security lighting", "power point installation",
    ],
    "Real Estate Agent": [
        "real estate agent near me", "property valuation", "house for sale",
        "property management service", "real estate auctioneer", "buyer's agent",
        "commercial real estate", "rental property manager", "land for sale",
        "investment property advisor", "first home buyer agent", "luxury real estate",
    ],
    "Restaurant / Cafe": [
        "restaurant near me", "cafe near me", "fine dining restaurant",
        "pizza delivery", "catering service", "private dining",
        "brunch cafe", "takeaway food", "function venue",
        "restaurant booking", "food delivery service", "organic cafe",
    ],
    "Gym / Fitness": [
        "gym near me", "personal trainer", "fitness centre",
        "crossfit gym", "yoga studio near me", "pilates classes",
        "boxing gym", "24 hour gym", "group fitness classes",
        "strength training gym", "weight loss program", "martial arts studio",
    ],
    "Auto Repair / Mechanic": [
        "car mechanic near me", "auto repair shop", "car service centre",
        "brake repair", "transmission repair", "tyre replacement",
        "roadworthy certificate", "logbook service", "car air conditioning repair",
        "diesel mechanic", "mobile mechanic", "pre purchase car inspection",
    ],
    "Salon / Spa / Beauty": [
        "hair salon near me", "beauty salon", "day spa",
        "nail salon", "barber shop near me", "laser hair removal",
        "facial treatment", "massage therapy", "eyebrow threading",
        "bridal hair and makeup", "skin clinic", "waxing salon",
    ],
    "Chiropractor": [
        "chiropractor near me", "back pain treatment", "spinal adjustment",
        "sports chiropractor", "neck pain relief", "sciatica treatment",
        "posture correction", "chiropractic clinic", "headache treatment chiropractor",
        "pregnancy chiropractor", "pediatric chiropractor",
    ],
    "Veterinarian": [
        "vet near me", "emergency vet", "pet vaccination",
        "dog grooming", "cat vet", "animal hospital",
        "pet dental care", "pet surgery", "veterinary clinic",
        "exotic animal vet", "pet microchipping", "puppy health check",
    ],
    "Insurance Agent": [
        "insurance broker near me", "car insurance quote", "home insurance",
        "life insurance advisor", "business insurance", "health insurance broker",
        "income protection insurance", "travel insurance", "landlord insurance",
        "professional indemnity insurance", "workers compensation insurance",
    ],
    "Financial Advisor": [
        "financial planner near me", "investment advisor", "retirement planning",
        "wealth management", "superannuation advice", "mortgage broker",
        "financial planning service", "estate planning advisor", "debt consolidation",
        "self managed super fund advisor", "tax effective investment",
    ],
    "Photographer": [
        "wedding photographer", "portrait photographer", "commercial photographer",
        "real estate photographer", "event photographer", "newborn photographer",
        "family photographer", "headshot photographer", "product photography",
        "corporate photographer", "drone photographer",
    ],
    "Landscaping": [
        "landscaper near me", "garden design service", "lawn mowing service",
        "tree removal", "irrigation installation", "retaining wall builder",
        "landscape architect", "garden maintenance", "artificial turf installer",
        "paving contractor", "outdoor living design", "hedge trimming service",
    ],
    "HVAC": [
        "air conditioning installation", "heating repair", "HVAC contractor",
        "ducted air conditioning", "split system installation", "furnace repair",
        "commercial HVAC", "air conditioning service", "ventilation system",
        "heat pump installer", "evaporative cooling", "air duct cleaning",
    ],
    "Roofing": [
        "roof repair near me", "roofing contractor", "roof replacement",
        "metal roofing", "tile roof repair", "gutter installation",
        "roof restoration", "commercial roofing", "roof leak repair",
        "colorbond roofing", "roof painting", "roof inspection service",
    ],
    "Pest Control": [
        "pest control near me", "termite inspection", "cockroach treatment",
        "rodent control", "bed bug treatment", "ant control service",
        "spider treatment", "commercial pest control", "pre purchase pest inspection",
        "possum removal", "wasp nest removal", "flea treatment",
    ],
    "Cleaning Service": [
        "house cleaning service", "commercial cleaning", "carpet cleaning",
        "end of lease cleaning", "office cleaning service", "window cleaning",
        "deep cleaning service", "pressure washing", "tile and grout cleaning",
        "upholstery cleaning", "regular house cleaning", "spring cleaning service",
    ],
    "IT Services": [
        "IT support near me", "managed IT services", "computer repair",
        "network setup", "cybersecurity services", "cloud computing solutions",
        "IT consulting", "data recovery service", "business IT support",
        "VoIP phone systems", "server maintenance", "IT helpdesk outsourcing",
    ],
    "Marketing Agency": [
        "digital marketing agency", "SEO services", "social media marketing",
        "PPC management", "content marketing agency", "web design agency",
        "branding agency", "email marketing service", "Google Ads management",
        "video production agency", "PR agency", "lead generation service",
    ],
    "Construction": [
        "home builder near me", "construction company", "renovation contractor",
        "commercial construction", "custom home builder", "bathroom renovation",
        "kitchen renovation", "extension builder", "granny flat builder",
        "project home builder", "demolition contractor", "concrete contractor",
    ],
    "Architecture": [
        "architect near me", "residential architect", "commercial architect",
        "interior designer", "building designer", "sustainable architecture",
        "heritage architect", "architectural drafting", "house design service",
        "landscape architect", "3D architectural rendering",
    ],
    "Physiotherapy": [
        "physiotherapist near me", "sports physio", "back pain physiotherapy",
        "post surgery rehabilitation", "neck pain treatment physio",
        "shoulder physio", "knee rehabilitation", "workplace injury physio",
        "dry needling treatment", "hydrotherapy", "exercise physiologist",
    ],
    "Pharmacy": [
        "pharmacy near me", "compounding pharmacy", "online pharmacy",
        "late night pharmacy", "prescription delivery", "vaccination pharmacy",
        "travel health clinic pharmacy", "medication management",
        "health screening pharmacy", "weight management pharmacy",
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


class RateLimiter:
    """Simple per-API rate limiter with minimum interval between calls."""

    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self._last_call = 0.0
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_call = time.time()


def extract_domain(url: str) -> str:
    """Extract clean domain from a URL."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc or parsed.path.split("/")[0]
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        # Remove port
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain
    except Exception:
        return ""


def domain_to_company_name(domain: str) -> str:
    """Convert domain string to a readable company name.
    e.g., 'smith-dental.com.au' -> 'Smith Dental'
    """
    name = domain.lower().strip()
    for prefix in ("https://", "http://", "www."):
        if name.startswith(prefix):
            name = name[len(prefix):]
    name = name.split("/")[0]
    # Remove TLDs (order matters — longer first)
    tld_patterns = [
        ".com.au", ".co.uk", ".org.au", ".net.au", ".gov.au",
        ".co.in", ".org.in", ".net.in",
        ".co.nz", ".com", ".org", ".net", ".io", ".co",
        ".biz", ".info", ".au", ".uk", ".in", ".us",
    ]
    for tld in tld_patterns:
        if name.endswith(tld):
            name = name[: -len(tld)]
            break
    name = name.replace("-", " ").replace("_", " ").replace(".", " ")
    name = " ".join(name.split())
    return name.title() if name else domain


def format_phone(raw_phone: str, country_code: str) -> str:
    """Normalize phone number with country code prefix."""
    if not raw_phone:
        return ""
    # Clean the input
    cleaned = raw_phone.strip()
    # Already has + prefix — just clean whitespace
    if cleaned.startswith("+"):
        return re.sub(r"[\s.-]", "", cleaned)
    # Remove common formatting
    digits = re.sub(r"[^\d]", "", cleaned)
    if not digits or len(digits) < 8:
        return ""
    code_digits = country_code.replace("+", "")
    # Strip leading 0 and prepend country code
    if digits.startswith("0"):
        digits = digits[1:]
    if digits.startswith(code_digits):
        return f"+{digits}"
    return f"{country_code}{digits}"


def is_valid_email(email: str) -> bool:
    """Basic email validation — filters out obvious non-emails."""
    if not email or "@" not in email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False
    bad_patterns = [
        "example.com", "test.com", "sentry.io", "wixpress.com",
        ".png", ".jpg", ".gif", ".svg", ".webp", ".css", ".js",
        "noreply", "no-reply", "mailer-daemon", "postmaster",
        "schema.org", "sentry", "w3.org", "googleapis",
    ]
    email_lower = email.lower()
    return not any(bp in email_lower for bp in bad_patterns)


def is_platform_domain(domain: str) -> bool:
    """Check if a domain is a known platform/directory/non-SMB to skip."""
    d = domain.lower().strip()
    if d.startswith("www."):
        d = d[4:]
    # Exact match or subdomain match against blocklist
    for pd in PLATFORM_DOMAINS:
        if d == pd or d.endswith(f".{pd}"):
            return True
    # Filter educational and government domains globally
    edu_gov_patterns = [".edu.", ".edu", ".gov.", ".gov", ".ac.uk", ".ac.au"]
    for pattern in edu_gov_patterns:
        if pattern in d or d.endswith(pattern):
            return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# API CLIENTS
# ══════════════════════════════════════════════════════════════════════════════


class SemrushClient:
    """SEMrush API client for keyword expansion AND domain discovery."""

    BASE_URL = "https://api.semrush.com/"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = RateLimiter(1.2)

    def _request(self, params: dict) -> str:
        """Make a rate-limited request and return raw text."""
        self.limiter.wait()
        params["key"] = self.api_key
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            if resp.status_code == 200 and "ERROR" not in resp.text[:50]:
                return resp.text
        except Exception:
            pass
        return ""

    def get_related_keywords(self, phrase: str, database: str, display_limit: int = 15) -> list[dict]:
        """Get related keywords for a seed phrase."""
        text = self._request({
            "type": "phrase_related",
            "phrase": phrase,
            "database": database,
            "display_limit": display_limit,
            "export_columns": "Ph,Nq,Cp",
        })
        return self._parse_keyword_csv(text)

    def get_organic_domains(self, phrase: str, database: str, limit: int = 10) -> list[dict]:
        """Find domains ranking organically for a keyword.
        Returns list of {'domain': ..., 'url': ...}
        """
        text = self._request({
            "type": "phrase_organic",
            "phrase": phrase,
            "database": database,
            "display_limit": limit,
            "export_columns": "Dn,Ur",
        })
        return self._parse_domain_csv(text)

    def get_adwords_domains(self, phrase: str, database: str, limit: int = 10) -> list[dict]:
        """Find domains running ads for a keyword (high-intent prospects).
        Returns list of {'domain': ..., 'url': ...}
        """
        text = self._request({
            "type": "phrase_adwords",
            "phrase": phrase,
            "database": database,
            "display_limit": limit,
            "export_columns": "Dn,Ur",
        })
        return self._parse_domain_csv(text)

    def _parse_keyword_csv(self, text: str) -> list[dict]:
        results = []
        lines = text.strip().split("\n")
        if len(lines) < 2:
            return results
        for line in lines[1:]:
            parts = line.split(";")
            if len(parts) >= 3:
                try:
                    keyword = parts[0].strip()
                    volume = int(parts[1].strip().replace(",", "") or "0")
                    cpc = float(parts[2].strip().replace(",", "") or "0")
                    results.append({"keyword": keyword, "volume": volume, "cpc": cpc})
                except (ValueError, IndexError):
                    continue
        return results

    def _parse_domain_csv(self, text: str) -> list[dict]:
        results = []
        lines = text.strip().split("\n")
        if len(lines) < 2:
            return results
        for line in lines[1:]:
            parts = line.split(";")
            if len(parts) >= 2:
                domain = parts[0].strip()
                url = parts[1].strip() if len(parts) > 1 else ""
                # Clean domain
                d = extract_domain(domain) or extract_domain(url)
                if d and not is_platform_domain(d):
                    results.append({"domain": d, "url": url})
        return results


class SerpApiClient:
    """SerpApi client — optional fallback for domain discovery."""

    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = RateLimiter(1.2)
        self._available = True  # Track if API credits remain

    def search_keyword(self, query: str, country_gl: str, num: int = 20) -> list[str]:
        """Search Google and return discovered domains."""
        if not self._available:
            return []
        self.limiter.wait()
        params = {
            "q": query, "gl": country_gl, "api_key": self.api_key,
            "num": num, "output": "json",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            if resp.status_code == 429 or "run out of searches" in resp.text:
                self._available = False
                return []
            if resp.status_code != 200:
                return []
            data = resp.json()
            if "error" in data:
                self._available = False
                return []
            return self._extract_domains(data)
        except Exception:
            return []

    def search_business_info(self, company_name: str, country_gl: str) -> dict:
        """Search for a company's phone/email via Google knowledge graph."""
        if not self._available:
            return {}
        self.limiter.wait()
        query = f'"{company_name}" phone number email contact'
        params = {
            "q": query, "gl": country_gl, "api_key": self.api_key,
            "num": 5, "output": "json",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            if resp.status_code != 200:
                return {}
            data = resp.json()
            info = {}
            kg = data.get("knowledge_graph", {})
            if kg.get("phone"):
                info["phone"] = kg["phone"]
            if kg.get("email"):
                info["email"] = kg["email"]
            for local in data.get("local_results", {}).get("places", []):
                if not info.get("phone") and local.get("phone"):
                    info["phone"] = local["phone"]
            return info
        except Exception:
            return {}

    def _extract_domains(self, data: dict) -> list[str]:
        domains = set()
        for result in data.get("organic_results", []):
            d = extract_domain(result.get("link", ""))
            if d and not is_platform_domain(d):
                domains.add(d)
        for ad in data.get("ads", []):
            d = extract_domain(ad.get("link", "") or ad.get("tracking_link", ""))
            if d and not is_platform_domain(d):
                domains.add(d)
        for place in data.get("local_results", {}).get("places", []):
            d = extract_domain(place.get("website", "") or place.get("link", ""))
            if d and not is_platform_domain(d):
                domains.add(d)
        return list(domains)


class ApolloClient:
    """Apollo.io API client for people search and organization enrichment."""

    BASE_URL = "https://api.apollo.io/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = RateLimiter(0.6)

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }

    def search_people_by_domain(self, domain: str, per_page: int = 5) -> list[dict]:
        """Search for people at a domain using the new api_search endpoint."""
        self.limiter.wait()
        url = f"{self.BASE_URL}/mixed_people/api_search"
        payload = {
            "q_organization_domains": domain,
            "per_page": per_page,
        }
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            if resp.status_code == 200:
                return resp.json().get("people", [])
            return []
        except Exception:
            return []

    def enrich_organization(self, domain: str) -> dict:
        """Get organization-level data including phone number."""
        self.limiter.wait()
        url = f"{self.BASE_URL}/organizations/enrich"
        try:
            resp = requests.get(
                url, params={"domain": domain},
                headers=self._headers(), timeout=30
            )
            if resp.status_code == 200:
                org = resp.json().get("organization", {})
                return {
                    "company_name": org.get("name", ""),
                    "phone": org.get("phone", ""),
                    "website": org.get("website_url", ""),
                    "industry": org.get("industry", ""),
                    "employees": org.get("estimated_num_employees", ""),
                    "city": org.get("city", ""),
                    "linkedin": org.get("linkedin_url", ""),
                }
            return {}
        except Exception:
            return {}

    def enrich_person(self, first_name: str, last_name: str, domain: str) -> dict:
        """Try to enrich a person with email (phone requires webhook, so skip)."""
        self.limiter.wait()
        url = f"{self.BASE_URL}/people/match"
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "domain": domain,
            "reveal_personal_emails": True,
        }
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            if resp.status_code == 200:
                person = resp.json().get("person", {})
                if person:
                    email = ""
                    if person.get("personal_emails"):
                        email = person["personal_emails"][0]
                    elif person.get("email"):
                        email = person["email"]
                    return {
                        "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                        "role": person.get("title", ""),
                        "email": email,
                        "company": person.get("organization", {}).get("name", ""),
                    }
            return {}
        except Exception:
            return {}


class LushaClient:
    """Lusha API client — company enrichment and person lookup."""

    BASE_URL = "https://api.lusha.com"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = RateLimiter(0.3)

    def _headers(self) -> dict:
        return {"api_key": self.api_key, "Content-Type": "application/json"}

    def get_company_info(self, domain: str) -> dict:
        """Get company information from Lusha company API v2."""
        self.limiter.wait()
        url = f"{self.BASE_URL}/v2/company"
        try:
            resp = requests.get(
                url, params={"domain": domain},
                headers=self._headers(), timeout=30
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data:
                    return {
                        "company_name": data.get("name", ""),
                        "description": data.get("description", ""),
                        "domain": data.get("domain", ""),
                        "employees": data.get("employees", ""),
                        "industry": data.get("mainIndustry", ""),
                        "sub_industry": data.get("subIndustry", ""),
                        "linkedin": data.get("social", {}).get("linkedin", {}).get("url", ""),
                        "city": data.get("location", {}).get("city", ""),
                        "country": data.get("location", {}).get("country", ""),
                        "website": data.get("website", ""),
                    }
            return {}
        except Exception:
            return {}

    def enrich_person(self, first_name: str, last_name: str, company_domain: str) -> dict:
        """Enrich a person via Lusha Person API v2."""
        self.limiter.wait()
        url = f"{self.BASE_URL}/v2/person"
        try:
            resp = requests.get(
                url,
                params={
                    "firstName": first_name,
                    "lastName": last_name,
                    "companyDomain": company_domain,
                },
                headers=self._headers(),
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                contact = data.get("contact", {})
                if contact and contact.get("data"):
                    person_data = contact["data"]
                    result = {
                        "name": f"{person_data.get('firstName', '')} {person_data.get('lastName', '')}".strip(),
                        "role": person_data.get("jobTitle", ""),
                        "email": "",
                        "phone": "",
                        "company": person_data.get("company", {}).get("name", ""),
                    }
                    if person_data.get("emails"):
                        result["email"] = person_data["emails"][0].get("email", "")
                    if person_data.get("phoneNumbers"):
                        result["phone"] = person_data["phoneNumbers"][0].get("number", "")
                    return result
            return {}
        except Exception:
            return {}


class WebScraper:
    """Free web scraper for extracting contact info from company websites."""

    CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/team", "/our-team", ""]

    def __init__(self, country_code: str = "AU"):
        self.country_code = country_code
        self.phone_regex = COUNTRY_CONFIG.get(country_code, COUNTRY_CONFIG["AU"])["phone_regex"]
        self.limiter = RateLimiter(0.8)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def scrape_domain(self, domain: str) -> dict:
        """Scrape a domain for contact information."""
        result = {"emails": [], "phones": [], "company_name": ""}
        for path in self.CONTACT_PATHS:
            url = f"https://{domain}{path}"
            page_data = self._scrape_page(url)
            if page_data:
                result["emails"].extend(page_data.get("emails", []))
                result["phones"].extend(page_data.get("phones", []))
                if not result["company_name"] and page_data.get("company_name"):
                    result["company_name"] = page_data["company_name"]
        # Deduplicate
        result["emails"] = list(dict.fromkeys(e for e in result["emails"] if is_valid_email(e)))
        result["phones"] = list(dict.fromkeys(result["phones"]))
        return result

    def _scrape_page(self, url: str) -> dict | None:
        self.limiter.wait()
        try:
            resp = self.session.get(url, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)

            # Emails from text + mailto links
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            for a_tag in soup.find_all("a", href=True):
                if a_tag["href"].startswith("mailto:"):
                    email = a_tag["href"].replace("mailto:", "").split("?")[0].strip()
                    if email:
                        emails.append(email)

            # Phones from text + tel links
            phones = re.findall(self.phone_regex, text)
            for a_tag in soup.find_all("a", href=True):
                if a_tag["href"].startswith("tel:"):
                    phone = a_tag["href"].replace("tel:", "").strip()
                    if phone:
                        phones.append(phone)

            # Company name
            company_name = ""
            og_name = soup.find("meta", property="og:site_name")
            if og_name and og_name.get("content"):
                company_name = og_name["content"].strip()
            elif soup.title and soup.title.string:
                title_text = soup.title.string.strip()
                for sep in [" | ", " - ", " – ", " — ", " :: ", " : "]:
                    if sep in title_text:
                        company_name = title_text.split(sep)[0].strip()
                        break
                if not company_name:
                    company_name = title_text[:60]

            return {"emails": emails[:5], "phones": phones[:5], "company_name": company_name}
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════
# LEAD GENERATION PIPELINE
# ══════════════════════════════════════════════════════════════════════════════


class LeadGenerationPipeline:
    """Orchestrates the complete 6-phase lead generation pipeline."""

    def __init__(
        self,
        industry: str,
        country: str,
        min_volume: int,
        min_cpc: float,
        output_folder: str,
        progress_callback=None,
        log_callback=None,
    ):
        self.industry = industry
        self.country = country
        self.min_volume = min_volume
        self.min_cpc = min_cpc
        self.output_folder = output_folder
        self.progress_callback = progress_callback or (lambda *a: None)
        self.log_callback = log_callback or (lambda *a: None)
        self._cancelled = False

        self.config = COUNTRY_CONFIG[country]

        # API clients
        self.semrush = SemrushClient(API_KEYS["semrush"])
        self.serpapi = SerpApiClient(API_KEYS["serpapi"])
        self.apollo = ApolloClient(API_KEYS["apollo"])
        self.lusha = LushaClient(API_KEYS["lusha"])
        self.scraper = WebScraper(country)

        # Data stores
        self.keywords: list[str] = []
        self.domains: list[str] = []
        self.leads: list[dict] = []

    def cancel(self):
        self._cancelled = True

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_callback(f"[{timestamp}] {msg}")

    def _progress(self, pct: int, status: str = ""):
        self.progress_callback(pct, status)

    def run(self) -> str:
        """Execute the full pipeline. Returns path to output CSV."""
        try:
            self._phase1_seed_keywords()
            if self._cancelled:
                return ""
            self._phase2_semrush_expansion()
            if self._cancelled:
                return ""
            self._phase3_domain_discovery()
            if self._cancelled:
                return ""
            if not self.domains:
                self._log("No prospect domains found. Try different industry/settings.")
                return ""
            self._phase4_enrichment()
            if self._cancelled:
                return ""
            self._phase5_cleanup()
            if self._cancelled:
                return ""
            return self._phase6_export()
        except Exception as e:
            self._log(f"Pipeline error: {e}")
            return ""

    # ── Phase 1: Seed Keywords ──────────────────────────────────────────────

    def _phase1_seed_keywords(self):
        self._progress(2, "Generating seed keywords...")
        self._log(f"Phase 1: Generating seed keywords for '{self.industry}'")

        seeds = INDUSTRY_KEYWORDS.get(self.industry, [])
        if not seeds:
            base = self.industry.lower()
            seeds = [
                f"{base} near me", f"best {base}", f"{base} services",
                f"{base} {self.config['location_suffix']}",
                f"professional {base}", f"local {base}",
                f"affordable {base}", f"top {base}",
            ]

        self.keywords = seeds[:]
        self._log(f"   Generated {len(self.keywords)} seed keywords")
        self._progress(5, f"{len(self.keywords)} seed keywords ready")

    # ── Phase 2: SEMrush Keyword Expansion ──────────────────────────────────

    def _phase2_semrush_expansion(self):
        self._progress(6, "Expanding keywords via SEMrush...")
        self._log("Phase 2: SEMrush keyword expansion")

        db = self.config["semrush_db"]
        expanded = set(self.keywords)
        seeds_to_expand = self.keywords[:7]

        for i, seed in enumerate(seeds_to_expand):
            if self._cancelled:
                return
            self._log(f"   Expanding: '{seed}'")
            results = self.semrush.get_related_keywords(seed, db, display_limit=15)

            added = 0
            for kw_data in results:
                kw = kw_data["keyword"]
                vol = kw_data["volume"]
                cpc = kw_data["cpc"]
                if vol >= self.min_volume and cpc >= self.min_cpc and kw not in expanded:
                    expanded.add(kw)
                    added += 1
                    if len(expanded) >= 50:
                        break

            self._log(f"   -> +{added} keywords (total: {len(expanded)})")
            pct = 6 + int((i + 1) / len(seeds_to_expand) * 14)
            self._progress(pct, f"Keyword expansion: {len(expanded)} keywords")
            if len(expanded) >= 50:
                break

        self.keywords = list(expanded)
        self._log(f"   Total unique keywords: {len(self.keywords)}")
        self._progress(20, f"{len(self.keywords)} keywords ready for search")

    # ── Phase 3: Domain Discovery ───────────────────────────────────────────

    def _phase3_domain_discovery(self):
        self._progress(21, "Discovering business domains...")
        self._log("Phase 3: Domain discovery via SEMrush + SerpApi")

        db = self.config["semrush_db"]
        gl = self.config["serpapi_gl"]
        all_domains = set()

        # Use top keywords for domain discovery
        keywords_to_search = self.keywords[:20]
        total_steps = len(keywords_to_search)

        for i, kw in enumerate(keywords_to_search):
            if self._cancelled:
                return

            # SEMrush organic — find sites ranking for this keyword
            organic_results = self.semrush.get_organic_domains(kw, db, limit=10)
            for r in organic_results:
                d = r["domain"]
                if d not in all_domains:
                    all_domains.add(d)

            # SEMrush adwords — find sites running ads (high-intent)
            ad_results = self.semrush.get_adwords_domains(kw, db, limit=5)
            for r in ad_results:
                d = r["domain"]
                if d not in all_domains:
                    all_domains.add(d)

            # SerpApi as supplementary source (may be out of credits)
            if i < 5:  # Only first 5 keywords to conserve credits
                serp_domains = self.serpapi.search_keyword(f"{kw} {self.config['location_suffix']}", gl, num=10)
                for d in serp_domains:
                    if d not in all_domains:
                        all_domains.add(d)

            if (i + 1) % 5 == 0 or i == total_steps - 1:
                self._log(f"   Searched {i + 1}/{total_steps} keywords -> {len(all_domains)} domains")

            pct = 21 + int((i + 1) / total_steps * 24)
            self._progress(pct, f"Found {len(all_domains)} unique domains")

            if len(all_domains) >= 80:
                self._log("   Reached domain cap (80). Moving to enrichment.")
                break

        self.domains = list(all_domains)[:80]
        self._log(f"   Total prospect domains: {len(self.domains)}")
        self._progress(45, f"{len(self.domains)} domains ready for enrichment")

    # ── Phase 4: Lead Enrichment ────────────────────────────────────────────

    def _phase4_enrichment(self):
        self._progress(46, "Enriching leads...")
        self._log("Phase 4: Multi-source lead enrichment")

        total = len(self.domains)
        for i, domain in enumerate(self.domains):
            if self._cancelled:
                return

            domain_leads = []
            company_name = ""
            company_phone = ""

            # Step 1: Apollo organization enrichment — get company name + phone
            org_data = self.apollo.enrich_organization(domain)
            if org_data:
                company_name = org_data.get("company_name", "")
                company_phone = org_data.get("phone", "")
                if company_name:
                    self._log(f"   [{i + 1}/{total}] {company_name} ({domain})")
                else:
                    self._log(f"   [{i + 1}/{total}] {domain}")
            else:
                self._log(f"   [{i + 1}/{total}] {domain}")

            # Step 2: Apollo people search — get names and roles
            people = self.apollo.search_people_by_domain(domain, per_page=5)
            for person in people:
                first = person.get("first_name", "")
                last = person.get("last_name", "")
                title = person.get("title", "")
                email = person.get("email", "")
                if first:
                    lead = {
                        "name": f"{first} {last}".strip() if last else first,
                        "domain": domain,
                        "company": company_name or person.get("organization", {}).get("name", ""),
                        "role": title,
                        "email": email or "",
                        "phone": "",
                        "source": "Apollo",
                    }
                    domain_leads.append(lead)

            # Step 3: Lusha company data — fill in company details
            if not company_name:
                lusha_company = self.lusha.get_company_info(domain)
                if lusha_company:
                    company_name = lusha_company.get("company_name", "")
                    # Update all leads with company name
                    for ld in domain_leads:
                        if not ld.get("company"):
                            ld["company"] = company_name

            # Step 4: Lusha person enrichment — try for leads with full names
            for ld in domain_leads:
                if ld.get("name") and " " in ld["name"]:
                    parts = ld["name"].split()
                    first_n = parts[0]
                    last_n = parts[-1]
                    if last_n and len(last_n) > 1:  # Has a real last name
                        lusha_person = self.lusha.enrich_person(first_n, last_n, domain)
                        if lusha_person:
                            if not ld.get("email") and lusha_person.get("email"):
                                ld["email"] = lusha_person["email"]
                            if not ld.get("phone") and lusha_person.get("phone"):
                                ld["phone"] = lusha_person["phone"]
                            if not ld.get("role") and lusha_person.get("role"):
                                ld["role"] = lusha_person["role"]
                            ld["source"] += "+Lusha"

            # Step 5: Web scraping — always scrape for emails and phones
            scraped = self.scraper.scrape_domain(domain)
            scraped_company = scraped.get("company_name", "")
            scraped_emails = scraped.get("emails", [])
            scraped_phones = scraped.get("phones", [])

            if not company_name and scraped_company:
                company_name = scraped_company

            # Fill missing data in existing leads from scraping
            email_idx = 0
            for ld in domain_leads:
                if not ld.get("email") and email_idx < len(scraped_emails):
                    ld["email"] = scraped_emails[email_idx]
                    email_idx += 1
                    ld["source"] += "+Scrape"
                if not ld.get("phone"):
                    if scraped_phones:
                        ld["phone"] = scraped_phones[0]
                    elif company_phone:
                        ld["phone"] = company_phone
                if not ld.get("company"):
                    ld["company"] = company_name or domain_to_company_name(domain)

            # Step 6: SerpApi business info fallback (for missing phones)
            for ld in domain_leads:
                if not ld.get("phone") and ld.get("company"):
                    info = self.serpapi.search_business_info(ld["company"], self.config["serpapi_gl"])
                    if info.get("phone"):
                        ld["phone"] = info["phone"]
                        ld["source"] += "+SerpApi"
                    if not ld.get("email") and info.get("email"):
                        ld["email"] = info["email"]

            # If Apollo found people, use them
            if domain_leads:
                self.leads.extend(domain_leads)
            else:
                # Fallback: create a domain-level lead from scraped/org data
                fallback = {
                    "name": "",
                    "domain": domain,
                    "company": company_name or domain_to_company_name(domain),
                    "role": "",
                    "email": scraped_emails[0] if scraped_emails else "",
                    "phone": company_phone or (scraped_phones[0] if scraped_phones else ""),
                    "source": "Org+Scrape",
                }
                if fallback["email"] or fallback["phone"]:
                    self.leads.append(fallback)

            pct = 46 + int((i + 1) / total * 44)
            self._progress(pct, f"Enriched {i + 1}/{total} domains ({len(self.leads)} leads)")

        self._log(f"   Total raw leads: {len(self.leads)}")
        self._progress(90, f"{len(self.leads)} raw leads collected")

    # ── Phase 5: Data Cleanup ───────────────────────────────────────────────

    def _phase5_cleanup(self):
        self._progress(91, "Cleaning and deduplicating leads...")
        self._log("Phase 5: Data cleanup")

        phone_code = self.config["phone_code"]
        cleaned = []
        seen = set()

        for lead in self.leads:
            # Format phone number
            if lead.get("phone"):
                lead["phone"] = format_phone(lead["phone"], phone_code)

            # Clean company name
            if not lead.get("company") or lead["company"] == lead.get("domain", ""):
                lead["company"] = domain_to_company_name(lead.get("domain", ""))

            # Validate email
            if lead.get("email") and not is_valid_email(lead["email"]):
                lead["email"] = ""

            # Skip entries with no useful data at all
            if not lead.get("name") and not lead.get("email") and not lead.get("phone"):
                continue

            # Deduplicate
            dedup_key = ""
            if lead.get("name") and lead.get("domain"):
                dedup_key = f"{lead['name'].lower()}|{lead['domain'].lower()}"
            elif lead.get("email"):
                dedup_key = lead["email"].lower()
            else:
                dedup_key = f"{lead.get('phone', '')}|{lead.get('domain', '')}"

            if dedup_key and dedup_key in seen:
                continue
            if dedup_key:
                seen.add(dedup_key)

            cleaned.append(lead)

        self.leads = cleaned
        self._log(f"   Final leads after cleanup: {len(self.leads)}")
        self._progress(95, f"{len(self.leads)} leads cleaned")

    # ── Phase 6: CSV Export ─────────────────────────────────────────────────

    def _phase6_export(self) -> str:
        self._progress(96, "Exporting CSV...")
        self._log("Phase 6: CSV export")

        if not self.leads:
            self._log("   No leads to export.")
            return ""

        os.makedirs(self.output_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        industry_slug = re.sub(r"[^\w]+", "_", self.industry.lower()).strip("_")
        filename = f"leads_{industry_slug}_{self.country}_{timestamp}.csv"
        filepath = os.path.join(self.output_folder, filename)

        fieldnames = ["Name", "Company Name", "Domain", "Role", "Phone Number", "Email", "Notes"]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for lead in self.leads:
                notes_parts = []
                if lead.get("source"):
                    notes_parts.append(f"Source: {lead['source']}")
                row = {
                    "Name": lead.get("name", ""),
                    "Company Name": lead.get("company", ""),
                    "Domain": lead.get("domain", ""),
                    "Role": lead.get("role", ""),
                    "Phone Number": lead.get("phone", ""),
                    "Email": lead.get("email", ""),
                    "Notes": " | ".join(notes_parts),
                }
                writer.writerow(row)

        self._log(f"   Saved {len(self.leads)} leads to: {filepath}")
        self._progress(100, f"Done! {len(self.leads)} leads exported")
        return filepath


# ══════════════════════════════════════════════════════════════════════════════
# GUI APPLICATION — Dark Theme
# ══════════════════════════════════════════════════════════════════════════════

# Lazy-load tkinter — only imported when GUI is actually started (main())
# This allows the pipeline/API classes above to be imported without tkinter
tk = None
ttk = None
filedialog = None
messagebox = None

# Color palette
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "bg_card": "#1f2b47",
    "accent": "#e94560",
    "accent_hover": "#ff6b81",
    "text_primary": "#eaeaea",
    "text_secondary": "#a0a0b0",
    "text_muted": "#6c6c80",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#e74c3c",
    "input_bg": "#0d1b2a",
    "input_border": "#1b2838",
    "button_bg": "#e94560",
    "button_fg": "#ffffff",
    "progress_bg": "#0d1b2a",
    "progress_fg": "#e94560",
    "log_bg": "#0a0f1a",
}


class LeadGeneratorApp:
    """Main GUI application with dark theme."""

    def __init__(self, root):
        self.root = root
        self.root.title("Lead Generation Pro")
        self.root.geometry("820x740")
        self.root.minsize(780, 700)
        self.root.configure(bg=COLORS["bg_dark"])

        self.pipeline = None
        self.pipeline_thread = None

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=COLORS["bg_dark"])
        style.configure("Card.TFrame", background=COLORS["bg_card"])
        style.configure(
            "Dark.TLabel", background=COLORS["bg_dark"],
            foreground=COLORS["text_primary"], font=("Segoe UI", 10),
        )
        style.configure(
            "CardLabel.TLabel", background=COLORS["bg_card"],
            foreground=COLORS["text_primary"], font=("Segoe UI", 10),
        )
        style.configure(
            "Header.TLabel", background=COLORS["bg_dark"],
            foreground=COLORS["accent"], font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "SubHeader.TLabel", background=COLORS["bg_dark"],
            foreground=COLORS["text_secondary"], font=("Segoe UI", 10),
        )
        style.configure(
            "Dark.TCombobox",
            fieldbackground=COLORS["input_bg"], background=COLORS["bg_light"],
            foreground=COLORS["text_primary"],
            selectbackground=COLORS["accent"], selectforeground=COLORS["button_fg"],
        )
        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=COLORS["progress_bg"], background=COLORS["progress_fg"], thickness=8,
        )

        # Main container
        main = ttk.Frame(self.root, style="Dark.TFrame", padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(main, text="Lead Generation Pro", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 2))
        ttk.Label(main, text="Discover & enrich B2B leads automatically", style="SubHeader.TLabel").pack(
            anchor=tk.W, pady=(0, 15)
        )

        # Input Card
        card = ttk.Frame(main, style="Card.TFrame", padding=15)
        card.pack(fill=tk.X, pady=(0, 12))

        # Row 1: Industry + Country
        row1 = ttk.Frame(card, style="Card.TFrame")
        row1.pack(fill=tk.X, pady=(0, 10))

        ind_frame = ttk.Frame(row1, style="Card.TFrame")
        ind_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Label(ind_frame, text="Industry", style="CardLabel.TLabel").pack(anchor=tk.W)
        self.industry_var = tk.StringVar(value="Dentist")
        self.industry_combo = ttk.Combobox(
            ind_frame, textvariable=self.industry_var,
            values=sorted(INDUSTRY_KEYWORDS.keys()),
            style="Dark.TCombobox", state="normal", font=("Segoe UI", 10),
        )
        self.industry_combo.pack(fill=tk.X, pady=(3, 0))

        country_frame = ttk.Frame(row1, style="Card.TFrame")
        country_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(country_frame, text="Country", style="CardLabel.TLabel").pack(anchor=tk.W)
        self.country_var = tk.StringVar(value="AU")
        self.country_combo = ttk.Combobox(
            country_frame, textvariable=self.country_var,
            values=["AU", "USA", "UK", "India"],
            style="Dark.TCombobox", state="readonly", font=("Segoe UI", 10),
        )
        self.country_combo.pack(fill=tk.X, pady=(3, 0))

        # Row 2: Volume + CPC
        row2 = ttk.Frame(card, style="Card.TFrame")
        row2.pack(fill=tk.X, pady=(0, 10))

        vol_frame = ttk.Frame(row2, style="Card.TFrame")
        vol_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Label(vol_frame, text="Min Search Volume", style="CardLabel.TLabel").pack(anchor=tk.W)
        self.volume_var = tk.StringVar(value="50")
        tk.Entry(
            vol_frame, textvariable=self.volume_var,
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"], font=("Segoe UI", 10),
            relief=tk.FLAT, bd=5,
        ).pack(fill=tk.X, pady=(3, 0))

        cpc_frame = ttk.Frame(row2, style="Card.TFrame")
        cpc_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(cpc_frame, text="Min CPC ($)", style="CardLabel.TLabel").pack(anchor=tk.W)
        self.cpc_var = tk.StringVar(value="1.0")
        tk.Entry(
            cpc_frame, textvariable=self.cpc_var,
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"], font=("Segoe UI", 10),
            relief=tk.FLAT, bd=5,
        ).pack(fill=tk.X, pady=(3, 0))

        # Row 3: Output folder
        row3 = ttk.Frame(card, style="Card.TFrame")
        row3.pack(fill=tk.X)
        ttk.Label(row3, text="Output Folder", style="CardLabel.TLabel").pack(anchor=tk.W)
        folder_row = ttk.Frame(row3, style="Card.TFrame")
        folder_row.pack(fill=tk.X, pady=(3, 0))

        self.folder_var = tk.StringVar(value=self._default_output_folder())
        tk.Entry(
            folder_row, textvariable=self.folder_var,
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"], font=("Segoe UI", 10),
            relief=tk.FLAT, bd=5,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(
            folder_row, text="Browse", bg=COLORS["bg_light"], fg=COLORS["text_primary"],
            font=("Segoe UI", 9), relief=tk.FLAT, padx=10, pady=4,
            command=self._browse_folder,
        ).pack(side=tk.RIGHT)

        # Action Buttons
        btn_frame = ttk.Frame(main, style="Dark.TFrame")
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.generate_btn = tk.Button(
            btn_frame, text="   Generate Leads   ",
            bg=COLORS["accent"], fg=COLORS["button_fg"],
            activebackground=COLORS["accent_hover"], activeforeground=COLORS["button_fg"],
            font=("Segoe UI", 12, "bold"), relief=tk.FLAT, padx=25, pady=8,
            cursor="hand2", command=self._on_generate,
        )
        self.generate_btn.pack(side=tk.LEFT)

        self.cancel_btn = tk.Button(
            btn_frame, text="  Cancel  ",
            bg=COLORS["bg_light"], fg=COLORS["text_primary"],
            activebackground=COLORS["bg_medium"],
            font=("Segoe UI", 10), relief=tk.FLAT, padx=15, pady=6,
            state=tk.DISABLED, command=self._on_cancel,
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            btn_frame, textvariable=self.status_var,
            bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
            font=("Segoe UI", 10), anchor=tk.E,
        ).pack(side=tk.RIGHT)

        # Progress Bar
        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(
            main, variable=self.progress_var, maximum=100, mode="determinate",
            style="Dark.Horizontal.TProgressbar",
        ).pack(fill=tk.X, pady=(0, 12))

        # Log Panel
        ttk.Label(main, text="Activity Log", style="Dark.TLabel").pack(anchor=tk.W, pady=(0, 3))
        log_frame = tk.Frame(main, bg=COLORS["log_bg"])
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame, bg=COLORS["log_bg"], fg=COLORS["text_secondary"],
            font=("Consolas", 9), relief=tk.FLAT, wrap=tk.WORD,
            state=tk.DISABLED, padx=10, pady=8, spacing1=2,
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text.tag_configure("success", foreground=COLORS["success"])
        self.log_text.tag_configure("error", foreground=COLORS["error"])
        self.log_text.tag_configure("warning", foreground=COLORS["warning"])

    def _default_output_folder(self) -> str:
        if platform.system() == "Windows":
            return r"C:\AI LEAD GENERATION AGENT ai code\___LEADS GENERATED___"
        return os.path.join(os.path.expanduser("~"), "LeadGen_Output")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder", initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    def _validate_inputs(self) -> bool:
        if not self.industry_var.get().strip():
            messagebox.showwarning("Input Required", "Please enter an industry.")
            return False
        try:
            vol = int(self.volume_var.get())
            if vol < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Min Search Volume must be a positive number.")
            return False
        try:
            cpc = float(self.cpc_var.get())
            if cpc < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Min CPC must be a positive number.")
            return False
        if not self.folder_var.get().strip():
            messagebox.showwarning("Input Required", "Please specify an output folder.")
            return False
        return True

    def _on_generate(self):
        if not self._validate_inputs():
            return
        self.generate_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        self._clear_log()

        self.pipeline = LeadGenerationPipeline(
            industry=self.industry_var.get().strip(),
            country=self.country_var.get().strip(),
            min_volume=int(self.volume_var.get()),
            min_cpc=float(self.cpc_var.get()),
            output_folder=self.folder_var.get().strip(),
            progress_callback=self._update_progress_safe,
            log_callback=self._append_log_safe,
        )
        self.pipeline_thread = threading.Thread(target=self._run_pipeline, daemon=True)
        self.pipeline_thread.start()

    def _run_pipeline(self):
        result_path = self.pipeline.run()
        self.root.after(0, self._on_pipeline_done, result_path)

    def _on_pipeline_done(self, result_path: str):
        self.generate_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
        if result_path:
            count = len(self.pipeline.leads) if self.pipeline else 0
            self.status_var.set(f"Done! {count} leads exported")
            messagebox.showinfo("Success", f"Generated {count} leads!\n\nSaved to:\n{result_path}")
        elif self.pipeline and self.pipeline._cancelled:
            self.status_var.set("Cancelled")
        else:
            self.status_var.set("Completed (no leads found)")
            messagebox.showwarning(
                "No Results",
                "No leads were found. Try a different industry or lower the search volume/CPC thresholds.",
            )

    def _on_cancel(self):
        if self.pipeline:
            self.pipeline.cancel()
            self.cancel_btn.configure(state=tk.DISABLED)
            self.status_var.set("Cancelling...")

    def _update_progress_safe(self, pct: int, status: str = ""):
        self.root.after(0, self._update_progress, pct, status)

    def _update_progress(self, pct: int, status: str = ""):
        self.progress_var.set(pct)
        if status:
            self.status_var.set(status)

    def _append_log_safe(self, message: str):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.log_text.configure(state=tk.NORMAL)
        tag = ""
        if "Done" in message or "Saved" in message or "Total" in message:
            tag = "success"
        elif "Error" in message or "error" in message:
            tag = "error"
        elif "Warning" in message or "warning" in message:
            tag = "warning"
        self.log_text.insert(tk.END, message + "\n", tag if tag else ())
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import tkinter as tk_mod
    from tkinter import filedialog as fd_mod, messagebox as mb_mod, ttk as ttk_mod

    global tk, ttk, filedialog, messagebox
    tk = tk_mod
    ttk = ttk_mod
    filedialog = fd_mod
    messagebox = mb_mod

    root = tk.Tk()
    LeadGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
