"use client";

import { useEffect } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAppStore } from "@/store/app-store";
import { timeAgo } from "@/lib/utils";

export function TimelineReplay() {
  const timeline = useAppStore((s) => s.timeline);
  const replayIndex = useAppStore((s) => s.replayIndex);
  const replaying = useAppStore((s) => s.replaying);
  const setReplayIndex = useAppStore((s) => s.setReplayIndex);
  const setReplaying = useAppStore((s) => s.setReplaying);
  const visible = timeline.slice(0, replayIndex + 1);

  useEffect(() => {
    if (!replaying) return;
    const id = window.setInterval(() => {
      setReplayIndex(replayIndex >= timeline.length - 1 ? 0 : replayIndex + 1);
    }, 1100);
    return () => window.clearInterval(id);
  }, [replayIndex, replaying, setReplayIndex, timeline.length]);

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
      <Card>
        <CardHeader>
          <CardTitle>Temporal Reconstruction</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setReplayIndex(0)}>
              <RotateCcw size={14} />
              Reset
            </Button>
            <Button size="sm" onClick={() => setReplaying(!replaying)}>
              {replaying ? <Pause size={14} /> : <Play size={14} />}
              {replaying ? "Pause" : "Replay"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={timeline.length ? ((replayIndex + 1) / timeline.length) * 100 : 0} className="mb-6" />
          <div className="relative space-y-4 before:absolute before:bottom-0 before:left-[18px] before:top-0 before:w-px before:bg-white/10">
            {visible.map((event, index) => (
              <motion.div
                key={event.timeline_id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                className="relative pl-12"
              >
                <div className={`absolute left-[10px] top-3 h-4 w-4 rounded-full border ${event.severity === "critical" ? "border-red-200 bg-red-400 shadow-conflict" : "border-sky-200 bg-sky-400"}`} />
                <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge tone={event.severity === "critical" ? "danger" : "info"}>{event.kind}</Badge>
                      <span className="text-xs text-slate-500">{event.source}</span>
                    </div>
                    <span className="text-xs text-slate-500">{timeAgo(event.timestamp)}</span>
                  </div>
                  <div className="text-sm font-medium text-white">{event.summary}</div>
                  <div className="mt-2 text-xs text-slate-500">{event.correlation_id}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Replay State</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md border border-white/10 bg-white/[0.035] p-4">
            <div className="text-3xl font-semibold text-white">{Math.min(replayIndex + 1, timeline.length)}</div>
            <div className="text-sm text-slate-400">events materialized</div>
          </div>
          <div className="rounded-md border border-white/10 bg-white/[0.035] p-4">
            <div className="text-sm font-medium text-white">Current signal</div>
            <p className="mt-2 text-sm leading-6 text-slate-400">{timeline[replayIndex]?.summary}</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {timeline.map((event, index) => (
              <button
                key={event.timeline_id}
                onClick={() => setReplayIndex(index)}
                className={`rounded-md border px-3 py-2 text-left text-xs transition ${index <= replayIndex ? "border-sky-300/30 bg-sky-300/10 text-sky-100" : "border-white/10 bg-white/[0.03] text-slate-500"}`}
              >
                {event.kind}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
