"use client";

import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { MetricGrid } from "@/components/dashboard/metric-grid";
import { ObservabilityPanel } from "@/components/dashboard/observability-panel";
import { RecommendationFeed } from "@/components/dashboard/recommendation-feed";
import { SectionHeader } from "@/components/layout/section-header";
import { StatusStrip } from "@/components/dashboard/status-strip";
import { useBootstrapData } from "@/hooks/use-bootstrap-data";

export default function DashboardPage() {
  useBootstrapData();

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Cognitive Operations"
        title="Organizational Intelligence"
        description="Live decisions, conflicts, memory retrieval, graph updates, and orchestration telemetry."
      />
      <StatusStrip />
      <MetricGrid />
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <ObservabilityPanel />
        <RecommendationFeed />
      </div>
      <ActivityFeed />
    </div>
  );
}
