"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";

import type{ RequestHistoryItem } from "@/lib/api";

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

function aggregateByType(items: RequestHistoryItem[]) {
    const counts: Record<string, number> = {};
    for (const item of items) {
        counts[item.type] = (counts[item.type] ?? 0) + 1;
    }
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
}

export function RequestsPieChart({ data }: Props) {
    if (!data.length) {
        return (
        <div className="flex h-48 items-center justify-center rounded-xl border border-border bg-white dark:bg-card">
            <p className="text-[12px] text-muted-foreground">No request data available.</p>
        </div>
        );
    }

    const chartData = aggregateByType(data);

    return (
        <ResponsiveContainer height={200} width="100%">
            <PieChart>
                <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                >
                    {chartData.map((_, index) => (
                        <Cell
                            key={`cell-${index}`}
                            // eslint-disable-next-line security/detect-object-injection
                            fill={COLORS[index % COLORS.length]}
                        />
                    ))}
                </Pie>
                <Tooltip
                    contentStyle={{
                        background: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        fontSize: "12px",
                    }}
                    labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
                    itemStyle={{ color: "var(--muted-foreground)" }}
                />
                <Legend
                    iconType="circle"
                    iconSize={8}
                    formatter={(value) => (
                        <span style={{ color: "var(--muted-foreground)", fontSize: "11px" }}>
                            {value}
                        </span>
                    )}
                />
            </PieChart>
        </ResponsiveContainer>
    );
}
