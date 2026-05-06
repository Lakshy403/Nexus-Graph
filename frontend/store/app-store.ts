"use client";

import { create } from "zustand";
import type { ActivityEvent, Conflict, Decision, KnowledgeEdge, KnowledgeNode, MetricPoint, Recommendation, SystemStats, TimelineEvent } from "@/types/domain";
import { demoActivity, demoConflicts, demoDecisions, demoEdges, demoMetrics, demoNodes, demoRecommendations, demoStats, demoTimeline } from "@/lib/demo-data";

interface AppState {
  connected: boolean;
  selectedNodeId?: string;
  replayIndex: number;
  replaying: boolean;
  stats: SystemStats;
  metrics: MetricPoint[];
  decisions: Decision[];
  conflicts: Conflict[];
  recommendations: Recommendation[];
  timeline: TimelineEvent[];
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  activity: ActivityEvent[];
  setConnected: (connected: boolean) => void;
  selectNode: (nodeId?: string) => void;
  setReplayIndex: (index: number) => void;
  setReplaying: (value: boolean) => void;
  hydrate: (payload: { stats?: Partial<SystemStats>; decisions?: Decision[]; timeline?: TimelineEvent[] }) => void;
  addDecision: (decision: Partial<Decision>) => void;
  addConflict: (conflict: Partial<Conflict>) => void;
  addTimeline: (entry: Partial<TimelineEvent>) => void;
  addGraphUpdate: (update: Record<string, unknown>) => void;
  addActivity: (event: ActivityEvent) => void;
}

export const useAppStore = create<AppState>((set) => ({
  connected: false,
  selectedNodeId: "conf-token-72",
  replayIndex: demoTimeline.length - 1,
  replaying: false,
  stats: demoStats,
  metrics: demoMetrics,
  decisions: demoDecisions,
  conflicts: demoConflicts,
  recommendations: demoRecommendations,
  timeline: demoTimeline,
  nodes: demoNodes,
  edges: demoEdges,
  activity: demoActivity,
  setConnected: (connected) => set({ connected }),
  selectNode: (selectedNodeId) => set({ selectedNodeId }),
  setReplayIndex: (replayIndex) => set({ replayIndex }),
  setReplaying: (replaying) => set({ replaying }),
  hydrate: (payload) =>
    set((state) => ({
      ...state,
      stats: payload.stats ? { ...state.stats, ...payload.stats } : state.stats,
      decisions: payload.decisions?.length ? payload.decisions : state.decisions,
      timeline: payload.timeline?.length ? payload.timeline : state.timeline
    })),
  addDecision: (decision) =>
    set((state) => {
      const raw = decision as Partial<Decision> & { event_id?: string; source_user?: string };
      const id = raw.id || raw.event_id || `decision-${Date.now()}`;
      const next: Decision = {
        id,
        decision: decision.decision || "New decision captured",
        constraint: decision.constraint,
        category: decision.category || "General",
        importance: (decision.importance as Decision["importance"]) || "medium",
        made_by: raw.made_by || raw.source_user,
        timestamp: new Date().toISOString(),
        confidence: decision.confidence
      };
      const severity: ActivityEvent["severity"] = next.importance === "critical" ? "critical" : "high";
      const activityEvent: ActivityEvent = {
        id: `activity-${Date.now()}`,
        type: "decision:created",
        title: "Decision created",
        detail: next.decision,
        timestamp: next.timestamp || new Date().toISOString(),
        severity
      };
      return {
        decisions: [next, ...state.decisions].slice(0, 40),
        stats: { ...state.stats, decisions: state.stats.decisions + 1 },
        activity: [activityEvent, ...state.activity].slice(0, 60)
      };
    }),
  addConflict: (conflict) =>
    set((state) => {
      const next: Conflict = {
        conflict_id: conflict.conflict_id || `conflict-${Date.now()}`,
        type: conflict.type || "decision_drift",
        severity: (conflict.severity as Conflict["severity"]) || "high",
        confidence: Number(conflict.confidence || 0.82),
        reasoning: conflict.reasoning || (conflict as Partial<Conflict> & { message?: string }).message || "Conflict detected by AI orchestration.",
        recommendation: conflict.recommendation || "Review related decision and open remediation.",
        related_decision_id: conflict.related_decision_id,
        affected_systems: conflict.affected_systems || [],
        timestamp: new Date().toISOString()
      };
      return {
        conflicts: [next, ...state.conflicts].slice(0, 50),
        stats: { ...state.stats, conflicts: state.stats.conflicts + 1 },
        activity: [
          {
            id: `activity-${Date.now()}`,
            type: "conflict:detected",
            title: `${next.severity.toUpperCase()} conflict detected`,
            detail: next.reasoning,
            timestamp: next.timestamp || new Date().toISOString(),
            severity: next.severity
          },
          ...state.activity
        ].slice(0, 60)
      };
    }),
  addTimeline: (entry) =>
    set((state) => {
      const next: TimelineEvent = {
        timeline_id: entry.timeline_id || `timeline-${Date.now()}`,
        event_id: entry.event_id || `event-${Date.now()}`,
        correlation_id: entry.correlation_id || "live-correlation",
        kind: entry.kind || "event",
        summary: entry.summary || "Timeline updated",
        timestamp: entry.timestamp || new Date().toISOString(),
        source: entry.source,
        severity: entry.severity as TimelineEvent["severity"]
      };
      return { timeline: [...state.timeline, next].slice(-120), replayIndex: state.timeline.length };
    }),
  addGraphUpdate: (update) =>
    set((state) => ({
      stats: { ...state.stats, graphRelationships: state.stats.graphRelationships + 1 },
      activity: [
        {
          id: `activity-${Date.now()}`,
          type: "graph:update",
          title: "Graph updated",
          detail: String(update.update || update.type || "Relationship updated"),
          timestamp: new Date().toISOString()
        },
        ...state.activity
      ].slice(0, 60)
    })),
  addActivity: (event) => set((state) => ({ activity: [event, ...state.activity].slice(0, 60) }))
}));
