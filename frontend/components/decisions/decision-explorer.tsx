"use client";

import { useMemo, useState } from "react";
import { Search, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useAppStore } from "@/store/app-store";

export function DecisionExplorer() {
  const decisions = useAppStore((s) => s.decisions);
  const conflicts = useAppStore((s) => s.conflicts);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return decisions.filter((d) => [d.decision, d.constraint, d.category, d.made_by].filter(Boolean).join(" ").toLowerCase().includes(q));
  }, [decisions, query]);

  const grouped = useMemo(() => {
    return filtered.reduce<Record<string, typeof filtered>>((acc, decision) => {
      acc[decision.category] = [...(acc[decision.category] || []), decision];
      return acc;
    }, {});
  }, [filtered]);

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Semantic search decisions, constraints, owners, systems" className="pl-10" />
        </div>
        {Object.entries(grouped).map(([category, items]) => (
          <Card key={category}>
            <CardHeader>
              <CardTitle>{category}</CardTitle>
              <Badge tone="info">{items.length} decisions</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {items.map((decision, index) => {
                const relatedConflicts = conflicts.filter((conflict) => conflict.related_decision_id === decision.id);
                return (
                  <motion.div key={decision.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.035 }} className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
                    <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-white">{decision.decision}</div>
                        <div className="mt-1 text-xs text-slate-500">made by {decision.made_by || "unknown"}</div>
                      </div>
                      <Badge tone={decision.importance === "critical" ? "danger" : decision.importance === "high" ? "warning" : "neutral"}>{decision.importance}</Badge>
                    </div>
                    <div className="text-sm text-slate-400">{decision.constraint}</div>
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      <div className="rounded-md border border-white/8 bg-slate-950/40 p-3">
                        <div className="text-xs text-slate-500">confidence</div>
                        <Progress value={(decision.confidence || 0.74) * 100} className="mt-2" />
                      </div>
                      <div className="rounded-md border border-white/8 bg-slate-950/40 p-3">
                        <div className="text-xs text-slate-500">conflicts</div>
                        <div className="mt-1 text-lg font-semibold text-white">{relatedConflicts.length}</div>
                      </div>
                      <div className="rounded-md border border-white/8 bg-slate-950/40 p-3">
                        <div className="text-xs text-slate-500">lineage</div>
                        <div className="mt-1 text-sm text-slate-300">{decision.context?.join(" -> ") || "graph linked"}</div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Lineage Lens</CardTitle>
          <ShieldCheck size={16} className="text-emerald-200" />
        </CardHeader>
        <CardContent className="space-y-4">
          {decisions.slice(0, 4).map((decision) => (
            <div key={decision.id} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
              <div className="text-sm font-medium text-white">{decision.category}</div>
              <p className="mt-1 line-clamp-3 text-xs leading-5 text-slate-400">{decision.decision}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {decision.context?.map((item) => (
                  <Badge key={item} tone="neutral">{item}</Badge>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
