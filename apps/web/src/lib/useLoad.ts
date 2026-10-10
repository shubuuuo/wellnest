"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

const EVENT = "wellnest:predictions-changed";

export function notifyPredictionsChanged() {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(EVENT));
}

export function useLoad<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const bump = () => setTick((t) => t + 1);
    window.addEventListener(EVENT, bump);
    return () => window.removeEventListener(EVENT, bump);
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .get<T>(path)
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setError(null);
      })
      .catch((e) => {
        if (!cancelled)
          setError(
            e instanceof ApiError ? e.userMessage : "Something went wrong",
          );
      });
    return () => {
      cancelled = true;
    };
  }, [path, tick]);

  return { data, error, reload: () => setTick((t) => t + 1) };
}
