"use client";

import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/store/app-store";

export function RecommendationFeed() {
  const recommendations = useAppStore((s) => s.recommendations);
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Recommendation Feed</CardTitle>
        <Sparkles size={16} className="text-sky-200" />
      </CardHeader>
      <CardContent className="space-y-3">
        {recommendations.map((item) => (
          <div key={item.recommendation_id} className="rounded-md border border-white/10 bg-white/[0.035] p-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-white">{item.title}</div>
              <Badge tone={item.priority === "urgent" ? "danger" : "warning"}>{item.priority}</Badge>
            </div>
            <p className="text-sm leading-5 text-slate-400">{item.summary}</p>
            <div className="mt-3 text-xs text-slate-500">{item.action}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
