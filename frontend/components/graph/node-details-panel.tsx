"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useAppStore } from "@/store/app-store";

export function NodeDetailsPanel() {
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);
  const selectNode = useAppStore((s) => s.selectNode);
  const node = useAppStore((s) => s.nodes.find((item) => item.id === selectedNodeId));

  if (!node) return null;
  const entries = Object.entries(node.metadata || {});

  return (
    <Card className="absolute right-4 top-4 z-20 w-[360px] overflow-hidden">
      <div className="flex items-start justify-between gap-4 border-b border-white/10 p-4">
        <div>
          <Badge tone={node.kind === "Conflict" ? "danger" : "info"}>{node.kind}</Badge>
          <div className="mt-3 text-lg font-semibold text-white">{node.label}</div>
          <div className="text-sm text-slate-400">{node.subtitle}</div>
        </div>
        <Button variant="ghost" size="icon" onClick={() => selectNode(undefined)} aria-label="Close node details">
          <X size={16} />
        </Button>
      </div>
      <div className="max-h-[62vh] space-y-3 overflow-auto p-4">
        {entries.map(([key, value]) => (
          <div key={key} className="rounded-md border border-white/8 bg-white/[0.035] p-3">
            <div className="text-[11px] uppercase tracking-[0.14em] text-slate-500">{key}</div>
            <pre className="mt-1 whitespace-pre-wrap break-words font-sans text-sm leading-5 text-slate-300">
              {typeof value === "object" ? JSON.stringify(value, null, 2) : String(value)}
            </pre>
          </div>
        ))}
      </div>
    </Card>
  );
}
