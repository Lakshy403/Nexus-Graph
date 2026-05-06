"use client";

import { SectionHeader } from "@/components/layout/section-header";
import { TimelineReplay } from "@/components/timeline/timeline-replay";
import { useBootstrapData } from "@/hooks/use-bootstrap-data";

export default function TimelinePage() {
  useBootstrapData();
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Temporal Intelligence"
        title="Decision Evolution Replay"
        description="Chronological reconstruction of conversations, decisions, tasks, commits, conflicts, and AI remediation."
      />
      <TimelineReplay />
    </div>
  );
}
