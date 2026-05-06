"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, ChevronDown } from "lucide-react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useAppStore } from "@/store/app-store";
import type { Severity } from "@/types/domain";

const filters: Array<Severity | "all"> = ["all", "critical", "high", "medium", "low"];

export function ConflictBoard() {
  const conflicts = useAppStore((s) => s.conflicts);
  const [filter, setFilter] = useState<Severity | "all">("all");
  const [open, setOpen] = useState<string | undefined>(conflicts[0]?.conflict_id);
  const filtered = useMemo(() => conflicts.filter((c) => filter === "all" || c.severity === filter), [conflicts, filter]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {filters.map((item) => (
          <Button key={item} variant={filter === item ? "default" : "outline"} size="sm" onClick={() => setFilter(item)}>
            {item}
          </Button>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {filtered.map((conflict, index) => (
          <motion.div key={conflict.conflict_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.04 }}>
            <Card className={conflict.severity === "critical" ? "shadow-conflict" : ""}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="grid h-9 w-9 place-items-center rounded-md border border-red-300/25 bg-red-400/12 text-red-200">
                    <AlertTriangle size={17} />
                  </div>
                  <div>
                    <CardTitle>{conflict.type.replaceAll("_", " ")}</CardTitle>
                    <div className="mt-1 text-xs text-slate-500">{conflict.conflict_id}</div>
                  </div>
                </div>
                <Badge tone={conflict.severity === "critical" ? "danger" : "warning"}>{conflict.severity}</Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="mb-2 flex justify-between text-xs text-slate-400">
                    <span>confidence</span>
                    <span>{Math.round(conflict.confidence * 100)}%</span>
                  </div>
                  <Progress value={conflict.confidence * 100} />
                </div>
                <p className="text-sm leading-6 text-slate-300">{conflict.reasoning}</p>
                <div className="flex flex-wrap gap-2">
                  {conflict.affected_systems?.map((system) => (
                    <Badge key={system} tone="neutral">{system}</Badge>
                  ))}
                </div>
                <Button variant="outline" size="sm" onClick={() => setOpen(open === conflict.conflict_id ? undefined : conflict.conflict_id)}>
                  <ChevronDown size={14} />
                  Reasoning
                </Button>
                {open === conflict.conflict_id && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
                    <div className="text-xs uppercase tracking-[0.14em] text-slate-500">recommended fix</div>
                    <div className="mt-2 text-sm leading-6 text-slate-300">{conflict.recommendation}</div>
                    <div className="mt-3 text-xs text-slate-500">linked decision: {conflict.related_decision_id}</div>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
