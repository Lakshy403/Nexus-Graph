"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

export function ActivityFeed() {
  const activity = useAppStore((s) => s.activity);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Event Stream</CardTitle>
        <span className="text-xs text-slate-400">{activity.length} signals</span>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {activity.slice(0, 9).map((event, index) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.025 }}
            className="rounded-md border border-white/10 bg-white/[0.035] p-3"
          >
            <div className="mb-2 flex items-center justify-between gap-2">
              <Badge tone={event.severity === "critical" ? "danger" : event.severity === "high" ? "warning" : "info"}>{event.type}</Badge>
              <span className="text-xs text-slate-500">{timeAgo(event.timestamp)}</span>
            </div>
            <div className="text-sm font-medium text-slate-100">{event.title}</div>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{event.detail}</p>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
