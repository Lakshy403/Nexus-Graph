import type { KnowledgeEdge, KnowledgeNode } from "@/types/domain";

const layer: Record<string, number> = {
  Person: 0,
  Decision: 1,
  ArchitectureConstraint: 2,
  Task: 2,
  Commit: 3,
  Conflict: 4,
  Incident: 5,
  Recommendation: 5
};

export function layoutGraph(nodes: KnowledgeNode[], edges: KnowledgeEdge[]) {
  const buckets = new Map<number, KnowledgeNode[]>();
  nodes.forEach((node) => {
    const index = layer[node.kind] ?? 2;
    buckets.set(index, [...(buckets.get(index) || []), node]);
  });

  const rfNodes = nodes.map((node) => {
    const layerIndex = layer[node.kind] ?? 2;
    const bucket = buckets.get(layerIndex) || [];
    const yIndex = bucket.findIndex((item) => item.id === node.id);
    return {
      id: node.id,
      type: "knowledge",
      position: { x: layerIndex * 270, y: yIndex * 150 + (layerIndex % 2) * 42 },
      data: node
    };
  });

  const rfEdges = edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: "relationship",
    animated: edge.animated,
    data: edge,
    style: {
      stroke: edge.type === "VIOLATES" ? "#f87171" : edge.type === "RECOMMENDED_FIX" ? "#34d399" : "#38bdf8",
      strokeWidth: edge.type === "VIOLATES" ? 2.4 : 1.6
    }
  }));

  return { nodes: rfNodes, edges: rfEdges };
}
