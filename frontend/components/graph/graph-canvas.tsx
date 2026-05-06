"use client";

import { useEffect, useMemo } from "react";
import ReactFlow, { Background, Controls, MiniMap, useEdgesState, useNodesState, type NodeMouseHandler } from "reactflow";
import { motion } from "framer-motion";
import KnowledgeNode from "@/components/graph/knowledge-node";
import RelationshipEdge from "@/components/graph/relationship-edge";
import { NodeDetailsPanel } from "@/components/graph/node-details-panel";
import { layoutGraph } from "@/utils/graph-layout";
import { useAppStore } from "@/store/app-store";

const nodeTypes = { knowledge: KnowledgeNode };
const edgeTypes = { relationship: RelationshipEdge };

export function GraphCanvas() {
  const sourceNodes = useAppStore((s) => s.nodes);
  const sourceEdges = useAppStore((s) => s.edges);
  const selectNode = useAppStore((s) => s.selectNode);
  const graph = useMemo(() => layoutGraph(sourceNodes, sourceEdges), [sourceEdges, sourceNodes]);
  const [nodes, setNodes, onNodesChange] = useNodesState(graph.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(graph.edges);

  useEffect(() => {
    setNodes(graph.nodes);
    setEdges(graph.edges);
  }, [graph.edges, graph.nodes, setEdges, setNodes]);

  const onNodeClick: NodeMouseHandler = (_, node) => selectNode(node.id);

  return (
    <motion.div initial={{ opacity: 0, scale: 0.99 }} animate={{ opacity: 1, scale: 1 }} className="relative h-[calc(100vh-210px)] min-h-[680px] overflow-hidden rounded-lg border border-white/10 bg-slate-950/45">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.25}
        maxZoom={1.4}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(148,163,184,0.15)" gap={24} />
        <MiniMap pannable zoomable nodeColor={(node) => (node.data.kind === "Conflict" ? "#f87171" : "#38bdf8")} maskColor="rgba(2,6,23,0.72)" />
        <Controls className="!border-white/10 !bg-slate-950/80 !text-slate-200" />
      </ReactFlow>
      <NodeDetailsPanel />
    </motion.div>
  );
}
