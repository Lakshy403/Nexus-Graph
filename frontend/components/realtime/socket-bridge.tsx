"use client";

import { useEffect } from "react";
import { io, type Socket } from "socket.io-client";
import { useAppStore } from "@/store/app-store";

const socketUrl = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:3000";

export function SocketBridge() {
  const setConnected = useAppStore((s) => s.setConnected);
  const addDecision = useAppStore((s) => s.addDecision);
  const addConflict = useAppStore((s) => s.addConflict);
  const addTimeline = useAppStore((s) => s.addTimeline);
  const addGraphUpdate = useAppStore((s) => s.addGraphUpdate);
  const addActivity = useAppStore((s) => s.addActivity);

  useEffect(() => {
    const socket: Socket = io(socketUrl, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 750
    });

    socket.on("connect", () => {
      setConnected(true);
      ["decision-events", "conflict-events", "graph-updates", "timeline-events", "orchestration-events"].forEach((channel) => {
        socket.emit("subscribe", channel);
      });
    });
    socket.on("disconnect", () => setConnected(false));
    socket.on("decision:created", addDecision);
    socket.on("conflict:detected", addConflict);
    socket.on("timeline:update", addTimeline);
    socket.on("graph:update", addGraphUpdate);
    socket.on("orchestration:status", (event) => {
      addActivity({
        id: `orchestration-${Date.now()}`,
        type: "orchestration:status",
        title: "Orchestration status",
        detail: `${event.stage || "workflow"} completed`,
        timestamp: new Date().toISOString()
      });
    });

    return () => {
      socket.disconnect();
    };
  }, [addActivity, addConflict, addDecision, addGraphUpdate, addTimeline, setConnected]);

  return null;
}
