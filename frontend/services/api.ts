import type { Decision, SystemStats, TimelineEvent } from "@/types/domain";

const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:3000";
const aiUrl = process.env.NEXT_PUBLIC_AI_SERVICE_URL || "http://localhost:8001";

async function safeJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchSystemStats(): Promise<Partial<SystemStats> | null> {
  const [gateway, ai] = await Promise.all([
    safeJson<{ raw_events: number; extracted_decisions: number; processing_logs: number }>(`${gatewayUrl}/events/stats`),
    safeJson<{ mongodb?: Record<string, number>; neo4j?: Record<string, number>; chromadb?: { embeddings: number } }>(`${aiUrl}/stats`)
  ]);

  if (!gateway && !ai) return null;
  return {
    decisions: ai?.mongodb?.extracted_decisions ?? gateway?.extracted_decisions,
    semanticHits: ai?.chromadb?.embeddings,
    graphRelationships:
      (ai?.neo4j?.decisions || 0) +
      (ai?.neo4j?.tasks || 0) +
      (ai?.neo4j?.commits || 0) +
      (ai?.neo4j?.conflicts || 0)
  };
}

export async function fetchDecisions(): Promise<Decision[] | null> {
  const data = await safeJson<{ decisions: Array<Record<string, unknown>> }>(`${aiUrl}/decisions`);
  if (!data?.decisions) return null;
  return data.decisions.map((d) => ({
    id: String(d.id || crypto.randomUUID()),
    decision: String(d.decision || ""),
    constraint: d.constraint ? String(d.constraint) : undefined,
    category: String(d.category || "General"),
    importance: (String(d.importance || "medium") as Decision["importance"]),
    made_by: d.made_by ? String(d.made_by) : undefined
  }));
}

export async function fetchTimeline(correlationId: string): Promise<TimelineEvent[] | null> {
  const data = await safeJson<{ timeline: TimelineEvent[] }>(`${aiUrl}/timeline/${correlationId}`);
  return data?.timeline || null;
}
