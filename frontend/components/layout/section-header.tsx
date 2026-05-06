"use client";

import { motion } from "framer-motion";

export function SectionHeader({
  eyebrow,
  title,
  description
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="max-w-4xl">
      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-sky-200/80">{eyebrow}</div>
      <h1 className="text-3xl font-semibold tracking-normal text-white md:text-4xl">{title}</h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">{description}</p>
    </motion.div>
  );
}
