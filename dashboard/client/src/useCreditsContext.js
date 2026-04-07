import { useState, useEffect, useCallback, useRef } from "react";

const API_BASE = "/api";
const REFRESH_INTERVAL = 30_000; // 30 seconds

export function useCreditsContext() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetched, setLastFetched] = useState(null);
  const intervalRef = useRef(null);

  const fetchCredits = useCallback(async (isManual = false) => {
    try {
      setLoading(true);
      setError(null);
      const url = isManual ? `${API_BASE}/credits/refresh` : `${API_BASE}/credits`;
      const opts = isManual ? { method: "POST" } : {};
      const resp = await fetch(url, opts);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      setData(json);
      setLastFetched(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(() => fetchCredits(true), [fetchCredits]);

  useEffect(() => {
    fetchCredits();
    intervalRef.current = setInterval(() => fetchCredits(), REFRESH_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, [fetchCredits]);

  return { data, loading, error, lastFetched, refresh };
}
