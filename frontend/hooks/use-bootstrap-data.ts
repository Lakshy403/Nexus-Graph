"use client";

import { useEffect } from "react";
import { fetchDecisions, fetchSystemStats } from "@/services/api";
import { useAppStore } from "@/store/app-store";

export function useBootstrapData() {
  const hydrate = useAppStore((s) => s.hydrate);

  useEffect(() => {
    let mounted = true;
    Promise.all([fetchSystemStats(), fetchDecisions()]).then(([stats, decisions]) => {
      if (!mounted) return;
      hydrate({
        stats: stats || undefined,
        decisions: decisions || undefined
      });
    });
    return () => {
      mounted = false;
    };
  }, [hydrate]);
}
