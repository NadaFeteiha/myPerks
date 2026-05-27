"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import type { RequestHistoryItem } from "@/lib/api";

type Props = {
  data: RequestHistoryItem[];
};

const COLORS = [
  "#534ab7", // brand-purple-600
  "#5dcaa5", // brand-teal-200
  "#7262cb", // brand-purple-400
  "#1d9e75", // brand-teal-400
  "#9080e0", // brand-purple-300
  "#0f6e56", // brand-teal-600
];

export function RequestsPieChart({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex h-48 items-center justify-center rounded-xl border border-border bg-white dark:bg-card">
        <p className="text-[12px] text-muted-foreground">
          No request data available.
        </p>
      </div>
    );
  }

  const chartData = aggregateByType(data);

  return (
    <ResponsiveContainer height={200} width="100%">
      <PieChart>
        <Pie
          cx="50%"
          cy="50%"
          data={chartData}
          dataKey="value"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={3}
        >
          {chartData.map((_, index) => (
            <Cell fill={COLORS[index % COLORS.length]} key={`cell-${index}`} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            fontSize: "12px",
          }}
          itemStyle={{ color: "var(--muted-foreground)" }}
          labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
        />
        <Legend
          formatter={(value) => (
            <span
              style={{ color: "var(--muted-foreground)", fontSize: "11px" }}
            >
              {value}
            </span>
          )}
          iconSize={8}
          iconType="circle"
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

function aggregateByType(items: RequestHistoryItem[]) {
  const counts: Record<string, number> = {};
  for (const item of items) {
    counts[item.type] = (counts[item.type] ?? 0) + 1;
  }
  return Object.entries(counts).map(([name, value]) => ({ name, value }));
}
