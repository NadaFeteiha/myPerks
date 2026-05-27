"use client";

import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import type { BenefitSummaryItem } from "@/lib/api";

type Props = {
    data: BenefitSummaryItem[];
}

export function BenefitsBarChart({ data }: Props) {
    if (!data.length) {
        return (
            <div className="flex h-48 items-center justify-center rounded-xl border border-border bg-white dark:bg-card">
                <p className="text-[12px] text-muted-foreground">No benefits data available.</p>
            </div>
        )
    }

    const chartData = data.map((item) => ({
        name: item.leave_type,
        remaining: item.remaining_days,
        used: item.used_days,
    }));

    return (
        <ResponsiveContainer height={200} width="100%">
            <BarChart barSize={24} data={chartData} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis
                    dataKey="name"
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                />
                <YAxis
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={28}
                />
                <Tooltip
                    contentStyle={{
                        background: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        fontSize: "12px",
                    }}
                    labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
                    itemStyle={{ color: "var(--muted-foreground)" }}
                    cursor={{ fill: "var(--muted)", opacity: 0.4 }}
                />
                <Bar dataKey="used" name="Used" fill="#534ab7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="remaining" name="Remaining" fill="#5dcaa5" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    )
}
