import React from "react";
import { useCreditsContext } from "./useCreditsContext";

/* ── Inline SVG Icons (Lucide-style) ─────────────────────────────────── */
const Icon = ({ d, size = 20, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const icons = {
  rocket: "M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09zM12 15l-3-3M22 2l-7.5 7.5M9.66 9.66a8 8 0 1 0 4.68 4.68",
  search: "M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM21 21l-4.35-4.35",
  refresh: "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8M21 3v5h-5M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16M3 21v-5h5",
  alert: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01",
  check: "M20 6L9 17l-5-5",
  zap: "M13 2L3 14h9l-1 8 10-12h-9l1-8",
};

/* ── Styles ──────────────────────────────────────────────────────────── */
const styles = {
  container: {
    minHeight: "100vh", padding: "24px",
    background: "linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%)",
  },
  header: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    marginBottom: 32, flexWrap: "wrap", gap: 16,
  },
  title: { fontSize: 28, fontWeight: 700, color: "#fff", display: "flex", alignItems: "center", gap: 12 },
  subtitle: { fontSize: 14, color: "#8888aa", marginTop: 4 },
  refreshBtn: {
    background: "linear-gradient(135deg, #e94560, #ff6b81)", border: "none",
    color: "#fff", padding: "10px 20px", borderRadius: 8, cursor: "pointer",
    fontSize: 14, fontWeight: 600, display: "flex", alignItems: "center", gap: 8,
    transition: "transform 0.2s, box-shadow 0.2s",
  },
  grid: {
    display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: 20, marginBottom: 24,
  },
  card: {
    background: "linear-gradient(145deg, #1f2b47, #16213e)",
    borderRadius: 16, padding: 24, border: "1px solid #2a3a5c",
    boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
  },
  summaryCard: {
    background: "linear-gradient(135deg, #1a1a2e, #0f3460)",
    borderRadius: 16, padding: 24, marginBottom: 24,
    border: "1px solid #e94560", boxShadow: "0 4px 20px rgba(233,69,96,0.15)",
  },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  serviceName: { fontSize: 18, fontWeight: 600, color: "#fff" },
  badge: (color) => ({
    padding: "4px 12px", borderRadius: 12, fontSize: 12, fontWeight: 600,
    background: `${color}22`, color, border: `1px solid ${color}44`,
  }),
  creditsRow: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 },
  creditsNum: { fontSize: 32, fontWeight: 700, color: "#fff" },
  creditsTotal: { fontSize: 14, color: "#8888aa" },
  progressBg: { height: 8, borderRadius: 4, background: "#0d1b2a", marginBottom: 16, overflow: "hidden" },
  progressFill: (pct, color) => ({
    height: "100%", borderRadius: 4, width: `${pct}%`,
    background: `linear-gradient(90deg, ${color}, ${color}cc)`,
    transition: "width 0.8s ease-in-out",
  }),
  statRow: { display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #1a2540" },
  statLabel: { fontSize: 13, color: "#8888aa" },
  statValue: { fontSize: 13, color: "#e0e0e0", fontWeight: 500 },
  searchesHighlight: {
    background: "linear-gradient(135deg, #0f3460, #1a1a2e)",
    borderRadius: 12, padding: "16px 20px", marginTop: 16, textAlign: "center",
    border: "1px solid #2a3a5c",
  },
  searchesNum: { fontSize: 24, fontWeight: 700, color: "#e94560" },
  searchesLabel: { fontSize: 12, color: "#8888aa", marginTop: 4 },
  summaryGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 16 },
  summaryItem: { textAlign: "center" },
  summaryNum: { fontSize: 36, fontWeight: 800, color: "#e94560" },
  summaryLabel: { fontSize: 12, color: "#8888aa" },
  timestamp: { textAlign: "center", color: "#666", fontSize: 12, marginTop: 16 },
  error: {
    background: "#e7453022", border: "1px solid #e74530", borderRadius: 12,
    padding: 16, textAlign: "center", color: "#ff6b6b", marginBottom: 24,
  },
  loading: { textAlign: "center", padding: 80, color: "#8888aa", fontSize: 18 },
  alertBanner: (color) => ({
    background: `${color}15`, border: `1px solid ${color}44`, borderRadius: 12,
    padding: "12px 20px", marginBottom: 16, display: "flex", alignItems: "center", gap: 12,
    color, fontSize: 14, fontWeight: 500,
  }),
};

/* ── Helpers ─────────────────────────────────────────────────────────── */
function getColor(pct) {
  if (pct > 20) return "#2ecc71";
  if (pct > 5) return "#f39c12";
  return "#e74c3c";
}
function fmt(n) { return (n || 0).toLocaleString(); }

/* ── ServiceCard Component ───────────────────────────────────────────── */
function ServiceCard({ name, data }) {
  if (!data || data.status === "error") {
    return (
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <span style={styles.serviceName}>{name}</span>
          <span style={styles.badge("#e74c3c")}>Error</span>
        </div>
        <p style={{ color: "#ff6b6b", fontSize: 14 }}>{data?.error || "Unavailable"}</p>
      </div>
    );
  }
  const color = getColor(data.percentage);
  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <span style={styles.serviceName}>{name}</span>
        <span style={styles.badge(color)}>{data.percentage}%</span>
      </div>
      <div style={styles.creditsRow}>
        <span style={styles.creditsNum}>{fmt(data.remaining)}</span>
        <span style={styles.creditsTotal}>/ {fmt(data.total)}</span>
      </div>
      <div style={styles.progressBg}>
        <div style={styles.progressFill(data.percentage, color)} />
      </div>
      <div style={styles.searchesHighlight}>
        <div style={styles.searchesNum}>
          <Icon d={icons.search} size={18} color="#e94560" /> {fmt(data.remainingSearches)}
        </div>
        <div style={styles.searchesLabel}>searches available</div>
      </div>
      <div style={{ marginTop: 16 }}>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Reset Date</span>
          <span style={styles.statValue}>{data.resetDate || "N/A"}</span>
        </div>
        <div style={styles.statRow}>
          <span style={styles.statLabel}>Daily Usage Rate</span>
          <span style={styles.statValue}>{fmt(data.usageRate)} / day</span>
        </div>
      </div>
    </div>
  );
}

/* ── Main Dashboard ──────────────────────────────────────────────────── */
export function CreditsDashboard() {
  const { data, loading, error, lastFetched, refresh } = useCreditsContext();

  if (loading && !data) {
    return <div style={styles.loading}>Loading credits data...</div>;
  }

  const summary = data?.summary || {};
  const alerts = [];
  if (summary.servicesCritical > 0)
    alerts.push({ msg: `${summary.servicesCritical} service(s) critically low on credits!`, color: "#e74c3c" });
  if (summary.servicesLow > 0)
    alerts.push({ msg: `${summary.servicesLow} service(s) running low on credits`, color: "#f39c12" });

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <div style={styles.title}>
            <Icon d={icons.zap} size={28} color="#e94560" />
            API Credits & Lead Searches
          </div>
          <div style={styles.subtitle}>Real-time monitoring of Apollo, Lusha & Semrush API usage</div>
        </div>
        <button style={styles.refreshBtn} onClick={refresh}
          onMouseOver={(e) => { e.currentTarget.style.transform = "scale(1.05)"; }}
          onMouseOut={(e) => { e.currentTarget.style.transform = "scale(1)"; }}>
          <Icon d={icons.refresh} size={16} /> Refresh Now
        </button>
      </div>

      {/* Error banner */}
      {error && <div style={styles.error}>{error}</div>}

      {/* Alert banners */}
      {alerts.map((a, i) => (
        <div key={i} style={styles.alertBanner(a.color)}>
          <Icon d={icons.alert} size={18} color={a.color} /> {a.msg}
        </div>
      ))}

      {/* Summary card */}
      {data && (
        <div style={styles.summaryCard}>
          <div style={styles.summaryGrid}>
            <div style={styles.summaryItem}>
              <div style={styles.summaryNum}>{fmt(summary.totalSearchesAvailable)}</div>
              <div style={styles.summaryLabel}>Total Searches Available</div>
            </div>
            <div style={styles.summaryItem}>
              <div style={{ ...styles.summaryNum, color: "#2ecc71" }}>{summary.servicesHealthy || 0}</div>
              <div style={styles.summaryLabel}>Healthy</div>
            </div>
            <div style={styles.summaryItem}>
              <div style={{ ...styles.summaryNum, color: "#f39c12" }}>{summary.servicesLow || 0}</div>
              <div style={styles.summaryLabel}>Low</div>
            </div>
            <div style={styles.summaryItem}>
              <div style={{ ...styles.summaryNum, color: "#e74c3c" }}>{summary.servicesCritical || 0}</div>
              <div style={styles.summaryLabel}>Critical</div>
            </div>
          </div>
        </div>
      )}

      {/* Service cards */}
      <div style={styles.grid}>
        <ServiceCard name="Apollo.io" data={data?.apollo} />
        <ServiceCard name="Lusha" data={data?.lusha} />
        <ServiceCard name="Semrush" data={data?.semrush} />
      </div>

      {/* Timestamp */}
      <div style={styles.timestamp}>
        Last updated: {lastFetched ? lastFetched.toLocaleTimeString() : "—"} • Auto-refreshes every 30s
      </div>
    </div>
  );
}
