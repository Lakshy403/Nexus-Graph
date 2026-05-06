"use client";

import { ConflictBoard } from "@/components/conflicts/conflict-board";
import { SectionHeader } from "@/components/layout/section-header";
import { useBootstrapData } from "@/hooks/use-bootstrap-data";

export default function ConflictsPage() {
  useBootstrapData();
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Conflict Intelligence"
        title="Decision Drift Monitor"
        description="Real-time policy, security, infrastructure, architecture, and dependency conflicts with AI reasoning and remediation."
      />
      <ConflictBoard />
    </div>
  );
}
