"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .get<T>(path)
      .then((d) => {
        if (!cancelled) setData(d);
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
  }, [path]);

  return { data, error };
}
