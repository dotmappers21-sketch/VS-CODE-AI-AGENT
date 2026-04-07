const express = require("express");
const cors = require("cors");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// ── Smart Cache (5-minute TTL) ──────────────────────────────────────────
let cache = { data: null, timestamp: 0 };
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function isCacheValid() {
  return cache.data && Date.now() - cache.timestamp < CACHE_TTL;
}

// ── API Fetchers ────────────────────────────────────────────────────────

async function fetchApolloCredits() {
  const apiKey = process.env.APOLLO_API_KEY;
  if (!apiKey) return { status: "error", error: "No API key configured" };
  try {
    const resp = await fetch("https://api.apollo.io/api/v1/auth/health", {
      headers: { "X-Api-Key": apiKey, "Content-Type": "application/json" },
    });
    if (!resp.ok) return { status: "error", error: `HTTP ${resp.status}` };
    const data = await resp.json();
    const plan = data.plan || {};
    const total = plan.credits_limit || 10000;
    const used = plan.credits_used || 0;
    const remaining = Math.max(0, total - used);
    const percentage = total > 0 ? Math.round((remaining / total) * 100) : 0;
    return {
      remaining,
      total,
      percentage,
      remainingSearches: Math.floor(remaining / 2),
      resetDate: plan.reset_date || "N/A",
      usageRate: Math.round(used / Math.max(1, getDaysInMonth())),
      status: "success",
    };
  } catch (err) {
    return { status: "error", error: err.message };
  }
}

async function fetchLushaCredits() {
  const apiKey = process.env.LUSHA_API_KEY;
  if (!apiKey) return { status: "error", error: "No API key configured" };
  try {
    const resp = await fetch("https://api.lusha.com/v2/account/balance", {
      headers: { api_key: apiKey, "Content-Type": "application/json" },
    });
    if (!resp.ok) return { status: "error", error: `HTTP ${resp.status}` };
    const data = await resp.json();
    const remaining = data.credits_remaining ?? data.remaining ?? 0;
    const total = data.credits_total ?? data.total ?? remaining;
    const percentage = total > 0 ? Math.round((remaining / total) * 100) : 0;
    return {
      remaining,
      total,
      percentage,
      remainingSearches: Math.floor(remaining / 2),
      resetDate: data.reset_date || "N/A",
      usageRate: Math.round((total - remaining) / Math.max(1, getDaysInMonth())),
      status: "success",
    };
  } catch (err) {
    return { status: "error", error: err.message };
  }
}

async function fetchSemrushCredits() {
  const apiKey = process.env.SEMRUSH_API_KEY;
  if (!apiKey) return { status: "error", error: "No API key configured" };
  try {
    const resp = await fetch(
      `https://www.semrush.com/users/countapiunits.html?key=${apiKey}`
    );
    if (!resp.ok) return { status: "error", error: `HTTP ${resp.status}` };
    const text = await resp.text();
    const remaining = parseInt(text.trim(), 10);
    if (isNaN(remaining))
      return { status: "error", error: "Invalid response" };
    const total = 10000; // SEMrush standard plan
    const percentage = total > 0 ? Math.round((remaining / total) * 100) : 0;
    return {
      remaining,
      total,
      percentage,
      remainingSearches: Math.floor(remaining / 2.67),
      resetDate: getMonthEndDate(),
      usageRate: Math.round((total - remaining) / Math.max(1, getDaysInMonth())),
      status: "success",
    };
  } catch (err) {
    return { status: "error", error: err.message };
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────

function getDaysInMonth() {
  const now = new Date();
  return now.getDate();
}

function getMonthEndDate() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth() + 1, 1)
    .toISOString()
    .split("T")[0];
}

function buildSummary(apollo, lusha, semrush) {
  const services = [apollo, lusha, semrush];
  const healthy = services.filter(
    (s) => s.status === "success" && s.percentage > 20
  ).length;
  const low = services.filter(
    (s) => s.status === "success" && s.percentage > 5 && s.percentage <= 20
  ).length;
  const critical = services.filter(
    (s) => s.status === "success" && s.percentage <= 5
  ).length;
  const totalSearches = services.reduce(
    (sum, s) => sum + (s.remainingSearches || 0),
    0
  );
  return {
    totalSearchesAvailable: totalSearches,
    servicesHealthy: healthy,
    servicesLow: low,
    servicesCritical: critical,
  };
}

// ── Routes ──────────────────────────────────────────────────────────────

app.get("/api/credits", async (req, res) => {
  if (isCacheValid()) {
    return res.json(cache.data);
  }
  try {
    const [apollo, lusha, semrush] = await Promise.all([
      fetchApolloCredits(),
      fetchLushaCredits(),
      fetchSemrushCredits(),
    ]);
    const result = {
      apollo,
      lusha,
      semrush,
      summary: buildSummary(apollo, lusha, semrush),
      lastUpdated: new Date().toISOString(),
      timestamp: Date.now(),
    };
    cache = { data: result, timestamp: Date.now() };
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch credits", details: err.message });
  }
});

app.post("/api/credits/refresh", async (req, res) => {
  cache = { data: null, timestamp: 0 }; // Clear cache
  try {
    const [apollo, lusha, semrush] = await Promise.all([
      fetchApolloCredits(),
      fetchLushaCredits(),
      fetchSemrushCredits(),
    ]);
    const result = {
      apollo,
      lusha,
      semrush,
      summary: buildSummary(apollo, lusha, semrush),
      lastUpdated: new Date().toISOString(),
      timestamp: Date.now(),
    };
    cache = { data: result, timestamp: Date.now() };
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: "Failed to refresh credits", details: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Credits Dashboard API running on http://localhost:${PORT}`);
});
