"use client";

import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "reactflow";
import type { KnowledgeEdge } from "@/types/domain";

export default function RelationshipEdge(props: EdgeProps<KnowledgeEdge>) {
  const [edgePath, labelX, labelY] = getBezierPath(props);
  const label = props.data?.type || "RELATED_TO";
  return (
    <>
      <BaseEdge path={edgePath} markerEnd={props.markerEnd} style={props.style} />
      <EdgeLabelRenderer>
        <div
          className="pointer-events-none absolute rounded-full border border-white/10 bg-slate-950/80 px-2 py-0.5 text-[10px] font-medium text-slate-300 shadow-lg backdrop-blur"
          style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
        >
          {label}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
