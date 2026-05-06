"use client";

import { DecisionExplorer } from "@/components/decisions/decision-explorer";
import { SectionHeader } from "@/components/layout/section-header";
import { useBootstrapData } from "@/hooks/use-bootstrap-data";

export default function DecisionsPage() {
  useBootstrapData();
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Decision Memory"
        title="Decision Lineage Explorer"
        description="Search extracted decisions, inspect constraints, rank importance, and follow relationships across discussions, tickets, commits, and incidents."
      />
      <DecisionExplorer />
    </div>
  );
}
