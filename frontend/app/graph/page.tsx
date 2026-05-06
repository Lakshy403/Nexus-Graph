"use client";

import { GraphCanvas } from "@/components/graph/graph-canvas";
import { SectionHeader } from "@/components/layout/section-header";
import { useBootstrapData } from "@/hooks/use-bootstrap-data";

export default function GraphPage() {
  useBootstrapData();
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Knowledge Graph"
        title="Causal Relationship Map"
        description="People, decisions, constraints, tasks, commits, incidents, conflicts, and recommendations linked into one operational memory graph."
      />
      <GraphCanvas />
    </div>
  );
}
