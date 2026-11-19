"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchHealth, fetchPresetCatalogue, HealthResponse, PresetMetadata, ApiError } from "@/lib/api";
import { CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";

interface ApiStatusBannerProps {
  onPresetsLoaded?: (presets: PresetMetadata[]) => void;
  compact?: boolean;
  className?: string;
}

export function ApiStatusBanner({ onPresetsLoaded, compact = false, className = "" }: ApiStatusBannerProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [presetCount, setPresetCount] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialStatus() {
      try {
        const [hData, pData] = await Promise.all([fetchHealth(), fetchPresetCatalogue()]);
        if (!cancelled) {
          setHealth(hData);
          setPresetCount(pData.presets.length);
          if (onPresetsLoaded) {
            onPresetsLoaded(pData.presets);
          }
          setError(null);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Could not reach scientific backend at http://127.0.0.1:8000.");
          }
          setHealth(null);
          setLoading(false);
        }
      }
    }

    loadInitialStatus();

    return () => {
      cancelled = true;
    };
  }, [onPresetsLoaded]);

  const handleManualRetry = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hData, pData] = await Promise.all([fetchHealth(), fetchPresetCatalogue()]);
      setHealth(hData);
      setPresetCount(pData.presets.length);
      if (onPresetsLoaded) {
        onPresetsLoaded(pData.presets);
      }
      setError(null);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Could not reach scientific backend at http://127.0.0.1:8000.");
      }
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, [onPresetsLoaded]);

  if (compact) {
    if (loading) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[var(--muted)]">
          <RefreshCw className="h-3 w-3 animate-spin text-[var(--muted-light)]" />
          <span>Connecting API...</span>
        </span>
      );
    }

    if (error) {
      return (
        <button
          type="button"
          onClick={handleManualRetry}
          className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[var(--crimson)] hover:text-rose-400 bg-[var(--crimson-light)] px-2 py-0.5 rounded-sm border border-[var(--crimson-border)] transition-colors cursor-pointer"
          title={error}
        >
          <AlertTriangle className="h-3 w-3 text-[var(--crimson)]" />
          <span>API Offline (Retry)</span>
        </button>
      );
    }

    return (
      <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[var(--emerald)] bg-[var(--emerald-light)] px-2 py-0.5 rounded-sm border border-emerald-500/30">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--emerald)] animate-pulse" />
        <span>API Online (v{health?.version})</span>
      </span>
    );
  }

  return (
    <div
      className={`rounded-sm border p-4 text-xs font-sans transition-all shadow-xs ${
        loading
          ? "border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--muted)]"
          : error
          ? "border-[var(--crimson-border)] bg-[var(--crimson-light)] text-[var(--foreground)]"
          : "border-emerald-500/30 bg-[var(--surface-subtle)] text-[var(--foreground)]"
      } ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-start gap-3">
          {loading ? (
            <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-[var(--surface)] text-[var(--muted)] border border-[var(--border)] shrink-0">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-rose-950/40 text-[var(--crimson)] border border-[var(--crimson-border)] shrink-0">
              <AlertTriangle className="h-3.5 w-3.5 text-[var(--crimson)]" />
            </div>
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-emerald-950/40 text-[var(--emerald)] border border-emerald-500/40 shrink-0">
              <CheckCircle2 className="h-4 w-4 text-[var(--emerald)]" />
            </div>
          )}

          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-xs tracking-tight text-[var(--foreground)]">
                {loading
                  ? "Verifying Engine API Connectivity..."
                  : error
                  ? "Scientific Backend Offline"
                  : "Scientific Engine Connected & Validated"}
              </span>
              {!loading && !error && (
                <span className="font-mono text-[10px] rounded-xs bg-[var(--emerald-light)] px-1 py-0.2 text-[var(--emerald)] border border-emerald-500/30 font-bold">
                  {presetCount} Presets Synchronized
                </span>
              )}
            </div>
            <p className="text-[11px] leading-relaxed text-[var(--muted)]">
              {loading
                ? "Connecting to local FastAPI runtime at http://127.0.0.1:8000..."
                : error
                ? error
                : `Active runtime: ${health?.engine} v${health?.version} (commit ${health?.commit_hash.slice(0, 7)})`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
          <button
            type="button"
            onClick={handleManualRetry}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-sm border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-[11px] font-sans font-medium text-[var(--foreground)] hover:bg-[var(--surface-hover)] hover:border-[var(--accent-border)] disabled:opacity-50 transition-colors shadow-2xs cursor-pointer"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
            <span>{loading ? "Testing..." : "Test Connection"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ApiStatusBanner;
