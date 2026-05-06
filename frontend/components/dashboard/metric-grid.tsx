"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Brain, Clock3, GitMerge, RadioTower, Waypoints } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { compactNumber, formatLatency } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

export function MetricGrid() {
  const stats = useAppStore((s) => s.stats);
  const metrics = [
    { label: "Total Decisions", value: compactNumber(stats.decisions), icon: Brain, tone: "text-sky-200" },
    { label: "Active Conflicts", value: stats.conflicts, icon: AlertTriangle, tone: "text-red-200", glow: true },
    { label: "Semantic Hits", value: compactNumber(stats.semanticHits), icon: Waypoints, tone: "text-emerald-200" },
    { label: "Graph Links", value: compactNumber(stats.graphRelationships), icon: GitMerge, tone: "text-violet-200" },
    { label: "Throughput/min", value: stats.throughput, icon: RadioTower, tone: "text-cyan-200" },
    { label: "Latency", value: formatLatency(stats.latency), icon: Clock3, tone: "text-amber-200" }
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {metrics.map((metric, index) => {
        const Icon = metric.icon;
        return (
          <motion.div key={metric.label} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.045 }}>
            <Card className={metric.glow ? "shadow-conflict" : ""}>
              <CardContent className="p-4">
                <div className="mb-5 flex items-center justify-between">
                  <Icon size={18} className={metric.tone} />
                  <span className="h-1.5 w-1.5 rounded-full bg-white/40" />
                </div>
                <div className="text-2xl font-semibold text-white">{metric.value}</div>
                <div className="mt-1 text-xs text-slate-400">{metric.label}</div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
