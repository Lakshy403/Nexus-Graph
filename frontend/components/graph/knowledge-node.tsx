"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { AlertTriangle, Brain, CheckCircle2, GitCommit, Lightbulb, Network, ScrollText, UserRound } from "lucide-react";
import { cn } from "@/lib/utils";
import type { KnowledgeNode as KnowledgeNodeType } from "@/types/domain";

const iconMap = {
  Person: UserRound,
  Decision: Brain,
  Task: CheckCircle2,
  Commit: GitCommit,
  Conflict: AlertTriangle,
  Incident: Network,
  ArchitectureConstraint: ScrollText,
  Recommendation: Lightbulb
};

function KnowledgeNode({ data, selected }: NodeProps<KnowledgeNodeType>) {
  const Icon = iconMap[data.kind];
  const danger = data.severity === "critical" || data.kind === "Conflict";
  return (
    <div
      className={cn(
        "w-[218px] rounded-lg border bg-slate-950/88 p-3 shadow-xl backdrop-blur-md transition",
        selected && "ring-2 ring-sky-300/60",
        danger ? "border-red-300/35 shadow-conflict" : "border-sky-200/16 shadow-glow"
      )}
    >
      <Handle type="target" position={Position.Left} />
      <div className="flex items-start gap-3">
        <div className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-md border", danger ? "border-red-300/25 bg-red-400/12 text-red-200" : "border-sky-300/25 bg-sky-300/10 text-sky-200")}>
          <Icon size={17} />
        </div>
        <div className="min-w-0">
          <div className="text-[11px] uppercase tracking-[0.14em] text-slate-500">{data.kind}</div>
          <div className="truncate text-sm font-semibold text-white">{data.label}</div>
          <div className="mt-0.5 truncate text-xs text-slate-400">{data.subtitle}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default memo(KnowledgeNode);
