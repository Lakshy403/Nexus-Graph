"use client";

import { motion } from "framer-motion";
import { Database, GitBranch, Network, Server, Wifi } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useAppStore } from "@/store/app-store";

const services = [
  { label: "Gateway", icon: Server },
  { label: "AI gRPC", icon: Wifi },
  { label: "Neo4j", icon: Network },
  { label: "MongoDB", icon: Database },
  { label: "ChromaDB", icon: GitBranch }
];

export function StatusStrip() {
  const connected = useAppStore((s) => s.connected);
  return (
    <Card className="grid grid-cols-2 gap-2 p-3 md:grid-cols-5">
      {services.map((service, index) => {
        const Icon = service.icon;
        return (
          <motion.div
            key={service.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            className="flex items-center justify-between rounded-md border border-white/8 bg-white/[0.03] px-3 py-2"
          >
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <Icon size={15} className="text-sky-200" />
              {service.label}
            </div>
            <span className={`h-2 w-2 rounded-full ${connected || index > 1 ? "bg-emerald-300" : "bg-amber-300"}`} />
          </motion.div>
        );
      })}
    </Card>
  );
}
